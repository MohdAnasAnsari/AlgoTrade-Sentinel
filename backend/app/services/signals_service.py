"""
Signals service — background inference jobs, DB CRUD for signals.
"""
from __future__ import annotations

import logging
import sys
import threading
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)

_PROJECT_ROOT = str(Path(__file__).parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# In-memory job store
_jobs: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Background inference job
# ---------------------------------------------------------------------------

def start_inference_job(request_dict: dict) -> str:
    """Kick off background inference job. Returns job_id."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status":        "running",
        "message":       "Inference started…",
        "total_signals": None,
        "model_run_id":  None,
        "model_version": None,
        "error":         None,
    }

    def _worker():
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            tickers             = request_dict.get("tickers")
            confidence_threshold = float(request_dict.get("confidence_threshold", 0.55))
            feature_limit       = int(request_dict.get("feature_limit", 60))

            if not tickers:
                sys.path.insert(0, _PROJECT_ROOT)
                from ml.data_pipeline.watchlist import get_tickers

                tickers = get_tickers()

            features_per_ticker = {}
            for ticker in tickers:
                try:
                    df = load_features_for_ticker(ticker, limit=feature_limit, db=db)
                    if not df.empty:
                        features_per_ticker[ticker] = df
                except Exception as exc:
                    logger.warning("Feature load failed for %s: %s", ticker, exc)

            from ml.inference.batch_predictor import run_batch_inference
            result = run_batch_inference(features_per_ticker, confidence_threshold)

            stored = bulk_insert_signals(result["signals"], db)
            _jobs[job_id].update({
                "status":        "complete",
                "message":       f"Inference complete — {stored} signals stored",
                "total_signals": result["total_signals"],
                "model_run_id":  result["model_run_id"],
                "model_version": result["model_version"],
            })
        except Exception as exc:
            logger.exception("Inference job %s failed", job_id)
            _jobs[job_id].update({"status": "failed", "message": "Inference failed", "error": str(exc)})
        finally:
            db.close()

    threading.Thread(target=_worker, daemon=True).start()
    return job_id


def get_job_status(job_id: str) -> Optional[dict]:
    return _jobs.get(job_id)


# ---------------------------------------------------------------------------
# Feature loading
# ---------------------------------------------------------------------------

def load_features_for_ticker(ticker: str, limit: int = 60, db=None) -> pd.DataFrame:
    """
    Load recent feature-engineered rows for ticker from features_data table.
    Returns DataFrame indexed by date with feature columns.
    """
    from app.models.features import FeaturesData

    rows = (
        db.query(FeaturesData)
        .filter(FeaturesData.ticker == ticker)
        .order_by(FeaturesData.date.desc())
        .limit(limit)
        .all()
    )
    if not rows:
        return pd.DataFrame()

    columns = [c.key for c in FeaturesData.__table__.columns]
    df = pd.DataFrame([{col: getattr(r, col) for col in columns} for r in rows])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    return df


# ---------------------------------------------------------------------------
# DB signal operations
# ---------------------------------------------------------------------------

def bulk_insert_signals(signals: list[dict], db) -> int:
    """Insert a list of signal dicts into the signals table. Returns count inserted."""
    from app.models.signals import Signal

    if not signals:
        return 0

    count = 0
    for sig in signals:
        try:
            row = Signal(
                ticker=sig["ticker"],
                signal_date=sig["signal_date"],
                signal=sig["signal"],
                confidence=sig.get("confidence"),
                prob_buy=sig.get("prob_buy"),
                prob_sell=sig.get("prob_sell"),
                prob_hold=sig.get("prob_hold"),
                model_version=str(sig.get("model_version") or ""),
                model_run_id=sig.get("model_run_id"),
                explanation=sig.get("explanation"),
            )
            db.add(row)
            count += 1
        except Exception as exc:
            logger.warning("Failed to prepare signal row: %s", exc)

    try:
        db.commit()
    except Exception as exc:
        logger.error("Bulk insert commit failed: %s", exc)
        db.rollback()
        return 0

    return count


def _signal_to_dict(row) -> dict:
    return {
        "ticker":        row.ticker,
        "signal_date":   row.signal_date,
        "signal":        row.signal,
        "confidence":    row.confidence,
        "prob_buy":      row.prob_buy,
        "prob_sell":     row.prob_sell,
        "prob_hold":     row.prob_hold,
        "model_version": row.model_version,
        "explanation":   row.explanation,
    }


def get_latest_signals(db, signal_filter: Optional[str] = None) -> list[dict]:
    """Return the most recent signal per ticker, optionally filtered by BUY/SELL/HOLD."""
    from sqlalchemy import func
    from app.models.signals import Signal

    subq = (
        db.query(Signal.ticker, func.max(Signal.signal_date).label("max_date"))
        .group_by(Signal.ticker)
        .subquery()
    )
    query = db.query(Signal).join(
        subq,
        (Signal.ticker == subq.c.ticker) & (Signal.signal_date == subq.c.max_date),
    )
    if signal_filter:
        query = query.filter(Signal.signal == signal_filter.upper())
    rows = query.order_by(Signal.ticker).all()
    if rows:
        return [_signal_to_dict(r) for r in rows]

    return _fallback_latest_label_signals(db, signal_filter=signal_filter)


def get_ticker_signal_history(
    ticker: str,
    db,
    limit: int = 90,
) -> list[dict]:
    """Return signal history for one ticker, joined with close price."""
    from app.models.signals import Signal
    from app.models.market import MarketData

    pairs = (
        db.query(Signal, MarketData.close)
        .outerjoin(
            MarketData,
            (MarketData.ticker == Signal.ticker) & (MarketData.date == Signal.signal_date),
        )
        .filter(Signal.ticker == ticker)
        .order_by(Signal.signal_date.desc())
        .limit(limit)
        .all()
    )
    if pairs:
        return [
            {
                "signal_date": sig.signal_date,
                "signal":      sig.signal,
                "confidence":  sig.confidence,
                "prob_buy":    sig.prob_buy,
                "prob_sell":   sig.prob_sell,
                "prob_hold":   sig.prob_hold,
                "explanation": sig.explanation,
                "close":       close,
            }
            for sig, close in pairs
        ]
    return _fallback_signal_history(db, ticker=ticker, limit=limit)


def get_signal_by_id(signal_id: int, db) -> Optional[dict]:
    from app.models.signals import Signal
    row = db.query(Signal).filter(Signal.id == signal_id).first()
    if not row:
        return None
    return {
        "id":            row.id,
        "ticker":        row.ticker,
        "signal_date":   row.signal_date,
        "signal":        row.signal,
        "confidence":    row.confidence,
        "prob_buy":      row.prob_buy,
        "prob_sell":     row.prob_sell,
        "prob_hold":     row.prob_hold,
        "model_version": row.model_version,
        "model_run_id":  row.model_run_id,
        "explanation":   row.explanation,
        "created_at":    row.created_at,
    }


def get_ticker_latest_signal(ticker: str, db) -> Optional[dict]:
    from app.models.signals import Signal
    row = (
        db.query(Signal)
        .filter(Signal.ticker == ticker)
        .order_by(Signal.signal_date.desc())
        .first()
    )
    if not row:
        latest = _fallback_latest_label_signals(db)
        return next((item for item in latest if item["ticker"] == ticker.upper()), None)
    return {
        "ticker":        row.ticker,
        "signal_date":   row.signal_date,
        "signal":        row.signal,
        "confidence":    row.confidence,
        "prob_buy":      row.prob_buy,
        "prob_sell":     row.prob_sell,
        "prob_hold":     row.prob_hold,
        "model_version": row.model_version,
        "explanation":   row.explanation,
    }


def _fallback_latest_label_signals(db, signal_filter: Optional[str] = None) -> list[dict]:
    from sqlalchemy import func
    from app.models.features import LabelsData

    subq = (
        db.query(LabelsData.ticker, func.max(LabelsData.date).label("max_date"))
        .filter(LabelsData.signal_label.isnot(None))
        .group_by(LabelsData.ticker)
        .subquery()
    )
    query = db.query(LabelsData).join(
        subq,
        (LabelsData.ticker == subq.c.ticker) & (LabelsData.date == subq.c.max_date),
    )
    if signal_filter:
        query = query.filter(LabelsData.signal_label == signal_filter.upper())
    rows = query.order_by(LabelsData.ticker).all()
    return [
        {
            "ticker":        r.ticker,
            "signal_date":   r.date,
            "signal":        r.signal_label,
            "confidence":    None,
            "prob_buy":      None,
            "prob_sell":     None,
            "prob_hold":     None,
            "model_version": "dataset-fallback",
            "explanation":   None,
        }
        for r in rows
    ]


def _fallback_signal_history(db, ticker: str, limit: int) -> list[dict]:
    from app.models.features import LabelsData
    from app.models.market import MarketData

    pairs = (
        db.query(LabelsData, MarketData.close)
        .outerjoin(
            MarketData,
            (MarketData.ticker == LabelsData.ticker) & (MarketData.date == LabelsData.date),
        )
        .filter(LabelsData.ticker == ticker.upper(), LabelsData.signal_label.isnot(None))
        .order_by(LabelsData.date.desc())
        .limit(limit)
        .all()
    )
    return [
        {"signal_date": lbl.date, "signal": lbl.signal_label, "confidence": None, "close": close}
        for lbl, close in pairs
    ]
