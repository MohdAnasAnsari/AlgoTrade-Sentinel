from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models.features import DatasetVersion
from app.models.settings import AppSetting
from app.models.signals import Signal
from app.services.system_service import get_system_status

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

DEFAULT_SETTINGS: dict[str, dict[str, dict[str, Any]]] = {
    "model": {
        "signal_threshold": {"value": 0.55, "description": "Minimum class probability for acting on a signal."},
        "confidence_filter": {"value": 0.60, "description": "Filter to hide weak predictions in the UI."},
        "position_sizing_pct": {"value": 20.0, "description": "Target percent allocation per position."},
    },
    "backtest": {
        "initial_capital": {"value": 100_000.0, "description": "Default starting capital for backtests."},
        "transaction_cost": {"value": 0.001, "description": "Default transaction cost applied in backtests."},
        "slippage": {"value": 0.0005, "description": "Default slippage assumption for backtests."},
    },
    "retrain": {
        "auto_retrain_enabled": {"value": True, "description": "Enable automatic retraining checks."},
        "drift_threshold": {"value": 30.0, "description": "Drift share threshold that can trigger retraining."},
        "performance_threshold": {"value": 10.0, "description": "F1 degradation threshold that can trigger retraining."},
    },
    "portfolio": {
        "initial_cash": {"value": 100_000.0, "description": "Starting cash for the paper portfolio."},
        "max_positions": {"value": 5, "description": "Maximum simultaneous open paper positions."},
        "transaction_cost": {"value": 0.001, "description": "Transaction cost for each simulated trade."},
    },
}


def ensure_settings_seeded(db: Session) -> None:
    existing = {(row.category, row.key) for row in db.query(AppSetting.category, AppSetting.key).all()}
    created = False
    for category, section in DEFAULT_SETTINGS.items():
        for key, payload in section.items():
            if (category, key) in existing:
                continue
            db.add(
                AppSetting(
                    category=category,
                    key=key,
                    value_json=json.dumps(payload["value"]),
                    description=payload["description"],
                )
            )
            created = True
    if created:
        db.commit()


def get_effective_settings(db: Session) -> dict[str, dict[str, Any]]:
    ensure_settings_seeded(db)
    effective = {
        category: {key: payload["value"] for key, payload in values.items()}
        for category, values in DEFAULT_SETTINGS.items()
    }
    rows = db.query(AppSetting).all()
    for row in rows:
        effective.setdefault(row.category, {})
        effective[row.category][row.key] = _loads(row.value_json)
    return effective


def get_settings_response(db: Session) -> dict[str, Any]:
    effective = get_effective_settings(db)
    system_status = get_system_status(db)
    latest_dataset = db.query(DatasetVersion).order_by(DatasetVersion.version.desc()).first()
    latest_signal_version = (
        db.query(Signal.model_version)
        .filter(Signal.model_version.isnot(None), Signal.model_version != "")
        .order_by(Signal.created_at.desc())
        .first()
    )
    model_version = latest_signal_version[0] if latest_signal_version else None

    return {
        "model": effective["model"],
        "backtest": effective["backtest"],
        "retrain": effective["retrain"],
        "portfolio": effective["portfolio"],
        "environment": {
            "database_ok": bool(system_status["database"].get("ok")),
            "mlflow_ok": bool(system_status["mlflow"].get("ok")),
            "scheduler_running": bool(system_status["scheduler"].get("running")),
            "prefect_available": bool(system_status["scheduler"].get("prefect_available")),
            "last_pipeline_runs": system_status["pipeline_runs"],
        },
        "system": {
            "app_version": settings.APP_VERSION,
            "python_version": sys.version.split()[0],
            "model_version": model_version,
            "dataset_version": latest_dataset.version if latest_dataset else None,
        },
    }


def update_settings(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    ensure_settings_seeded(db)
    for category, values in payload.items():
        if values is None:
            continue
        for key, value in values.items():
            row = (
                db.query(AppSetting)
                .filter(AppSetting.category == category, AppSetting.key == key)
                .first()
            )
            if row is None:
                description = DEFAULT_SETTINGS.get(category, {}).get(key, {}).get("description")
                row = AppSetting(category=category, key=key, description=description, value_json="null")
                db.add(row)
            row.value_json = json.dumps(value)
    db.commit()
    return get_settings_response(db)


def get_portfolio_config(db: Session) -> dict[str, Any]:
    return get_effective_settings(db)["portfolio"]


def get_retrain_config(db: Session) -> dict[str, Any]:
    return get_effective_settings(db)["retrain"]


def _loads(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return value
