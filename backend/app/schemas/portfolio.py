from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel


PositionStatus = Literal["OPEN", "CLOSED"]


class PositionHighlight(BaseModel):
    ticker: str
    company_name: str | None = None
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class PortfolioSummary(BaseModel):
    snapshot_date: date | None
    total_value: float
    daily_change: float
    daily_change_pct: float
    total_pnl: float
    total_pnl_pct: float
    realized_pnl: float
    unrealized_pnl: float
    cash_balance: float
    invested_value: float
    open_positions: int
    initial_capital: float
    best_position: PositionHighlight | None = None
    worst_position: PositionHighlight | None = None


class PositionOut(BaseModel):
    id: int
    ticker: str
    entry_date: date
    entry_price: float
    shares: float
    current_price: float | None
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    status: PositionStatus
    company_name: str | None = None
    sector: str | None = None
    created_at: datetime | None

    model_config = {"from_attributes": True}


class PositionDetail(BaseModel):
    position: PositionOut
    orders: list["OrderOut"]


class OrderOut(BaseModel):
    id: int
    ticker: str
    order_date: date
    order_type: Literal["BUY", "SELL"]
    price: float
    shares: float
    total_value: float
    transaction_cost: float
    signal_id: int | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


class OrdersResponse(BaseModel):
    total: int
    items: list[OrderOut]


class PortfolioHistoryPoint(BaseModel):
    snapshot_date: date
    total_value: float
    cash_balance: float
    invested_value: float
    total_pnl: float
    total_pnl_pct: float
    realized_pnl: float
    unrealized_pnl: float


class PnLBreakdown(BaseModel):
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    total_pnl_pct: float
    best_position: PositionHighlight | None = None
    worst_position: PositionHighlight | None = None


PositionDetail.model_rebuild()
