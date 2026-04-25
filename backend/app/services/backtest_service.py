"""
Backtest service — orchestrates inference, engine, and DB persistence.
"""
from __future__ import annotations

import json
import logging
import sys
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_PROJECT_ROOT = str(Path(__file__).parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ── In-memory job store ────────────────────────────────────────────────────────
_jobs: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Job management
# ---------------------------------------------------------------------------

def start_backtest_job(request_dict: dict) -> str:
    """Kick off background job. Returns job_id."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "message": "Backtest started…", "run_ids": [], "error": None}

    def _worker():
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            run_ids = _execute_backtest(request_dict, job_id, db)
            _jobs[job_id].update({
                "status":  "complete",
                "message": f"Backtest complete — {len(run_ids)} result(s)",
                "run_ids": run_ids,
            })
        except Exception as exc:
            logger.exception("Backtest job %s failed", job_id)
            _jobs[job_id].update({"status": "failed", "message": "Backtest failed", "error": str(exc)})
        finally:
            db.close()

    threading.Thread(target=_worker, daemon=True).start()
    return job_id


def get_job_status(job_id: str) -> Optional[dict]:
    return _jobs.get(job_id)


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------

def _execute_backtest(req: dict, batch_id: str, db) -> list[str]:
    import pandas as pd
    from ml.backtesting.backtest_engine import run_backtest
    from app.models.backtest import BacktestResult

    tickers          = req["tickers"]
    model_run_id     = req.get("model_run_id")
    start_date       = req.get("start_date", "2023-01-01")
    end_date         = req.get("end_date",   "2024-12-31")
    initial_capital  = float(req.get("initial_capital",  100_000))
    transaction_cost = float(req.get("transaction_cost", 0.001))
    slippage         = float(req.get("slippage",         0.0005))
    position_frac    = float(req.get("position_frac",    0.10))
    strategy_name    = req.get("strategy_name") or (
        f"Model:{model_run_id[:8]}" if model_run_id else "Oracle"
    )

    spy_prices = _load_prices("SPY", start_date, end_date, db)

    run_ids = []
    for ticker in tickers:
        try:
            logger.info("Running backtest for %s", ticker)

            prices = _load_prices(ticker, start_date, end_date, db)
            if prices.empty:
                logger.warning("No prices for %s — skipping", ticker)
                continue

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

            run_id = str(uuid.uuid4())
            m = result["metrics"]

            # Determine actual date range from price data
            actual_start = prices["date"].min()
            actual_end   = prices["date"].max()

            record = BacktestResult(
                run_id           = run_id,
                batch_id         = batch_id,
                ticker           = ticker,
                strategy_name    = strategy_name,
                model_run_id     = model_run_id,
                start_date       = actual_start,
                end_date         = actual_end,
                initial_capital  = initial_capital,
                transaction_cost = transaction_cost,
                slippage         = slippage,
                position_frac    = position_frac,
                # Metrics
                total_return      = m["total_return"],
                annualized_return = m["annualized_return"],
                benchmark_return  = m["benchmark_return"],
                alpha             = m["alpha"],
                max_drawdown      = m["max_drawdown"],
                sharpe_ratio      = m["sharpe_ratio"],
                sortino_ratio     = m["sortino_ratio"],
                calmar_ratio      = m["calmar_ratio"],
                daily_volatility  = m["daily_volatility"],
                total_trades      = m["total_trades"],
                win_rate          = m["win_rate"],
                avg_win           = m["avg_win"],
                avg_loss          = m["avg_loss"],
                profit_factor     = m["profit_factor"],
                avg_holding_days  = m["avg_holding_days"],
                # JSON blobs
                equity_curve_json    = json.dumps(result["equity_curve"]),
                drawdown_json        = json.dumps(result["drawdown"]),
                trades_json          = json.dumps(result["trades"]),
                monthly_returns_json = json.dumps(result["monthly_returns"]),
            )
            db.add(record)
            db.commit()
            run_ids.append(run_id)
            logger.info("Backtest saved %s — total_return=%.2f%%", run_id, float(m["total_return"]))

        except Exception as exc:
            logger.error("Backtest failed for %s: %s", ticker, exc, exc_info=True)
            db.rollback()

    return run_ids


# ---------------------------------------------------------------------------
# Helpers — data loading
# ---------------------------------------------------------------------------

def _load_prices(ticker: str, start_date: str, end_date: str, db) -> "pd.DataFrame":
    import datetime as dt
    import pandas as pd
    from app.models.market import MarketData

    rows = (
        db.query(MarketData.date, MarketData.open, MarketData.high, MarketData.low, MarketData.close)
        .filter(
            MarketData.ticker == ticker,
            MarketData.date >= dt.date.fromisoformat(start_date),
            MarketData.date <= dt.date.fromisoformat(end_date),
        )
        .order_by(MarketData.date)
        .all()
    )

    if not rows:
        if ticker == "SPY":
            return _fetch_spy_yfinance(start_date, end_date)
        return pd.DataFrame(columns=["date", "open", "high", "low", "close"])

    return pd.DataFrame(rows, columns=["date", "open", "high", "low", "close"])


def _fetch_spy_yfinance(start_date: str, end_date: str) -> "pd.DataFrame":
    import pandas as pd
    try:
        import yfinance as yf
        df = yf.download("SPY", start=start_date, end=end_date, auto_adjust=True, progress=False)
        if df.empty:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close"])
        df = df.reset_index()
        df.columns = [c.lower() if isinstance(c, str) else c[0].lower() for c in df.columns]
        df = df.rename(columns={"index": "date"})
        df["date"] = pd.to_datetime(df["date"])
        return df[["date", "open", "high", "low", "close"]].dropna()
    except Exception as exc:
        logger.warning("Could not fetch SPY from yfinance: %s", exc)
        import pandas as pd
        return pd.DataFrame(columns=["date", "open", "high", "low", "close"])


def _get_predictions(
    model_run_id: Optional[str],
    ticker: str,
    start_date: str,
    end_date: str,
    db,
    prices: "pd.DataFrame",
) -> "pd.Series":
    import pandas as pd

    if model_run_id:
        try:
            features_df = _load_features(ticker, start_date, end_date, db)
            if not features_df.empty:
                from ml.backtesting.inference import generate_predictions
                return generate_predictions(model_run_id, features_df)
        except Exception as exc:
            logger.warning("Model inference failed (%s) — falling back to oracle: %s", model_run_id, exc)

    # Oracle fallback: use labels_data from DB
    return _load_oracle_predictions(ticker, start_date, end_date, db, prices)


def _load_features(ticker: str, start_date: str, end_date: str, db) -> "pd.DataFrame":
    import datetime as dt
    import pandas as pd
    from app.models.features import FeaturesData

    rows = (
        db.query(FeaturesData)
        .filter(
            FeaturesData.ticker == ticker,
            FeaturesData.date >= dt.date.fromisoformat(start_date),
            FeaturesData.date <= dt.date.fromisoformat(end_date),
        )
        .order_by(FeaturesData.date)
        .all()
    )

    if not rows:
        return pd.DataFrame()

    columns = [c.key for c in FeaturesData.__table__.columns]
    return pd.DataFrame([{col: getattr(r, col) for col in columns} for r in rows])


def _load_oracle_predictions(
    ticker: str,
    start_date: str,
    end_date: str,
    db,
    prices: "pd.DataFrame",
) -> "pd.Series":
    import datetime as dt
    import pandas as pd
    from app.models.features import LabelsData

    rows = (
        db.query(LabelsData.date, LabelsData.signal_label)
        .filter(
            LabelsData.ticker == ticker,
            LabelsData.date >= dt.date.fromisoformat(start_date),
            LabelsData.date <= dt.date.fromisoformat(end_date),
            LabelsData.signal_label.isnot(None),
        )
        .order_by(LabelsData.date)
        .all()
    )

    if rows:
        df = pd.DataFrame(rows, columns=["date", "signal"])
        df["date"] = pd.to_datetime(df["date"])
        return pd.Series(df["signal"].values, index=pd.DatetimeIndex(df["date"].values), name="signal")

    # Last resort: generate random BUY/HOLD/SELL for demo
    logger.warning("No predictions/labels for %s — using HOLD-only signals", ticker)
    prices_copy = prices.copy()
    prices_copy["date"] = pd.to_datetime(prices_copy["date"])
    return pd.Series(
        ["HOLD"] * len(prices_copy),
        index=pd.DatetimeIndex(prices_copy["date"].values),
        name="signal",
    )


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def _model_to_dict(obj) -> dict:
    from decimal import Decimal
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.key)
        if isinstance(val, Decimal):
            val = float(val)
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        d[col.key] = val
    return d


def list_backtest_runs(db, limit: int = 200) -> list[dict]:
    from app.models.backtest import BacktestResult

    rows = (
        db.query(BacktestResult)
        .order_by(BacktestResult.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_model_to_dict(r) for r in rows]


def get_backtest_detail(run_id: str, db) -> Optional[dict]:
    from app.models.backtest import BacktestResult

    row = db.query(BacktestResult).filter(BacktestResult.run_id == run_id).first()
    if row is None:
        return None
    return _model_to_dict(row)


def compare_runs(run_ids: list[str], db) -> list[dict]:
    from app.models.backtest import BacktestResult

    rows = db.query(BacktestResult).filter(BacktestResult.run_id.in_(run_ids)).all()
    return [_model_to_dict(r) for r in rows]
