"""
Training Lab API router.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.response import ok
from app.schemas.training import (
    ExperimentRun,
    FeatureImportances,
    ModelVersion,
    RegisteredModel,
    RunDetails,
    StartTrainingRequest,
    StartTrainingResponse,
    TrainingJobStatus,
)
from app.services import training_service as svc

router = APIRouter(tags=["training"])


# ---------------------------------------------------------------------------
# Training jobs
# ---------------------------------------------------------------------------

@router.post("/api/training/run")
def start_training(body: StartTrainingRequest) -> dict:
    """Trigger a background training job."""
    job_id = svc.start_training_job(
        dataset_version=body.dataset_version,
        model_list=body.model_list,
        run_name=body.run_name,
        n_optuna_trials=body.n_optuna_trials,
    )
    return ok(StartTrainingResponse(job_id=job_id, message="Training started in background"))


@router.get("/api/training/status/{job_id}")
def get_training_status(job_id: str) -> dict:
    """Poll training job status."""
    job = svc.get_job_status(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return ok(TrainingJobStatus(
        job_id=job_id,
        status=job["status"],
        message=job["message"],
        result=job.get("result"),
        error=job.get("error"),
    ))


# ---------------------------------------------------------------------------
# Experiment queries
# ---------------------------------------------------------------------------

@router.get("/api/experiments/list")
def list_experiments(limit: int = Query(100, ge=1, le=500)) -> dict:
    """Return all MLflow experiment runs, most recent first."""
    runs = svc.list_experiment_runs(limit=limit)
    return ok([ExperimentRun(**r) for r in runs])


@router.get("/api/experiments/best")
def best_experiment() -> dict:
    """Return the run with the highest F1 score."""
    run = svc.get_best_run()
    if run is None:
        return ok(None)
    return ok(ExperimentRun(**run))


@router.get("/api/experiments/{run_id}")
def get_experiment(run_id: str) -> dict:
    """Return full details for a specific run."""
    details = svc.get_run_details(run_id)
    if details is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return ok(RunDetails(**details))


# ---------------------------------------------------------------------------
# Model Registry
# ---------------------------------------------------------------------------

@router.get("/api/models/registry")
def list_registry() -> dict:
    """Return all registered models."""
    return ok([RegisteredModel(**m) for m in svc.get_registered_models()])


@router.get("/api/models/{model_name}/versions")
def model_versions(model_name: str) -> dict:
    """Return all versions of a registered model."""
    return ok([ModelVersion(**v) for v in svc.get_model_versions(model_name)])


@router.get("/api/models/{run_id}/importance")
def feature_importance(run_id: str) -> dict:
    """Return top-20 feature importances logged for a run."""
    fi = svc.get_feature_importances(run_id)
    if fi is None:
        raise HTTPException(status_code=404, detail=f"Feature importances not found for run {run_id}")
    return ok(FeatureImportances(**fi))
