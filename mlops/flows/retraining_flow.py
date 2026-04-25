"""Prefect wrapper for the automated retraining workflow."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from prefect import flow, task
    from prefect.logging import get_run_logger
    HAS_PREFECT = True
except ImportError:
    HAS_PREFECT = False

    def flow(fn=None, **kw):
        return fn if fn else (lambda f: f)

    def task(fn=None, **kw):
        return fn if fn else (lambda f: f)

    def get_run_logger():
        return logging.getLogger("retraining_flow")


@task(name="execute-retraining")
def execute_retraining_task(trigger_reasons: list[str] | None = None) -> dict:
    from ml.monitoring.retrain_trigger import execute_retraining_workflow

    return execute_retraining_workflow(trigger_reasons or ["Triggered by monitoring flow"])


@flow(name="automated-retraining-pipeline")
def automated_retraining_flow(trigger_reasons: list[str] | None = None) -> dict:
    log = get_run_logger() if HAS_PREFECT else logger
    log.info("Starting automated retraining workflow")
    result = execute_retraining_task(trigger_reasons)
    log.info(
        "Retraining complete | promoted=%s | new_model_version=%s | new_f1=%s",
        result.get("promoted"),
        result.get("new_model_version"),
        result.get("new_f1"),
    )
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(automated_retraining_flow())
