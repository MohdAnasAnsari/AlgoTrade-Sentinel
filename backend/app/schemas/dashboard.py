from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.portfolio import PortfolioSummary


PipelineState = Literal["healthy", "warning", "critical", "idle"]


class SparklinePoint(BaseModel):
    date: date
    close: float


class WatchlistSparkline(BaseModel):
    ticker: str
    company_name: str
    current_price: float | None
    change_pct: float | None
    points: list[SparklinePoint]


class DashboardSignalItem(BaseModel):
    ticker: str
    signal: str
    confidence: float | None
    signal_date: date | None
    created_at: datetime | None


class DashboardAlertItem(BaseModel):
    id: int
    severity: str
    message: str
    ticker: str | None
    created_at: datetime | None


class PipelineStatusItem(BaseModel):
    key: str
    label: str
    status: PipelineState
    last_run_at: str | None
    last_status: str | None
    description: str


class DashboardModelPerformance(BaseModel):
    champion_model_name: str | None
    champion_model_version: str | None
    champion_f1: float | None
    current_f1: float | None
    days_since_last_training: int | None


class DashboardOverview(BaseModel):
    portfolio: PortfolioSummary
    signals_today: dict[str, int]
    open_positions_count: int
    monitoring_status: str
    market_overview: list[WatchlistSparkline]
    latest_signals: list[DashboardSignalItem]
    portfolio_history: list[dict]
    recent_alerts: list[DashboardAlertItem]
    pipeline_status: list[PipelineStatusItem]
    model_performance: DashboardModelPerformance
