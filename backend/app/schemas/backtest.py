"""Pydantic schemas for Backtesting Center API."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class StartBacktestRequest(BaseModel):
    model_run_id:     Optional[str]  = None
    tickers:          list[str]
    start_date:       str            = "2023-01-01"
    end_date:         str            = "2024-12-31"
    initial_capital:  float          = 100_000.0
    transaction_cost: float          = 0.001
    slippage:         float          = 0.0005
    position_frac:    float          = 0.10
    strategy_name:    Optional[str]  = None


class BacktestJobStatus(BaseModel):
    job_id:   str
    status:   str            # "running" | "complete" | "failed"
    message:  str
    run_ids:  list[str]      = []
    error:    Optional[str]  = None


class StartBacktestResponse(BaseModel):
    job_id:   str
    message:  str


class BacktestSummary(BaseModel):
    run_id:           str
    batch_id:         Optional[str]
    ticker:           str
    strategy_name:    Optional[str]
    model_run_id:     Optional[str]
    start_date:       Optional[str]
    end_date:         Optional[str]
    initial_capital:  Optional[float]
    # Key metrics only for table
    total_return:      Optional[float]
    annualized_return: Optional[float]
    benchmark_return:  Optional[float]
    alpha:             Optional[float]
    max_drawdown:      Optional[float]
    sharpe_ratio:      Optional[float]
    sortino_ratio:     Optional[float]
    calmar_ratio:      Optional[float]
    daily_volatility:  Optional[float]
    total_trades:      Optional[int]
    win_rate:          Optional[float]
    avg_win:           Optional[float]
    avg_loss:          Optional[float]
    profit_factor:     Optional[float]
    avg_holding_days:  Optional[float]
    created_at:        Optional[str]


class EquityPoint(BaseModel):
    date:      str
    value:     float
    benchmark: Optional[float]


class DrawdownPoint(BaseModel):
    date:     str
    drawdown: float


class Trade(BaseModel):
    entry_date:   str
    exit_date:    str
    entry_price:  float
    exit_price:   float
    shares:       float
    pnl:          float
    return_pct:   float
    holding_days: int


class BacktestDetail(BacktestSummary):
    transaction_cost: Optional[float]
    slippage:         Optional[float]
    position_frac:    Optional[float]
    equity_curve:     list[EquityPoint]  = []
    drawdown:         list[DrawdownPoint] = []
    trades:           list[Trade]         = []
    monthly_returns:  dict[str, float]    = {}


class BacktestMetrics(BaseModel):
    run_id:            str
    ticker:            str
    total_return:      Optional[float]
    annualized_return: Optional[float]
    benchmark_return:  Optional[float]
    alpha:             Optional[float]
    max_drawdown:      Optional[float]
    sharpe_ratio:      Optional[float]
    sortino_ratio:     Optional[float]
    calmar_ratio:      Optional[float]
    daily_volatility:  Optional[float]
    total_trades:      Optional[int]
    win_rate:          Optional[float]
    avg_win:           Optional[float]
    avg_loss:          Optional[float]
    profit_factor:     Optional[float]
    avg_holding_days:  Optional[float]
