from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)

from app.models import Base, TimestampMixin


class MarketData(TimestampMixin, Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Numeric(16, 6))
    high = Column(Numeric(16, 6))
    low = Column(Numeric(16, 6))
    close = Column(Numeric(16, 6))
    adj_close = Column(Numeric(16, 6))
    volume = Column(BigInteger)

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_market_data_ticker_date"),
        Index("ix_market_data_ticker", "ticker"),
        Index("ix_market_data_date", "date"),
        Index("ix_market_data_ticker_date", "ticker", "date"),
    )
