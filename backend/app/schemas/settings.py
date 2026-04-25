from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ModelSettings(BaseModel):
    signal_threshold: float
    confidence_filter: float
    position_sizing_pct: float


class BacktestDefaults(BaseModel):
    initial_capital: float
    transaction_cost: float
    slippage: float


class RetrainSettings(BaseModel):
    auto_retrain_enabled: bool
    drift_threshold: float
    performance_threshold: float


class PortfolioEngineSettings(BaseModel):
    initial_cash: float
    max_positions: int
    transaction_cost: float


class EnvironmentStatus(BaseModel):
    database_ok: bool
    mlflow_ok: bool
    scheduler_running: bool
    prefect_available: bool
    last_pipeline_runs: dict


class SystemInfo(BaseModel):
    app_version: str
    python_version: str
    model_version: str | None
    dataset_version: int | None


class AppSettingsResponse(BaseModel):
    model: ModelSettings
    backtest: BacktestDefaults
    retrain: RetrainSettings
    portfolio: PortfolioEngineSettings
    environment: EnvironmentStatus
    system: SystemInfo


class UpdateSettingsRequest(BaseModel):
    model: Optional[ModelSettings] = None
    backtest: Optional[BacktestDefaults] = None
    retrain: Optional[RetrainSettings] = None
    portfolio: Optional[PortfolioEngineSettings] = None
