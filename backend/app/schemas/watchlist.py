from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WatchlistItemOut(BaseModel):
    id: int
    ticker: str
    company_name: str
    sector: Optional[str]
    added_at: datetime | None
    is_active: bool

    model_config = {"from_attributes": True}


class AddWatchlistRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    company_name: str | None = Field(default=None, max_length=200)
    sector: str | None = Field(default=None, max_length=120)


class WatchlistMutationResponse(BaseModel):
    success: bool
    ticker: str
    pipeline_status: str | None = None
    message: str
