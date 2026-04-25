from sqlalchemy import (
    Column, Date, Index, Integer, Numeric, String, Text,
)

from app.models import Base, TimestampMixin


class BacktestResult(TimestampMixin, Base):
    __tablename__ = "backtest_results"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    run_id          = Column(String(36),  unique=True, nullable=False, index=True)
    batch_id        = Column(String(36),  nullable=True, index=True)
    ticker          = Column(String(20),  nullable=False)
    strategy_name   = Column(String(200), nullable=True)
    model_run_id    = Column(String(100), nullable=True)

    start_date      = Column(Date, nullable=True)
    end_date        = Column(Date, nullable=True)
    initial_capital = Column(Numeric(16, 2), default=100_000)
    transaction_cost = Column(Numeric(8, 6), default=0.001)
    slippage        = Column(Numeric(8, 6), default=0.0005)
    position_frac   = Column(Numeric(8, 4), default=0.10)

    # ── Return metrics ──────────────────────────────────────────────────────
    total_return      = Column(Numeric(12, 4))
    annualized_return = Column(Numeric(12, 4))
    benchmark_return  = Column(Numeric(12, 4))
    alpha             = Column(Numeric(12, 4))

    # ── Risk metrics ────────────────────────────────────────────────────────
    max_drawdown     = Column(Numeric(12, 4))
    sharpe_ratio     = Column(Numeric(12, 4))
    sortino_ratio    = Column(Numeric(12, 4))
    calmar_ratio     = Column(Numeric(12, 4))
    daily_volatility = Column(Numeric(12, 4))

    # ── Trade metrics ───────────────────────────────────────────────────────
    total_trades    = Column(Integer)
    win_rate        = Column(Numeric(8, 4))
    avg_win         = Column(Numeric(12, 4))
    avg_loss        = Column(Numeric(12, 4))
    profit_factor   = Column(Numeric(12, 4))
    avg_holding_days = Column(Numeric(8, 2))

    # ── JSON blobs ──────────────────────────────────────────────────────────
    equity_curve_json   = Column(Text)
    drawdown_json       = Column(Text)
    trades_json         = Column(Text)
    monthly_returns_json = Column(Text)

    __table_args__ = (
        Index("ix_backtest_ticker",    "ticker"),
        Index("ix_backtest_batch_id",  "batch_id"),
        Index("ix_backtest_created",   "created_at"),
    )
