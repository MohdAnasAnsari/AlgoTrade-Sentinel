from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.schemas.monitoring import (
    DataDriftSummary,
    FeatureDriftDetail,
    FreshnessReport,
    ManualRetrainRequest,
    ManualRetrainResponse,
    MonitoringAlert,
    MonitoringHistoryItem,
    MonitoringSummary,
    PerformanceReport,
    PredictionDriftReport,
    RetrainHistoryItem,
)
from app.services import monitoring_service

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/latest")
def latest_monitoring_report(db: Session = Depends(get_db)) -> dict:
    return ok(MonitoringSummary(**monitoring_service.get_latest_summary(db)))


@router.get("/history")
def monitoring_history(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
) -> dict:
    rows = monitoring_service.get_monitoring_history(db, days=days)
    return ok([MonitoringHistoryItem(**row) for row in rows])


@router.get("/drift/data")
def data_drift_report(db: Session = Depends(get_db)) -> dict:
    return ok(DataDriftSummary(**monitoring_service.get_data_drift(db)))


@router.get("/drift/features")
def feature_drift_scores(db: Session = Depends(get_db)) -> dict:
    rows = monitoring_service.get_feature_drift_scores(db)
    return ok([FeatureDriftDetail(**row) for row in rows])


@router.get("/drift/predictions")
def prediction_drift_report(db: Session = Depends(get_db)) -> dict:
    return ok(PredictionDriftReport(**monitoring_service.get_prediction_drift(db)))


@router.get("/performance")
def performance_report(db: Session = Depends(get_db)) -> dict:
    return ok(PerformanceReport(**monitoring_service.get_performance(db)))


@router.get("/freshness")
def freshness_report(db: Session = Depends(get_db)) -> dict:
    return ok(FreshnessReport(**monitoring_service.get_freshness(db)))


@router.get("/alerts")
def active_alerts(db: Session = Depends(get_db)) -> dict:
    rows = monitoring_service.get_alerts(db)
    return ok([MonitoringAlert(**row) for row in rows])


@router.post("/retrain")
def manual_retrain(
    body: ManualRetrainRequest | None = Body(default=None),
) -> dict:
    payload = body or ManualRetrainRequest()
    result = monitoring_service.manual_retrain(reason=payload.reason)
    return ok(ManualRetrainResponse(**result))


@router.get("/retrain/history")
def retrain_history(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict:
    rows = monitoring_service.get_retrain_history(db, limit=limit)
    return ok([RetrainHistoryItem.model_validate(row) for row in rows])
