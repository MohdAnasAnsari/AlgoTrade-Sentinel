"""
Prefect flow: daily batch inference pipeline.

Loads latest features for all watchlist tickers, generates BUY/SELL/HOLD
signals via the champion model, stores them in the DB, and logs summary
metrics to MLflow.
"""
from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


try:
    from prefect import flow, task
    from prefect.logging import get_run_logger
    HAS_PREFECT = True
except ImportError:
    HAS_PREFECT = False
    def flow(fn=None, **kw):       return fn if fn else (lambda f: f)
    def task(fn=None, **kw):       return fn if fn else (lambda f: f)
    def get_run_logger():          return logging.getLogger("inference_flow")


@task(name="load_features_for_ticker", retries=2)
def load_features_task(ticker: str, limit: int = 60) -> dict:
    """Load recent feature rows for one ticker from the DB."""
    log = get_run_logger() if HAS_PREFECT else logger
    try:
        sys.path.insert(0, str(_PROJECT_ROOT / "backend"))
        from app.database import SessionLocal
        from app.services.signals_service import load_features_for_ticker

        db = SessionLocal()
        try:
            df = load_features_for_ticker(ticker, limit=limit, db=db)
            log.info("Loaded %d feature rows for %s", len(df), ticker)
            return {"ticker": ticker, "df": df, "error": None}
        finally:
            db.close()
    except Exception as exc:
        log.error("Failed to load features for %s: %s", ticker, exc)
        return {"ticker": ticker, "df": None, "error": str(exc)}


@task(name="run_inference", retries=1)
def run_inference_task(features_per_ticker: dict, confidence_threshold: float = 0.55) -> dict:
    """Run batch inference across all tickers."""
    log = get_run_logger() if HAS_PREFECT else logger
    from ml.inference.batch_predictor import run_batch_inference
    result = run_batch_inference(features_per_ticker, confidence_threshold)
    log.info(
        "Inference complete: %d signals across %d tickers",
        result["total_signals"],
        len(result["tickers_processed"]),
    )
    return result


@task(name="store_signals")
def store_signals_task(inference_result: dict) -> int:
    """Persist signals to the DB. Returns count of inserted rows."""
    log = get_run_logger() if HAS_PREFECT else logger
    sys.path.insert(0, str(_PROJECT_ROOT / "backend"))
    from app.database import SessionLocal
    from app.services.signals_service import bulk_insert_signals

    db = SessionLocal()
    try:
        count = bulk_insert_signals(inference_result["signals"], db)
        log.info("Inserted %d signals into DB", count)
        return count
    finally:
        db.close()


@task(name="log_inference_to_mlflow")
def log_inference_summary_task(inference_result: dict, rows_stored: int) -> None:
    """Log inference summary metrics to MLflow 'algotrade-inference' experiment."""
    log = get_run_logger() if HAS_PREFECT else logger
    try:
        import mlflow
        from ml.training.mlflow_logger import get_default_uri

        mlflow.set_tracking_uri(get_default_uri())
        mlflow.set_experiment("algotrade-inference")

        with mlflow.start_run(run_name=f"inference_{date.today()}"):
            mlflow.log_metrics({
                "total_signals":     inference_result["total_signals"],
                "tickers_processed": len(inference_result["tickers_processed"]),
                "tickers_skipped":   len(inference_result["tickers_skipped"]),
                "rows_stored":       rows_stored,
            })
            mlflow.log_param("model_run_id",  inference_result["model_run_id"])
            mlflow.log_param("model_version", inference_result["model_version"])
            mlflow.log_param("run_date",      str(date.today()))
        log.info("Logged inference summary to MLflow")
    except Exception as exc:
        log.warning("MLflow logging failed: %s", exc)


@flow(name="daily-inference-pipeline")
def daily_inference_flow(
    tickers: list[str] | None = None,
    confidence_threshold: float = 0.55,
    feature_limit: int = 60,
) -> dict:
    """
    Daily inference pipeline.
    1. Load features for each watchlist ticker.
    2. Run batch inference with champion model.
    3. Store signals in DB.
    4. Log summary to MLflow.
    """
    if tickers is None:
        from ml.data_pipeline.watchlist import get_tickers

        tickers = get_tickers()

    log = get_run_logger() if HAS_PREFECT else logger
    log.info("Starting inference for %d tickers", len(tickers))

    feature_results = [load_features_task(t, limit=feature_limit) for t in tickers]

    features_per_ticker = {
        r["ticker"]: r["df"]
        for r in feature_results
        if r["df"] is not None and not r["df"].empty
    }

    if not features_per_ticker:
        log.warning("No feature data available — aborting inference")
        return {"status": "no_data"}

    inference_result = run_inference_task(features_per_ticker, confidence_threshold)
    rows_stored      = store_signals_task(inference_result)
    log_inference_summary_task(inference_result, rows_stored)

    return {
        "status":      "complete",
        "run_date":    str(date.today()),
        "model_run_id": inference_result["model_run_id"],
        "total_signals": inference_result["total_signals"],
        "rows_stored":   rows_stored,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = daily_inference_flow()
    print(result)
