"""Monitoring service for API endpoints."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_BACKEND_DIR = str(Path(__file__).parents[2])
_REPO_ROOT = str(Path(__file__).parents[3])
for _path in (_BACKEND_DIR, _REPO_ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from app.models.monitoring import MonitoringReport, RetrainLog


def get_latest_summary(db: Session) -> dict[str, Any]:
    report = _ensure_latest_report()
    last_retrain = _latest_retrain(db)
    details = report.get("details", {})
    data_drift = details.get("data_drift", {})
    alerts = [alert for alert in details.get("alerts", []) if alert.get("severity") != "INFO"]
    alert_level = report.get("alert_level") or "INFO"
    return {
        "id": report.get("id"),
        "report_date": report.get("report_date"),
        "report_type": report.get("report_type"),
        "drift_share": report.get("drift_share"),
        "prediction_drift_detected": bool(report.get("prediction_drift_detected")),
        "model_perf_f1": report.get("model_perf_f1"),
        "alert_level": alert_level,
        "system_status": _system_status(alert_level),
        "feature_count": int(data_drift.get("feature_count", 0)),
        "drifted_count": int(data_drift.get("drifted_count", 0)),
        "active_alerts": len(alerts),
        "evidently_report_html": report.get("evidently_report_html"),
        "created_at": report.get("created_at"),
        "last_retrain_at": last_retrain.triggered_at if last_retrain else None,
        "last_retrain_reason": last_retrain.trigger_reason if last_retrain else None,
    }


def get_monitoring_history(db: Session, days: int = 30) -> list[dict[str, Any]]:
    _ensure_latest_report()
    rows = (
        db.query(MonitoringReport)
        .order_by(MonitoringReport.report_date.desc(), MonitoringReport.created_at.desc())
        .limit(days)
        .all()
    )
    history = [
        {
            "id": row.id,
            "report_date": row.report_date,
            "report_type": row.report_type,
            "drift_share": row.drift_share,
            "prediction_drift_detected": row.prediction_drift_detected,
            "model_perf_f1": row.model_perf_f1,
            "alert_level": row.alert_level,
            "created_at": row.created_at,
        }
        for row in rows
    ]
    history.reverse()
    return history


def get_data_drift(db: Session) -> dict[str, Any]:
    details = _latest_details()
    return details.get("data_drift", {})


def get_feature_drift_scores(db: Session) -> list[dict[str, Any]]:
    details = _latest_details()
    return sorted(
        details.get("feature_details", []),
        key=lambda item: item.get("drift_score", 0.0),
        reverse=True,
    )


def get_prediction_drift(db: Session) -> dict[str, Any]:
    details = _latest_details()
    return details.get("prediction_drift", {})


def get_performance(db: Session) -> dict[str, Any]:
    details = _latest_details()
    return details.get("performance", {})


def get_freshness(db: Session) -> dict[str, Any]:
    details = _latest_details()
    return details.get("freshness", {})


def get_alerts(db: Session) -> list[dict[str, Any]]:
    details = _latest_details()
    return [alert for alert in details.get("alerts", []) if alert.get("severity") != "INFO"]


def manual_retrain(reason: str = "Manual trigger via API") -> dict[str, Any]:
    from ml.monitoring.retrain_trigger import maybe_trigger_retraining

    return maybe_trigger_retraining(manual_trigger=True, manual_reason=reason)


def get_retrain_history(db: Session, limit: int = 50) -> list[RetrainLog]:
    return (
        db.query(RetrainLog)
        .order_by(RetrainLog.triggered_at.desc(), RetrainLog.created_at.desc())
        .limit(limit)
        .all()
    )


def _latest_retrain(db: Session) -> RetrainLog | None:
    return (
        db.query(RetrainLog)
        .order_by(RetrainLog.triggered_at.desc(), RetrainLog.created_at.desc())
        .first()
    )


def _latest_details() -> dict[str, Any]:
    report = _ensure_latest_report()
    return report.get("details", {})


def _ensure_latest_report() -> dict[str, Any]:
    from ml.monitoring.drift_detector import (
        generate_and_save_monitoring_report,
        get_latest_saved_report,
        report_is_stale,
    )

    report = get_latest_saved_report()
    if report_is_stale(report):
        logger.info("Refreshing monitoring report on demand")
        report = generate_and_save_monitoring_report(report_type="api")
    return report


def _system_status(alert_level: str) -> str:
    mapping = {
        "INFO": "HEALTHY",
        "WARN": "WARNING",
        "CRITICAL": "CRITICAL",
    }
    return mapping.get(alert_level, "HEALTHY")
