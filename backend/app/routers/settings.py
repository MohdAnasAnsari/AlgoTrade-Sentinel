from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.schemas.settings import AppSettingsResponse, UpdateSettingsRequest
from app.services import settings_service

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings(db: Session = Depends(get_db)) -> dict:
    return ok(AppSettingsResponse(**settings_service.get_settings_response(db)))


@router.post("")
def update_settings(body: UpdateSettingsRequest, db: Session = Depends(get_db)) -> dict:
    return ok(AppSettingsResponse(**settings_service.update_settings(db, body.model_dump(exclude_none=True))))
