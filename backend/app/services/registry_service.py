"""
Registry service — wraps ml.registry.registry_manager and writes audit log to DB.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_PROJECT_ROOT = str(Path(__file__).parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def list_registered_models() -> list[dict]:
    from ml.registry.registry_manager import list_registered_models as _list
    return _list()


def list_model_versions(model_name: str) -> list[dict]:
    from ml.registry.registry_manager import list_model_versions as _list
    return _list(model_name)


def get_champion(model_name: str) -> Optional[dict]:
    from ml.registry.registry_manager import get_champion as _get
    return _get(model_name)


def get_challengers(model_name: str) -> list[dict]:
    from ml.registry.registry_manager import get_challengers as _get
    return _get(model_name)


def compare_champion_challenger(model_name: str) -> dict:
    from ml.registry.registry_manager import compare_champion_challenger as _cmp
    return _cmp(model_name)


def promote_to_production(
    model_name: str,
    version: str,
    notes: str,
    promoted_by: str,
    db,
) -> dict:
    from ml.registry.registry_manager import promote_to_production as _promote
    from ml.registry.registry_manager import _get_run_metrics
    from ml.training.mlflow_logger import get_default_uri, REGISTERED_MODEL_NAME

    result = _promote(model_name, version, notes, promoted_by)

    # Audit log
    new_champ = result.get("new_champion") or {}
    run_id    = new_champ.get("run_id")
    run_metrics = _get_run_metrics(run_id) if run_id else {}

    _write_log(
        db=db,
        model_name=model_name,
        version=version,
        stage="Production",
        f1_score=run_metrics.get("f1_macro"),
        promoted_by=promoted_by,
        notes=notes,
        mlflow_run_id=run_id,
    )
    return result


def archive_version(model_name: str, version: str, db) -> dict:
    from ml.registry.registry_manager import archive_version as _archive

    result = _archive(model_name, version)
    _write_log(
        db=db,
        model_name=model_name,
        version=version,
        stage="Archived",
        promoted_by="user",
    )
    return result


def check_auto_promote(model_name: str, db) -> dict:
    from ml.registry.registry_manager import check_auto_promote as _auto

    result = _auto(model_name)
    if result:
        new_champ  = result.get("new_champion") or {}
        run_id     = new_champ.get("run_id")
        notes      = new_champ.get("description") or "Auto-promoted"
        _write_log(
            db=db,
            model_name=model_name,
            version=new_champ.get("version", ""),
            stage="Production",
            f1_score=new_champ.get("f1_macro"),
            promoted_by="auto",
            notes=notes,
            mlflow_run_id=run_id,
        )
        return {"promoted": True, "old_champion": result["old_champion"],
                "new_champion": result["new_champion"], "message": notes}
    return {"promoted": False, "old_champion": None, "new_champion": None,
            "message": "No auto-promotion triggered"}


def get_registry_log(db, limit: int = 50) -> list:
    from app.models.signals import ModelRegistryLog
    rows = (
        db.query(ModelRegistryLog)
        .order_by(ModelRegistryLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return rows


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _write_log(
    db,
    model_name: str,
    version: str,
    stage: str,
    f1_score: Optional[float] = None,
    promoted_by: str = "user",
    notes: str = "",
    mlflow_run_id: Optional[str] = None,
) -> None:
    from app.models.signals import ModelRegistryLog
    try:
        entry = ModelRegistryLog(
            model_name=model_name,
            version=str(version),
            stage=stage,
            f1_score=float(f1_score) if f1_score is not None else None,
            promoted_at=datetime.utcnow(),
            promoted_by=promoted_by,
            notes=notes or None,
            mlflow_run_id=mlflow_run_id,
        )
        db.add(entry)
        db.commit()
    except Exception as exc:
        logger.error("Failed to write registry audit log: %s", exc)
        db.rollback()
