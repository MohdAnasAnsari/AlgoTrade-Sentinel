from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.services.system_service import get_system_status

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
def system_status(db: Session = Depends(get_db)) -> dict:
    return ok(get_system_status(db))
