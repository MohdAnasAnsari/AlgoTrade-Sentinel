"""Prefect flow for daily monitoring, alerting, and retraining decisions."""
from __future__ import annotations

import logging
import sys
from datetime import date
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
        return logging.getLogger("monitoring_flow")


@task(name="generate-monitoring-report")
def monitoring_report_task() -> dict:
    from ml.monitoring.drift_detector import generate_and_save_monitoring_report

    return generate_and_save_monitoring_report(report_date=date.today(), report_type="daily")


@task(name="send-critical-alert")
def send_critical_alert_task(report: dict) -> dict | None:
    alerts = report.get("details", {}).get("alerts", [])
    critical_alerts = [alert for alert in alerts if alert.get("severity") == "CRITICAL"]
    if critical_alerts:
        log = get_run_logger() if HAS_PREFECT else logger
        log.error("Critical monitoring alert(s): %s", critical_alerts)
        return {"sent": True, "alerts": critical_alerts}
    return None


@task(name="evaluate-retraining")
def retraining_task(report: dict) -> dict:
    from ml.monitoring.retrain_trigger import maybe_trigger_retraining

    return maybe_trigger_retraining(report=report)


@flow(name="daily-monitoring-pipeline")
def daily_monitoring_flow() -> dict:
    log = get_run_logger() if HAS_PREFECT else logger
    log.info("Starting daily monitoring flow")

    report = monitoring_report_task()
    critical_alert = send_critical_alert_task(report)
    retraining = retraining_task(report)

    log.info(
        "Monitoring complete | alert_level=%s | drift_share=%s | retraining_triggered=%s",
        report.get("alert_level"),
        report.get("drift_share"),
        retraining.get("triggered"),
    )
    return {
        "report": report,
        "critical_alert": critical_alert,
        "retraining": retraining,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(daily_monitoring_flow())
