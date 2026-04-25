from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


AlertSeverity = Literal["INFO", "WARN", "CRITICAL"]


class AlertOut(BaseModel):
    id: int
    alert_type: str
    ticker: Optional[str]
    message: str
    severity: AlertSeverity
    is_read: bool
    created_at: datetime | None

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    total: int
    items: list[AlertOut]


class UnreadAlertCount(BaseModel):
    unread: int


class MarkAlertResponse(BaseModel):
    success: bool
    updated: int
