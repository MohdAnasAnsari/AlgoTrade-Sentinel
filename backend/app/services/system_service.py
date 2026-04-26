from __future__ import annotations

import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import psutil
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.features import FeaturesData
from app.models.market import MarketData
from app.models.monitoring import MonitoringReport, RetrainLog
from app.models.signals import Signal
from app.scheduler import get_scheduler_state

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ARTIFACT_ROOT = _REPO_ROOT / "ml" / "artifacts"
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def get_system_status(db: Session) -> dict[str, Any]:
    scheduler_state = get_scheduler_state()
    artifacts_usage = _artifact_usage(_ARTIFACT_ROOT)

    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": _database_status(db),
        "mlflow": _mlflow_status(),
        "scheduler": scheduler_state,
        "pipeline_runs": _pipeline_run_times(db, scheduler_state),
        "artifacts": artifacts_usage,
        "system": {
            "memory": _memory_usage(),
            "disk": _disk_usage(_REPO_ROOT),
            "server_time": datetime.utcnow().isoformat() + "Z",
        },
    }


def _database_status(db: Session) -> dict[str, Any]:
    try:
        db.query(func.count(MarketData.id)).scalar()
        return {"ok": True, "url": settings.DATABASE_URL.split("@")[-1]}
    except Exception as exc:
        logger.warning("Database connectivity check failed: %s", exc)
        return {"ok": False, "error": str(exc)}


def _mlflow_status() -> dict[str, Any]:
    from ml.training.mlflow_logger import get_default_uri

    uri = get_default_uri()
    if uri.startswith(("http://", "https://")):
        try:
            import httpx

            response = httpx.get(uri, timeout=settings.MLFLOW_STATUS_TIMEOUT_SECONDS, follow_redirects=True)
            return {"ok": response.status_code < 500, "uri": uri, "status_code": response.status_code}
        except Exception as exc:
            return {"ok": False, "uri": uri, "error": str(exc)}

    path = _uri_to_path(uri)
    return {"ok": path.exists(), "uri": uri, "path": str(path)}


def _uri_to_path(uri: str) -> Path:
    if uri.startswith("file:"):
        return Path(uri.removeprefix("file:"))
    if uri.startswith("sqlite:///"):
        parsed = urlparse(uri)
        path_str = parsed.path
        if os.name == "nt" and len(path_str) >= 3 and path_str[0] == "/" and path_str[2] == ":":
            path_str = path_str[1:]
        return Path(path_str)
    return Path(uri)


def _pipeline_run_times(db: Session, scheduler_state: dict[str, Any]) -> dict[str, Any]:
    pipeline_map = {
        "daily_ingest": _latest_market_ingest(db),
        "daily_features": _latest_feature_run(db),
        "daily_inference": _latest_inference_run(db),
        "daily_monitoring": _latest_monitoring_run(db),
        "last_retrain": _latest_retrain_run(db),
    }
    jobs = scheduler_state.get("jobs", {})
    for job_name in ("daily_ingest", "daily_features", "daily_inference", "daily_monitoring"):
        job_state = jobs.get(job_name, {})
        pipeline_map[job_name] = {
            "last_observed_at": pipeline_map[job_name],
            "last_started_at": job_state.get("last_started_at"),
            "last_finished_at": job_state.get("last_finished_at"),
            "last_status": job_state.get("last_status"),
            "last_error": job_state.get("last_error"),
        }
    return pipeline_map


def _latest_market_ingest(db: Session) -> str | None:
    return db.query(func.max(MarketData.created_at)).scalar()


def _latest_feature_run(db: Session) -> str | None:
    return db.query(func.max(FeaturesData.created_at)).scalar()


def _latest_inference_run(db: Session) -> str | None:
    return db.query(func.max(Signal.created_at)).scalar()


def _latest_monitoring_run(db: Session) -> str | None:
    return db.query(func.max(MonitoringReport.created_at)).scalar()


def _latest_retrain_run(db: Session) -> str | None:
    return db.query(func.max(RetrainLog.triggered_at)).scalar()


def _artifact_usage(path: Path) -> dict[str, Any]:
    size_bytes = 0
    if path.exists():
        for file_path in path.rglob("*"):
            if file_path.is_file():
                size_bytes += file_path.stat().st_size
    return {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": size_bytes,
    }


def _memory_usage() -> dict[str, Any]:
    memory = psutil.virtual_memory()
    process = psutil.Process(os.getpid())
    return {
        "system_total_bytes": memory.total,
        "system_available_bytes": memory.available,
        "system_percent": memory.percent,
        "process_rss_bytes": process.memory_info().rss,
    }


def _disk_usage(path: Path) -> dict[str, Any]:
    total, used, free = shutil.disk_usage(path)
    return {"path": str(path), "total_bytes": total, "used_bytes": used, "free_bytes": free}
