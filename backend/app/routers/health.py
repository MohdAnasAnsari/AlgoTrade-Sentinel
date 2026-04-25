from fastapi import APIRouter, Request

from app.config import settings
from app.core.response import ok
from app.scheduler import get_scheduler_state

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(request: Request) -> dict:
    return ok({
        "status": "ok",
        "version": settings.APP_VERSION,
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "scheduler": get_scheduler_state(),
    })
