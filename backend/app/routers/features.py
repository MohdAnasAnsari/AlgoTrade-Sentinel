from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.response import ok
from app.database import get_db
from app.schemas.features import (
    PipelineRunRequest,
)
from app.services.feature_service import FeatureService

router = APIRouter(tags=["features"])


def _svc(db: Session = Depends(get_db)) -> FeatureService:
    return FeatureService(db)


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------

@router.get("/api/features/list/{ticker}")
def get_feature_list(
    ticker: str,
    limit: int = 30,
    svc: FeatureService = Depends(_svc),
) -> dict:
    return ok(svc.get_feature_list(ticker, limit=limit))


@router.get("/api/features/stats/{ticker}")
def get_feature_stats(
    ticker: str,
    svc: FeatureService = Depends(_svc),
) -> dict:
    return ok(svc.get_feature_stats(ticker))


@router.post("/api/features/run")
def run_feature_pipeline(
    body: PipelineRunRequest = PipelineRunRequest(),
    svc: FeatureService = Depends(_svc),
) -> dict:
    return ok(svc.run_pipeline(
        tickers=body.tickers,
        split_date=body.split_date or "2023-01-01",
        build_ds=body.build_dataset,
    ))


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

@router.get("/api/labels/distribution")
def get_all_label_distributions(svc: FeatureService = Depends(_svc)) -> dict:
    return ok(svc.get_label_distribution())


@router.get("/api/labels/distribution/{ticker}")
def get_label_distribution(
    ticker: str,
    svc: FeatureService = Depends(_svc),
) -> dict:
    result = svc.get_label_distribution(ticker)
    if not result:
        raise HTTPException(status_code=404, detail=f"No labels found for {ticker}")
    return ok(result[0])


# ---------------------------------------------------------------------------
# Dataset versions
# ---------------------------------------------------------------------------

@router.get("/api/dataset/versions")
def get_dataset_versions(svc: FeatureService = Depends(_svc)) -> dict:
    return ok(svc.get_dataset_versions())


@router.get("/api/dataset/{version}/summary")
def get_dataset_summary(
    version: int,
    svc: FeatureService = Depends(_svc),
) -> dict:
    info = svc.get_dataset_summary(version)
    if not info:
        raise HTTPException(status_code=404, detail=f"Dataset version {version} not found")
    return ok(info)
