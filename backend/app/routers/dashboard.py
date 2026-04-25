from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.schemas.dashboard import DashboardOverview
from app.services.dashboard_service import get_dashboard_overview

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview")
def dashboard_overview(db: Session = Depends(get_db)) -> dict:
    return ok(DashboardOverview(**get_dashboard_overview(db)))
