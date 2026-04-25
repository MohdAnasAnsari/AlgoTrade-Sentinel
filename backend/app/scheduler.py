from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Callable

from app.config import settings

logger = logging.getLogger("algotrade.scheduler")

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

    HAS_APSCHEDULER = True
except Exception:  # pragma: no cover - optional dependency fallback
    AsyncIOScheduler = Any  # type: ignore[assignment]
    CronTrigger = Any  # type: ignore[assignment]
    HAS_APSCHEDULER = False

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_scheduler: AsyncIOScheduler | None = None
_lock = Lock()
_job_state: dict[str, dict[str, Any]] = {}


def prefect_available() -> bool:
    try:
        import prefect  # noqa: F401
    except Exception:
        return False
    return True


def scheduler_should_run() -> bool:
    return HAS_APSCHEDULER and (settings.apscheduler_enabled or not prefect_available())


def start_scheduler() -> AsyncIOScheduler | None:
    global _scheduler
    if not HAS_APSCHEDULER:
        logger.warning("APScheduler is not installed; scheduled jobs are disabled")
        return None
    if not scheduler_should_run():
        logger.info("APScheduler startup skipped because Prefect is available and fallback is disabled")
        return None

    with _lock:
        if _scheduler is not None and _scheduler.running:
            return _scheduler

        scheduler = AsyncIOScheduler(timezone="UTC")
        _register_jobs(scheduler)
        scheduler.start()
        _scheduler = scheduler
        logger.info("APScheduler started with %d jobs", len(scheduler.get_jobs()))
        return scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    with _lock:
        if _scheduler is not None:
            _scheduler.shutdown(wait=False)
            _scheduler = None
            logger.info("APScheduler stopped")


def get_scheduler_state() -> dict[str, Any]:
    return {
        "enabled": scheduler_should_run(),
        "apscheduler_available": HAS_APSCHEDULER,
        "running": bool(_scheduler and _scheduler.running),
        "prefect_available": prefect_available(),
        "jobs": _job_state,
    }


def _register_jobs(scheduler: AsyncIOScheduler) -> None:
    jobs = [
        ("daily_ingest", settings.INGEST_CRON, _run_ingest_flow),
        ("daily_features", settings.FEATURE_CRON, _run_feature_flow),
        ("daily_inference", settings.INFERENCE_CRON, _run_inference_flow),
        ("daily_monitoring", settings.MONITORING_CRON, _run_monitoring_flow),
    ]
    for job_id, cron_expr, func in jobs:
        scheduler.add_job(
            _job_wrapper,
            CronTrigger.from_crontab(cron_expr, timezone="UTC"),
            id=job_id,
            args=[job_id, func],
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        _job_state.setdefault(
            job_id,
            {
                "cron": cron_expr,
                "last_started_at": None,
                "last_finished_at": None,
                "last_status": "scheduled",
                "last_error": None,
                "last_result": None,
            },
        )


def _job_wrapper(job_id: str, func: Callable[[], Any]) -> Any:
    started_at = datetime.now(timezone.utc).isoformat()
    _job_state.setdefault(job_id, {})
    _job_state[job_id]["last_started_at"] = started_at
    _job_state[job_id]["last_status"] = "running"
    _job_state[job_id]["last_error"] = None
    try:
        result = func()
        _job_state[job_id]["last_status"] = "ok"
        _job_state[job_id]["last_result"] = _summarize_result(result)
        return result
    except Exception as exc:
        logger.exception("Scheduled job %s failed", job_id)
        _job_state[job_id]["last_status"] = "failed"
        _job_state[job_id]["last_error"] = str(exc)
        raise
    finally:
        _job_state[job_id]["last_finished_at"] = datetime.now(timezone.utc).isoformat()


def _summarize_result(result: Any) -> Any:
    if isinstance(result, dict):
        return {key: value for key, value in result.items() if key not in {"details", "feature_details"}}
    return result


def _run_ingest_flow() -> Any:
    from mlops.flows.ingest_flow import market_data_ingest_flow

    return market_data_ingest_flow(only_stale=True)


def _run_feature_flow() -> Any:
    from mlops.flows.feature_flow import feature_engineering_pipeline

    return feature_engineering_pipeline()


def _run_inference_flow() -> Any:
    from mlops.flows.inference_flow import daily_inference_flow

    return daily_inference_flow()


def _run_monitoring_flow() -> Any:
    from mlops.flows.monitoring_flow import daily_monitoring_flow

    return daily_monitoring_flow()
