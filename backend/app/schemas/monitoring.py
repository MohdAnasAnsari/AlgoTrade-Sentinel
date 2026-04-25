from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel


AlertSeverity = Literal["INFO", "WARN", "CRITICAL"]
SystemHealth = Literal["HEALTHY", "WARNING", "CRITICAL"]


class MonitoringAlert(BaseModel):
    id: str
    severity: AlertSeverity
    title: str
    description: str
    timestamp: str


class HistogramBin(BaseModel):
    bin_start: float
    bin_end: float
    reference_density: float
    current_density: float


class FeatureDriftDetail(BaseModel):
    feature: str
    drift_detected: bool
    drift_score: float
    p_value: Optional[float]
    reference_mean: Optional[float]
    current_mean: Optional[float]
    reference_std: Optional[float]
    current_std: Optional[float]
    reference_count: int
    current_count: int
    histogram: list[HistogramBin]


class DataDriftSummary(BaseModel):
    drift_share: float
    drifted_count: int
    feature_count: int
    summary_text: str
    top_drifted: list[FeatureDriftDetail]


class PredictionDriftReport(BaseModel):
    detected: bool
    threshold: float
    reference_counts: dict[str, int]
    current_counts: dict[str, int]
    reference_ratios: dict[str, float]
    current_ratios: dict[str, float]
    ratio_shifts: dict[str, float]
    largest_ratio_shift: float
    reference_total: int
    current_total: int


class RollingPerformancePoint(BaseModel):
    date: str
    f1: float
    accuracy: float
    sample_size: int


class PerformanceReport(BaseModel):
    ground_truth_available: bool
    window_days: int
    baseline_f1: Optional[float]
    baseline_accuracy: Optional[float]
    baseline_source: Optional[str]
    last_training_at: Optional[str]
    current_f1: Optional[float]
    current_accuracy: Optional[float]
    degradation_pct: Optional[float]
    degradation_detected: bool
    sample_size: int
    rolling: list[RollingPerformancePoint]


class FreshnessTickerStatus(BaseModel):
    ticker: str
    last_market_date: Optional[str]
    last_ingested_at: Optional[str]
    days_stale: Optional[int]
    status: Literal["fresh", "stale"]


class FreshnessReport(BaseModel):
    checked_at: str
    stale_threshold_days: int
    stale_count: int
    ticker_count: int
    tickers: list[FreshnessTickerStatus]


class MonitoringMetadata(BaseModel):
    generated_at: Optional[str] = None
    report_type: Optional[str] = None
    reference_dataset_version: Optional[int] = None
    reference_dataset_path: Optional[str] = None
    reference_rows: Optional[int] = None
    current_rows: Optional[int] = None
    current_window_days: Optional[int] = None
    feature_columns: list[str] = []
    current_as_of_date: Optional[str] = None
    drift_p_value_threshold: Optional[float] = None
    prediction_shift_threshold: Optional[float] = None


class MonitoringDetail(BaseModel):
    metadata: MonitoringMetadata
    data_drift: DataDriftSummary
    feature_details: list[FeatureDriftDetail]
    prediction_drift: PredictionDriftReport
    performance: PerformanceReport
    freshness: FreshnessReport
    alerts: list[MonitoringAlert]


class MonitoringSummary(BaseModel):
    id: Optional[int]
    report_date: Optional[date]
    report_type: Optional[str]
    drift_share: Optional[float]
    prediction_drift_detected: bool
    model_perf_f1: Optional[float]
    alert_level: AlertSeverity
    system_status: SystemHealth
    feature_count: int
    drifted_count: int
    active_alerts: int
    evidently_report_html: Optional[str]
    created_at: Optional[datetime]
    last_retrain_at: Optional[datetime]
    last_retrain_reason: Optional[str]


class MonitoringHistoryItem(BaseModel):
    id: int
    report_date: date
    report_type: str
    drift_share: Optional[float]
    prediction_drift_detected: bool
    model_perf_f1: Optional[float]
    alert_level: AlertSeverity
    created_at: Optional[datetime]


class ManualRetrainRequest(BaseModel):
    reason: str = "Manual trigger via API"


class ManualRetrainResponse(BaseModel):
    triggered: bool
    reasons: list[str]
    metrics: dict[str, Any]
    workflow: Optional[dict[str, Any]]
    log_id: Optional[int]
    old_model_version: Optional[str] = None
    new_model_version: Optional[str] = None
    new_f1: Optional[float] = None
    promoted: Optional[bool] = None
    notes: Optional[str] = None


class RetrainHistoryItem(BaseModel):
    id: int
    triggered_at: datetime
    trigger_reason: str
    old_model_version: Optional[str]
    new_model_version: Optional[str]
    new_f1: Optional[float]
    promoted: bool
    notes: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
