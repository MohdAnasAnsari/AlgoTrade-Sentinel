"""
Prefect flow: Backtesting Pipeline

Loads predictions from a trained model, runs backtest for each ticker,
and logs summary metrics to MLflow.
"""
import logging
import sys
from pathlib import Path

from prefect import flow, task

_PROJECT_ROOT = str(Path(__file__).parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logger = logging.getLogger(__name__)


@task(retries=1, retry_delay_seconds=30, name="run-backtest-ticker")
def run_backtest_task(
    ticker:          str,
    model_run_id:    str | None,
    start_date:      str,
    end_date:        str,
    initial_capital: float,
    transaction_cost: float,
    slippage:        float,
    position_frac:   float,
) -> dict:
    """Run backtest for a single ticker and return metrics."""
    import pandas as pd
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from ml.backtesting.backtest_engine import run_backtest

    _PROJECT = Path(__file__).parents[2]
    DB_PATH  = _PROJECT / "backend" / "algotrade.db"
    engine   = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
    Session  = sessionmaker(bind=engine)
    db       = Session()

    try:
        from backend.app.services.backtest_service import (
            _load_prices, _get_predictions,
        )
        prices = _load_prices(ticker, start_date, end_date, db)
        if prices.empty:
            raise ValueError(f"No price data for {ticker}")

        spy_prices = _load_prices("SPY", start_date, end_date, db)
        predictions = _get_predictions(model_run_id, ticker, start_date, end_date, db, prices)

        result = run_backtest(
            prices=prices,
            predictions=predictions,
            spy_prices=spy_prices if not spy_prices.empty else None,
            initial_capital=initial_capital,
            transaction_cost=transaction_cost,
            slippage=slippage,
            position_frac=position_frac,
        )
        return {"ticker": ticker, **result["metrics"]}
    finally:
        db.close()


@task(name="log-backtest-summary")
def log_summary_task(results: list[dict], model_run_id: str | None) -> None:
    """Log aggregate backtest metrics to MLflow."""
    try:
        import mlflow
        from ml.training.mlflow_logger import get_default_uri

        mlflow.set_tracking_uri(get_default_uri())
        mlflow.set_experiment("algotrade-backtests")

        with mlflow.start_run(run_name=f"backtest_{model_run_id or 'oracle'}"):
            mlflow.log_param("model_run_id", model_run_id or "oracle")
            mlflow.log_param("n_tickers", len(results))

            for r in results:
                ticker = r.get("ticker", "UNK")
                for key in ("total_return", "sharpe_ratio", "max_drawdown", "win_rate"):
                    if key in r:
                        mlflow.log_metric(f"{ticker}_{key}", float(r[key]))

            avg_return = sum(r.get("total_return", 0) for r in results) / max(len(results), 1)
            mlflow.log_metric("avg_total_return", round(avg_return, 4))
            logger.info("Logged %d backtest results to MLflow", len(results))
    except Exception as exc:
        logger.warning("MLflow logging failed: %s", exc)


@flow(name="backtesting-pipeline")
def backtesting_pipeline(
    model_run_id:    str | None = None,
    ticker_list:     list[str]  = None,
    start_date:      str        = "2023-01-01",
    end_date:        str        = "2024-12-31",
    initial_capital: float      = 100_000.0,
    transaction_cost: float     = 0.001,
    slippage:        float      = 0.0005,
    position_frac:   float      = 0.10,
) -> list[dict]:
    """
    Full backtesting pipeline:
    1. Run backtest for each ticker
    2. Log summary metrics to MLflow
    """
    tickers = ticker_list or ["AAPL"]
    results = []
    for ticker in tickers:
        result = run_backtest_task(
            ticker=ticker,
            model_run_id=model_run_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            transaction_cost=transaction_cost,
            slippage=slippage,
            position_frac=position_frac,
        )
        results.append(result)

    log_summary_task(results, model_run_id)
    return results


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-run-id", default=None)
    parser.add_argument("--tickers",      nargs="*", default=["AAPL"])
    parser.add_argument("--start",        default="2023-01-01")
    parser.add_argument("--end",          default="2024-12-31")
    parser.add_argument("--capital",      type=float, default=100_000)
    args = parser.parse_args()

    backtesting_pipeline(
        model_run_id=args.model_run_id,
        ticker_list=args.tickers,
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
    )
