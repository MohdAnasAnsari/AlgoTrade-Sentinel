from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.schemas.alerts import AlertListResponse, AlertOut, MarkAlertResponse, UnreadAlertCount
from app.services import alerts_service

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/")
def get_alerts(
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    severity: str | None = Query(None),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict:
    payload = alerts_service.list_alerts(
        db,
        limit=limit,
        offset=offset,
        severity=severity,
        unread_only=unread_only,
    )
    return ok(AlertListResponse(total=payload["total"], items=[AlertOut.model_validate(row) for row in payload["items"]]))


@router.get("/unread")
def unread_alerts(db: Session = Depends(get_db)) -> dict:
    return ok(UnreadAlertCount(unread=alerts_service.unread_count(db)))


@router.post("/{alert_id}/read")
def mark_alert_read(alert_id: int, db: Session = Depends(get_db)) -> dict:
    return ok(MarkAlertResponse(success=True, updated=alerts_service.mark_read(db, alert_id)))


@router.post("/read-all")
def mark_all_alerts_read(db: Session = Depends(get_db)) -> dict:
    return ok(MarkAlertResponse(success=True, updated=alerts_service.mark_all_read(db)))
