from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from app.models import Base, TimestampMixin


class FeaturesData(TimestampMixin, Base):
    __tablename__ = "features_data"

    id     = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False)
    date   = Column(Date, nullable=False)

    # Reference price stored for display convenience
    close  = Column(Numeric(16, 6))

    # ── Trend ──────────────────────────────────────────────────────────
    sma_10  = Column(Numeric(16, 6))
    sma_20  = Column(Numeric(16, 6))
    sma_50  = Column(Numeric(16, 6))
    sma_200 = Column(Numeric(16, 6))
    ema_10  = Column(Numeric(16, 6))
    ema_20  = Column(Numeric(16, 6))
    ema_50  = Column(Numeric(16, 6))
    macd_line        = Column(Numeric(16, 6))
    macd_signal      = Column(Numeric(16, 6))
    macd_hist        = Column(Numeric(16, 6))
    adx_14           = Column(Numeric(10, 4))
    price_vs_sma20_pct = Column(Numeric(10, 4))
    price_vs_sma50_pct = Column(Numeric(10, 4))

    # ── Momentum ───────────────────────────────────────────────────────
    rsi_14   = Column(Numeric(10, 4))
    stoch_k  = Column(Numeric(10, 4))
    stoch_d  = Column(Numeric(10, 4))
    roc_10   = Column(Numeric(10, 4))
    williams_r = Column(Numeric(10, 4))

    # ── Volatility ─────────────────────────────────────────────────────
    bb_upper   = Column(Numeric(16, 6))
    bb_lower   = Column(Numeric(16, 6))
    bb_width   = Column(Numeric(10, 4))
    bb_pct_b   = Column(Numeric(10, 4))
    atr_14     = Column(Numeric(16, 6))
    hist_vol_20 = Column(Numeric(10, 4))

    # ── Volume ──────────────────────────────────────────────────────────
    obv        = Column(BigInteger)
    vol_sma_20 = Column(Numeric(20, 2))
    vol_ratio  = Column(Numeric(10, 4))
    cmf_20     = Column(Numeric(10, 4))

    # ── Price action ────────────────────────────────────────────────────
    daily_return    = Column(Numeric(10, 4))
    return_3d       = Column(Numeric(10, 4))
    return_5d       = Column(Numeric(10, 4))
    return_10d      = Column(Numeric(10, 4))
    gap_pct         = Column(Numeric(10, 4))
    hl_range_pct    = Column(Numeric(10, 4))
    candle_body_pct = Column(Numeric(10, 4))

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_features_ticker_date"),
        Index("ix_features_ticker",      "ticker"),
        Index("ix_features_date",        "date"),
        Index("ix_features_ticker_date", "ticker", "date"),
    )


class LabelsData(TimestampMixin, Base):
    __tablename__ = "labels_data"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    ticker           = Column(String(20), nullable=False)
    date             = Column(Date, nullable=False)
    future_return_5d = Column(Numeric(12, 8))
    signal_label     = Column(String(10))

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_labels_ticker_date"),
        Index("ix_labels_ticker",      "ticker"),
        Index("ix_labels_date",        "date"),
        Index("ix_labels_ticker_date", "ticker", "date"),
    )


class DatasetVersion(TimestampMixin, Base):
    __tablename__ = "dataset_versions"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    version          = Column(Integer, nullable=False, unique=True)
    tickers          = Column(Text)
    date_range_start = Column(Date)
    date_range_end   = Column(Date)
    n_rows           = Column(Integer)
    n_train          = Column(Integer)
    n_test           = Column(Integer)
    feature_list     = Column(Text)
    label_distribution = Column(Text)
    split_date       = Column(Date)
    file_path        = Column(String(500))
