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

from app.models import Base, TimestampMixin


class MonitoringReport(TimestampMixin, Base):
    __tablename__ = "monitoring_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(Date, nullable=False, index=True)
    report_type = Column(String(50), nullable=False, default="daily")
    drift_share = Column(Float, nullable=True)
    drifted_features_json = Column(Text, nullable=True)
    prediction_drift_detected = Column(Boolean, nullable=False, default=False)
    model_perf_f1 = Column(Float, nullable=True)
    alert_level = Column(String(20), nullable=False, default="INFO")
    evidently_report_html = Column(String(500), nullable=True)

    __table_args__ = (
        Index("ix_monitoring_reports_date_type", "report_date", "report_type"),
        Index("ix_monitoring_reports_alert_level", "alert_level"),
    )


class RetrainLog(TimestampMixin, Base):
    __tablename__ = "retrain_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    triggered_at = Column(DateTime, nullable=False, index=True)
    trigger_reason = Column(Text, nullable=False)
    old_model_version = Column(String(50), nullable=True)
    new_model_version = Column(String(50), nullable=True)
    new_f1 = Column(Float, nullable=True)
    promoted = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_retrain_logs_promoted", "promoted"),
    )
