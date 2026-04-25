"""
MLflow Model Registry manager for AlgoTrade Sentinel.

Provides champion/challenger lifecycle management for the 'signal-predictor' model.
Champion = Production stage. Challengers = Staging stage.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ml.training.mlflow_logger import get_default_uri, REGISTERED_MODEL_NAME  # noqa: E402

AUTO_PROMOTE_F1_DELTA = 0.01  # challenger must beat champion by this margin


def _client():
    import mlflow
    from mlflow.tracking import MlflowClient
    mlflow.set_tracking_uri(get_default_uri())
    return MlflowClient()


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def list_registered_models() -> list[dict]:
    """Return all registered models with their latest version info."""
    client = _client()
    models = []
    for rm in client.search_registered_models():
        latest = rm.latest_versions[0] if rm.latest_versions else None
        models.append({
            "name":              rm.name,
            "latest_version":    latest.version if latest else None,
            "stage":             latest.current_stage if latest else None,
            "description":       rm.description,
            "creation_time":     rm.creation_timestamp,
            "last_updated_time": rm.last_updated_timestamp,
            "tags":              dict(rm.tags) if rm.tags else {},
        })
    return models


def list_model_versions(model_name: str = REGISTERED_MODEL_NAME) -> list[dict]:
    """Return all versions of a registered model, newest first."""
    client = _client()
    versions = client.search_model_versions(f"name='{model_name}'")
    result = []
    for mv in sorted(versions, key=lambda v: int(v.version), reverse=True):
        run_metrics = _get_run_metrics(mv.run_id) if mv.run_id else {}
        result.append({
            "version":       mv.version,
            "stage":         mv.current_stage,
            "run_id":        mv.run_id,
            "creation_time": mv.creation_timestamp,
            "description":   mv.description,
            "status":        mv.status,
            "f1_macro":      run_metrics.get("f1_macro"),
            "accuracy":      run_metrics.get("accuracy"),
            "roc_auc":       run_metrics.get("roc_auc"),
            "model_name":    _get_run_param(mv.run_id, "model_name") if mv.run_id else None,
        })
    return result


def get_champion(model_name: str = REGISTERED_MODEL_NAME) -> Optional[dict]:
    """Return the current Production (champion) model version, or None."""
    client = _client()
    versions = client.get_latest_versions(model_name, stages=["Production"])
    if not versions:
        return None
    mv = versions[0]
    run_metrics = _get_run_metrics(mv.run_id) if mv.run_id else {}
    return {
        "version":    mv.version,
        "stage":      mv.current_stage,
        "run_id":     mv.run_id,
        "f1_macro":   run_metrics.get("f1_macro"),
        "accuracy":   run_metrics.get("accuracy"),
        "roc_auc":    run_metrics.get("roc_auc"),
        "model_name": _get_run_param(mv.run_id, "model_name") if mv.run_id else None,
        "creation_time": mv.creation_timestamp,
        "description": mv.description,
    }


def get_challengers(model_name: str = REGISTERED_MODEL_NAME) -> list[dict]:
    """Return all Staging (challenger) model versions."""
    client = _client()
    versions = client.get_latest_versions(model_name, stages=["Staging"])
    result = []
    for mv in versions:
        run_metrics = _get_run_metrics(mv.run_id) if mv.run_id else {}
        result.append({
            "version":    mv.version,
            "stage":      mv.current_stage,
            "run_id":     mv.run_id,
            "f1_macro":   run_metrics.get("f1_macro"),
            "accuracy":   run_metrics.get("accuracy"),
            "roc_auc":    run_metrics.get("roc_auc"),
            "model_name": _get_run_param(mv.run_id, "model_name") if mv.run_id else None,
            "creation_time": mv.creation_timestamp,
            "description": mv.description,
        })
    return result


def compare_champion_challenger(model_name: str = REGISTERED_MODEL_NAME) -> dict:
    """Return side-by-side metrics comparison of champion vs challengers."""
    champion    = get_champion(model_name)
    challengers = get_challengers(model_name)
    return {
        "champion":    champion,
        "challengers": challengers,
        "model_name":  model_name,
    }


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

def promote_to_production(
    model_name: str = REGISTERED_MODEL_NAME,
    version: str = "",
    notes: str = "",
    promoted_by: str = "user",
) -> dict:
    """
    Transition version to Production. Archive existing Production version.
    Returns dict with old_champion and new_champion info.
    """
    client = _client()

    old_champion = get_champion(model_name)

    # Archive current Production (if any, and if it's different)
    if old_champion and old_champion["version"] != version:
        client.transition_model_version_stage(
            name=model_name,
            version=old_champion["version"],
            stage="Archived",
        )
        logger.info("Archived champion v%s", old_champion["version"])

    # Promote challenger
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage="Production",
    )
    if notes:
        client.update_model_version(model_name, version, description=notes)

    new_champion = get_champion(model_name)
    logger.info("Promoted v%s to Production for %s", version, model_name)
    return {"old_champion": old_champion, "new_champion": new_champion}


def archive_version(
    model_name: str = REGISTERED_MODEL_NAME,
    version: str = "",
) -> dict:
    """Transition a version to Archived stage."""
    client = _client()
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage="Archived",
    )
    logger.info("Archived v%s of %s", version, model_name)
    return {"model_name": model_name, "version": version, "stage": "Archived"}


def check_auto_promote(
    model_name: str = REGISTERED_MODEL_NAME,
    f1_delta: float = AUTO_PROMOTE_F1_DELTA,
) -> Optional[dict]:
    """
    If a challenger's F1 beats champion F1 by f1_delta, auto-promote it.
    Returns promotion result dict if promoted, else None.
    """
    champion    = get_champion(model_name)
    challengers = get_challengers(model_name)

    if not challengers:
        return None

    champion_f1 = float(champion["f1_macro"] or 0) if champion else 0.0
    threshold   = champion_f1 + f1_delta

    best_challenger = max(
        challengers,
        key=lambda c: float(c["f1_macro"] or 0),
    )
    challenger_f1 = float(best_challenger["f1_macro"] or 0)

    if challenger_f1 > threshold:
        logger.info(
            "Auto-promoting v%s (F1=%.4f) > champion (F1=%.4f) + delta %.3f",
            best_challenger["version"], challenger_f1, champion_f1, f1_delta,
        )
        return promote_to_production(
            model_name=model_name,
            version=best_challenger["version"],
            notes=f"Auto-promoted: F1={challenger_f1:.4f} > {champion_f1:.4f}+{f1_delta}",
            promoted_by="auto",
        )
    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_run_metrics(run_id: str) -> dict:
    try:
        import mlflow
        mlflow.set_tracking_uri(get_default_uri())
        run = mlflow.get_run(run_id)
        return run.data.metrics
    except Exception:
        return {}


def _get_run_param(run_id: str, param: str) -> Optional[str]:
    try:
        import mlflow
        mlflow.set_tracking_uri(get_default_uri())
        run = mlflow.get_run(run_id)
        return run.data.params.get(param)
    except Exception:
        return None
