from sqlalchemy import (
    Column, Date, DateTime, Float, Index, Integer, String, Text,
)

from app.models import Base, TimestampMixin


class Signal(TimestampMixin, Base):
    __tablename__ = "signals"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    ticker       = Column(String(20),  nullable=False, index=True)
    signal_date  = Column(Date,        nullable=False, index=True)
    signal       = Column(String(10),  nullable=False)
    confidence   = Column(Float,       nullable=True)
    prob_buy     = Column(Float,       nullable=True)
    prob_sell    = Column(Float,       nullable=True)
    prob_hold    = Column(Float,       nullable=True)
    model_version = Column(String(20), nullable=True)
    model_run_id  = Column(String(100),nullable=True)
    explanation   = Column(Text,       nullable=True)

    __table_args__ = (
        Index("ix_signals_ticker_date", "ticker", "signal_date"),
        Index("ix_signals_signal",      "signal"),
        Index("ix_signals_created",     "created_at"),
    )


class ModelRegistryLog(TimestampMixin, Base):
    __tablename__ = "model_registry_logs"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    model_name   = Column(String(200), nullable=False)
    version      = Column(String(20),  nullable=False)
    stage        = Column(String(50),  nullable=False)
    f1_score     = Column(Float,       nullable=True)
    promoted_at  = Column(DateTime,    nullable=True)
    promoted_by  = Column(String(100), nullable=True)
    notes        = Column(Text,        nullable=True)
    mlflow_run_id = Column(String(100),nullable=True)

    __table_args__ = (
        Index("ix_registry_model_version", "model_name", "version"),
        Index("ix_registry_stage",         "stage"),
    )
