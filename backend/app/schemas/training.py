"""
Pydantic schemas for the Training Lab API.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class ExperimentRun(BaseModel):
    run_id:          str
    run_name:        str
    model_name:      str
    status:          str
    start_time:      Optional[str]
    end_time:        Optional[str]
    duration_s:      Optional[float]
    dataset_version: Optional[int]
    train_size:      Optional[int]
    test_size:       Optional[int]
    accuracy:        Optional[float]
    precision_macro: Optional[float]
    recall_macro:    Optional[float]
    f1_macro:        Optional[float]
    roc_auc:         Optional[float]


class ConfusionMatrix(BaseModel):
    matrix: list[list[int]]
    labels: list[str]


class ClassificationReport(BaseModel):
    data: dict[str, Any]


class RunDetails(BaseModel):
    run_id:               str
    run_name:             str
    model_name:           str
    status:               str
    start_time:           Optional[str]
    end_time:             Optional[str]
    duration_s:           Optional[float]
    params:               dict[str, Any]
    metrics:              dict[str, float]
    confusion_matrix:     Optional[ConfusionMatrix]
    classification_report: Optional[dict[str, Any]]
    dataset_version:      Optional[int]
    train_size:           Optional[int]
    test_size:            Optional[int]


class FeatureImportanceItem(BaseModel):
    feature: str
    score:   float


class FeatureImportances(BaseModel):
    run_id:      str
    model_name:  str
    importances: list[FeatureImportanceItem]


class RegisteredModel(BaseModel):
    name:             str
    latest_version:   Optional[str]
    stage:            Optional[str]
    best_model_name:  Optional[str]
    description:      Optional[str]
    creation_time:    Optional[str]
    last_updated_time: Optional[str]


class ModelVersion(BaseModel):
    version:       str
    stage:         str
    run_id:        Optional[str]
    creation_time: Optional[str]
    description:   Optional[str]
    status:        Optional[str]


class StartTrainingRequest(BaseModel):
    dataset_version: int = 1
    model_list:      Optional[list[str]] = None
    run_name:        str = "training_run"
    n_optuna_trials: int = 10


class TrainingJobStatus(BaseModel):
    job_id:    str
    status:    str          # "running" | "complete" | "failed"
    message:   str
    result:    Optional[dict[str, Any]] = None
    error:     Optional[str] = None


class StartTrainingResponse(BaseModel):
    job_id:  str
    message: str
