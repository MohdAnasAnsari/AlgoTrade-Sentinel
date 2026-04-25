"""
Model Registry router — champion/challenger lifecycle management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.schemas.signals import (
    ArchiveRequest,
    AutoPromoteResult,
    ComparisonResult,
    ModelVersionOut,
    PromoteRequest,
    RegisteredModelOut,
    RegistryLogOut,
)
from app.services import registry_service
from ml.training.mlflow_logger import REGISTERED_MODEL_NAME

router = APIRouter(prefix="/api/registry", tags=["registry"])


@router.get("/models")
def list_models() -> dict:
    """List all registered MLflow models."""
    models = registry_service.list_registered_models()
    return ok([RegisteredModelOut(**m) for m in models])


@router.get("/models/{model_name}/champion")
def get_champion(model_name: str = REGISTERED_MODEL_NAME) -> dict:
    """Return the Production (champion) model version."""
    champion = registry_service.get_champion(model_name)
    if not champion:
        raise HTTPException(404, detail=f"No Production model found for '{model_name}'")
    return ok(ModelVersionOut(**champion))


@router.get("/models/{model_name}/challengers")
def get_challengers(model_name: str = REGISTERED_MODEL_NAME) -> dict:
    """Return all Staging (challenger) model versions."""
    challengers = registry_service.get_challengers(model_name)
    return ok([ModelVersionOut(**c) for c in challengers])


@router.get("/models/{model_name}/versions")
def list_versions(model_name: str = REGISTERED_MODEL_NAME) -> dict:
    """Return all versions of a registered model."""
    versions = registry_service.list_model_versions(model_name)
    return ok([ModelVersionOut(**v) for v in versions])


@router.get("/models/{model_name}/compare")
def compare(model_name: str = REGISTERED_MODEL_NAME) -> dict:
    """Compare champion vs challengers side by side."""
    result = registry_service.compare_champion_challenger(model_name)
    return ok(ComparisonResult(**result))


@router.post("/models/{model_name}/promote")
def promote(
    model_name: str,
    body: PromoteRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Promote a model version to Production; archive current champion."""
    try:
        result = registry_service.promote_to_production(
            model_name=model_name,
            version=body.version,
            notes=body.notes,
            promoted_by=body.promoted_by,
            db=db,
        )
        return ok(result)
    except Exception as exc:
        raise HTTPException(400, detail=str(exc))


@router.post("/models/{model_name}/archive")
def archive(
    model_name: str,
    body: ArchiveRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Archive a model version."""
    try:
        return ok(registry_service.archive_version(model_name, body.version, db))
    except Exception as exc:
        raise HTTPException(400, detail=str(exc))


@router.post("/models/{model_name}/auto-promote")
def auto_promote(model_name: str, db: Session = Depends(get_db)) -> dict:
    """Check if any challenger beats champion by ≥0.01 F1 and auto-promote."""
    result = registry_service.check_auto_promote(model_name, db)
    return ok(AutoPromoteResult(**result))


@router.get("/log")
def registry_log(limit: int = 50, db: Session = Depends(get_db)) -> dict:
    """Return recent model promotion audit log."""
    rows = registry_service.get_registry_log(db, limit=limit)
    return ok([RegistryLogOut.model_validate(r) for r in rows])
