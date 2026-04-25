from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel


class OHLCVRow(BaseModel):
    date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    adj_close: Optional[float] = None
    volume: Optional[int] = None

    model_config = {"from_attributes": True}


class TickerInfo(BaseModel):
    ticker: str
    name: str
    sector: str
    last_date: Optional[date] = None
    last_close: Optional[float] = None
    volume: Optional[int] = None
    freshness: Literal["fresh", "stale", "missing"]
    change_pct: Optional[float] = None


class TickerStats(BaseModel):
    ticker: str
    current_price: Optional[float] = None
    week52_high: Optional[float] = None
    week52_low: Optional[float] = None
    avg_volume: Optional[float] = None
    ytd_return: Optional[float] = None
    data_from: Optional[date] = None
    data_to: Optional[date] = None


class FreshnessInfo(BaseModel):
    ticker: str
    status: Literal["fresh", "stale", "missing"]
    last_date: Optional[date] = None
    days_stale: Optional[int] = None


class FreshnessReport(BaseModel):
    tickers: dict[str, FreshnessInfo]
    checked_at: datetime


class IngestRequest(BaseModel):
    tickers: Optional[list[str]] = None  # None = use watchlist


class IngestResponse(BaseModel):
    message: str
    tickers_ingested: list[str]
    tickers_failed: list[str]
    rows_added: int
