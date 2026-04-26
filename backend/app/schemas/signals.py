from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Signal schemas
# ---------------------------------------------------------------------------

class SignalOut(BaseModel):
    id:            int
    ticker:        str
    signal_date:   date
    signal:        str
    confidence:    Optional[float]
    prob_buy:      Optional[float]
    prob_sell:     Optional[float]
    prob_hold:     Optional[float]
    model_version: Optional[str]
    model_run_id:  Optional[str]
    explanation:   Optional[str]
    created_at:    Optional[datetime]

    class Config:
        from_attributes = True


class LatestSignal(BaseModel):
    ticker:        str
    signal_date:   Optional[date]
    signal:        Optional[str]
    confidence:    Optional[float]
    prob_buy:      Optional[float]
    prob_sell:     Optional[float]
    prob_hold:     Optional[float]
    model_version: Optional[str]
    explanation:   Optional[str]


class SignalHistoryPoint(BaseModel):
    signal_date: date
    signal:      str
    confidence:  Optional[float]
    close:       Optional[float]


class RunInferenceRequest(BaseModel):
    tickers:              Optional[list[str]] = None
    confidence_threshold: float = 0.55
    feature_limit:        int   = 60


class InferenceJobStatus(BaseModel):
    job_id:         str
    status:         str
    message:        str
    total_signals:  Optional[int]   = None
    model_run_id:   Optional[str]   = None
    model_version:  Optional[str]   = None
    error:          Optional[str]   = None


class StartInferenceResponse(BaseModel):
    job_id:  str
    message: str


# ---------------------------------------------------------------------------
# Registry schemas
# ---------------------------------------------------------------------------

class ModelVersionOut(BaseModel):
    version:       str
    stage:         str
    run_id:        Optional[str] = None
    f1_macro:      Optional[float] = None
    accuracy:      Optional[float] = None
    roc_auc:       Optional[float] = None
    model_name:    Optional[str] = None
    creation_time: Optional[int] = None
    description:   Optional[str] = None
    status:        Optional[str] = None


class RegisteredModelOut(BaseModel):
    name:              str
    latest_version:    Optional[str] = None
    stage:             Optional[str] = None
    description:       Optional[str] = None
    creation_time:     Optional[int] = None
    last_updated_time: Optional[int] = None
    tags:              Optional[dict] = None


class PromoteRequest(BaseModel):
    version:     str
    notes:       str  = ""
    promoted_by: str  = "user"


class ArchiveRequest(BaseModel):
    version: str


class AutoPromoteResult(BaseModel):
    promoted: bool
    old_champion: Optional[dict]
    new_champion: Optional[dict]
    message: str


class ComparisonResult(BaseModel):
    model_name:   str
    champion:     Optional[dict]
    challengers:  list[dict]


class RegistryLogOut(BaseModel):
    id:            int
    model_name:    str
    version:       str
    stage:         str
    f1_score:      Optional[float]
    promoted_at:   Optional[datetime]
    promoted_by:   Optional[str]
    notes:         Optional[str]
    mlflow_run_id: Optional[str]
    created_at:    Optional[datetime]

    class Config:
        from_attributes = True
