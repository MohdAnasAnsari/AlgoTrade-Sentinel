from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.models import Base, TimestampMixin


class Position(TimestampMixin, Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    entry_date = Column(Date, nullable=False, index=True)
    entry_price = Column(Float, nullable=False)
    shares = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    market_value = Column(Float, nullable=False, default=0.0)
    unrealized_pnl = Column(Float, nullable=False, default=0.0)
    unrealized_pnl_pct = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default="OPEN")
    company_name = Column(String(200), nullable=True)
    sector = Column(String(120), nullable=True)

    __table_args__ = (
        Index("ix_positions_ticker_status", "ticker", "status"),
        Index("ix_positions_status", "status"),
    )


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    order_date = Column(Date, nullable=False, index=True)
    order_type = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)
    shares = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    transaction_cost = Column(Float, nullable=False, default=0.0)
    signal_id = Column(Integer, nullable=True, index=True)

    __table_args__ = (
        Index("ix_orders_ticker_date", "ticker", "order_date"),
        Index("ix_orders_type", "order_type"),
    )


class PortfolioSnapshot(TimestampMixin, Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, nullable=False, unique=True, index=True)
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_value = Column(Float, nullable=False)
    total_pnl = Column(Float, nullable=False)
    total_pnl_pct = Column(Float, nullable=False)
    realized_pnl = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, nullable=False)


class Alert(TimestampMixin, Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(50), nullable=False, index=True)
    ticker = Column(String(20), nullable=True, index=True)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="INFO", index=True)
    is_read = Column(Boolean, nullable=False, default=False, index=True)

    __table_args__ = (
        Index("ix_alerts_created_at", "created_at"),
    )


class Watchlist(TimestampMixin, Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, unique=True, index=True)
    company_name = Column(String(200), nullable=False)
    sector = Column(String(120), nullable=True)
    added_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    __table_args__ = (
        Index("ix_watchlists_active", "is_active"),
    )
