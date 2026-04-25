from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from fastapi import Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T")


class ResponseMeta(BaseModel):
    timestamp: str
    version: str


class StandardResponse(BaseModel, Generic[T]):
    data: T
    meta: ResponseMeta


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: ResponseMeta
    page: int
    limit: int
    total: int
    pages: int


def _meta() -> dict[str, str]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
    }


def ok(data: Any) -> dict[str, Any]:
    """Wrap a payload in the standard { data, meta } envelope."""
    return {"data": data, "meta": _meta()}


def paginated(
    items: list[Any],
    *,
    page: int,
    limit: int,
    total: int,
) -> dict[str, Any]:
    """Wrap a list payload in the standard paginated envelope."""
    pages = max(1, (total + limit - 1) // limit)
    return {
        "data": items,
        "meta": _meta(),
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
    }
