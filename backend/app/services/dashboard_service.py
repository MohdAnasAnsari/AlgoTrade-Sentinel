from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.features import LabelsData
from app.models.signals import Signal
from app.services.alerts_service import recent_alerts
from app.services.market_service import MarketService
from app.services.monitoring_service import get_latest_summary
from app.services.portfolio_service import get_history, get_open_positions, get_summary
from app.services.system_service import get_system_status
from app.services.training_service import get_best_run
from app.services.watchlist_service import get_watchlist_map


def get_dashboard_overview(db: Session) -> dict[str, Any]:
    portfolio_summary = get_summary(db)
    monitoring_summary = get_latest_summary(db)
    market_service = MarketService(db)
    tickers = market_service.get_tickers()
    watchlist_map = get_watchlist_map(db)
    system_status = get_system_status(db)
    best_run = get_best_run()

    market_overview = []
    for ticker in tickers[:5]:
        points = market_service.get_ohlcv(ticker.ticker, limit=22)
        market_overview.append(
            {
                "ticker": ticker.ticker,
                "company_name": watchlist_map.get(ticker.ticker, {}).get("company_name") or ticker.name,
                "current_price": ticker.last_close,
                "change_pct": ticker.change_pct,
                "points": [{"date": point.date, "close": float(point.close or 0.0)} for point in points],
            }
        )

    latest_signals = _latest_signal_feed(db)
    recent_alert_rows = recent_alerts(db, limit=5)

    champion_version = None
    champion_model_name = None
    champion_f1 = None
    try:
        from ml.training.mlflow_logger import REGISTERED_MODEL_NAME
        from app.services.registry_service import get_champion

        champion_model_name = REGISTERED_MODEL_NAME
        champion = get_champion(REGISTERED_MODEL_NAME)
        if champion:
            champion_version = _string_or_none(champion.get("version"))
            champion_f1 = champion.get("f1_macro")
    except Exception:
        champion = None

    current_f1 = monitoring_summary.get("model_perf_f1")
    if champion_f1 is None and best_run:
        champion_f1 = best_run.get("f1_macro")

    last_training_at = None
    if best_run and best_run.get("start_time"):
        last_training_at = datetime.fromisoformat(best_run["start_time"].replace("Z", "+00:00"))
    days_since_training = None
    if last_training_at is not None:
        days_since_training = (datetime.now(last_training_at.tzinfo) - last_training_at).days

    return {
        "portfolio": portfolio_summary,
        "signals_today": _signal_counts(latest_signals),
        "open_positions_count": len(get_open_positions(db)),
        "monitoring_status": monitoring_summary.get("system_status", "HEALTHY"),
        "market_overview": market_overview,
        "latest_signals": latest_signals,
        "portfolio_history": get_history(db, days=30),
        "recent_alerts": [
            {
                "id": row.id,
                "severity": row.severity,
                "message": row.message,
                "ticker": row.ticker,
                "created_at": row.created_at,
            }
            for row in recent_alert_rows
        ],
        "pipeline_status": _pipeline_cards(system_status.get("pipeline_runs", {})),
        "model_performance": {
            "champion_model_name": champion_model_name,
            "champion_model_version": champion_version,
            "champion_f1": champion_f1,
            "current_f1": current_f1,
            "days_since_last_training": days_since_training,
        },
    }


def _latest_signal_feed(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(Signal)
        .order_by(Signal.signal_date.desc(), Signal.created_at.desc())
        .limit(10)
        .all()
    )
    if rows:
        return [
            {
                "ticker": row.ticker,
                "signal": row.signal,
                "confidence": float(row.confidence) if row.confidence is not None else None,
                "signal_date": row.signal_date,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    label_rows = (
        db.query(LabelsData)
        .filter(LabelsData.signal_label.isnot(None))
        .order_by(LabelsData.date.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "ticker": row.ticker,
            "signal": row.signal_label,
            "confidence": None,
            "signal_date": row.date,
            "created_at": None,
        }
        for row in label_rows
    ]


def _signal_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    today = date.today()
    counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
    for row in rows:
        if row.get("signal_date") != today:
            continue
        signal = str(row.get("signal") or "HOLD").upper()
        if signal in counts:
            counts[signal] += 1
    return counts


def _pipeline_cards(pipeline_runs: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    mapping = {
        "daily_ingest": "Data Pipeline",
        "daily_features": "Feature Pipeline",
        "daily_inference": "Inference",
        "daily_monitoring": "Monitoring",
    }
    for key, label in mapping.items():
        payload = pipeline_runs.get(key, {}) or {}
        last_status = payload.get("last_status")
        state = "idle"
        if last_status in {"ok", "complete"}:
            state = "healthy"
        elif last_status == "failed":
            state = "critical"
        elif last_status in {"running", "scheduled"} or payload.get("last_observed_at"):
            state = "warning"
        items.append(
            {
                "key": key,
                "label": label,
                "status": state,
                "last_run_at": _iso(payload.get("last_finished_at") or payload.get("last_observed_at")),
                "last_status": last_status,
                "description": payload.get("last_error") or "Latest pipeline status",
            }
        )
    return items


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
