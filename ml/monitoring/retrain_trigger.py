"""Retraining trigger logic and workflow orchestration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import text

from ml.data_pipeline.database import SessionLocal
from ml.monitoring.drift_detector import (
    MonitoringConfig,
    generate_and_save_monitoring_report,
    get_latest_saved_report,
)
from ml.registry import registry_manager

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RetrainConfig:
    drift_share_trigger_pct: float = 30.0
    performance_drop_trigger_pct: float = 10.0
    days_since_training_trigger: int = 30
    promotion_f1_delta: float = 0.01
    n_optuna_trials: int = 20


def evaluate_retrain_conditions(
    report: dict[str, Any] | None = None,
    report_date: date | None = None,
    manual_trigger: bool = False,
    manual_reason: str | None = None,
    config: RetrainConfig | None = None,
) -> dict[str, Any]:
    """Evaluate whether retraining should run and why."""
    cfg = config or RetrainConfig()
    report_date = report_date or date.today()
    report = report or get_latest_saved_report()

    reasons: list[str] = []
    metrics = {
        "drift_share": None,
        "performance_drop_pct": None,
        "days_since_last_training": None,
        "last_training_at": None,
    }

    if manual_trigger:
        reasons.append(manual_reason or "Manual trigger via API")

    if report:
        drift_share = float(report.get("drift_share") or 0.0)
        metrics["drift_share"] = drift_share
        if drift_share > cfg.drift_share_trigger_pct:
            reasons.append(f"Drift share {drift_share:.2f}% exceeded {cfg.drift_share_trigger_pct:.2f}% threshold")

        performance = report.get("details", {}).get("performance", {})
        degradation_pct = performance.get("degradation_pct")
        metrics["performance_drop_pct"] = degradation_pct
        if degradation_pct is not None and degradation_pct > cfg.performance_drop_trigger_pct:
            reasons.append(
                f"Model F1 dropped {degradation_pct:.2f}% from baseline, above {cfg.performance_drop_trigger_pct:.2f}%"
            )
        metrics["last_training_at"] = performance.get("last_training_at")

    last_training_at = metrics["last_training_at"] or _latest_training_timestamp()
    metrics["last_training_at"] = last_training_at

    if last_training_at:
        last_training_date = datetime.fromisoformat(last_training_at.replace("Z", "+00:00")).date()
        days_since = (report_date - last_training_date).days
        metrics["days_since_last_training"] = days_since
        if days_since >= cfg.days_since_training_trigger:
            reasons.append(
                f"{days_since} day(s) elapsed since last training, above {cfg.days_since_training_trigger} day threshold"
            )
    else:
        reasons.append("No prior training history found")

    return {
        "triggered": bool(reasons),
        "reasons": reasons,
        "metrics": metrics,
    }


def maybe_trigger_retraining(
    report: dict[str, Any] | None = None,
    manual_trigger: bool = False,
    manual_reason: str | None = None,
    monitoring_config: MonitoringConfig | None = None,
    retrain_config: RetrainConfig | None = None,
) -> dict[str, Any]:
    """Evaluate triggers and run the retraining workflow when needed."""
    report = report or get_latest_saved_report()
    if report is None:
        report = generate_and_save_monitoring_report(report_type="bootstrap", config=monitoring_config)

    decision = evaluate_retrain_conditions(
        report=report,
        manual_trigger=manual_trigger,
        manual_reason=manual_reason,
        config=retrain_config,
    )
    if not decision["triggered"]:
        logger.info("Retraining not triggered")
        return {
            "triggered": False,
            "reasons": [],
            "metrics": decision["metrics"],
            "workflow": None,
            "log_id": None,
        }

    workflow = execute_retraining_workflow(
        trigger_reasons=decision["reasons"],
        config=retrain_config,
    )
    workflow["triggered"] = True
    workflow["reasons"] = decision["reasons"]
    workflow["metrics"] = decision["metrics"]
    return workflow


def execute_retraining_workflow(
    trigger_reasons: list[str],
    config: RetrainConfig | None = None,
) -> dict[str, Any]:
    """Run feature -> training -> promotion -> inference and audit the result."""
    cfg = config or RetrainConfig()
    triggered_at = _utcnow_naive()
    old_champion = registry_manager.get_champion()

    new_model_version = None
    new_f1 = None
    promoted = False
    log_id = None
    notes = ""

    try:
        from mlops.flows.feature_flow import feature_engineering_pipeline
        from mlops.flows.inference_flow import daily_inference_flow
        from mlops.flows.training_flow import model_training_pipeline

        logger.info("Starting retraining workflow because: %s", "; ".join(trigger_reasons))
        feature_engineering_pipeline()
        dataset_version = _latest_dataset_version()

        training_result = model_training_pipeline(
            dataset_version=dataset_version,
            run_name=f"retrain_{triggered_at.strftime('%Y%m%d_%H%M%S')}",
            n_optuna_trials=cfg.n_optuna_trials,
        )
        new_f1 = training_result.get("best_f1")
        best_run_id = training_result.get("best_run_id")
        new_model_version = _model_version_for_run(best_run_id)

        promotion_result = registry_manager.check_auto_promote(f1_delta=cfg.promotion_f1_delta)
        promoted = bool(promotion_result.get("promoted"))

        inference_result = daily_inference_flow()
        notes = (
            f"Reasons: {'; '.join(trigger_reasons)} | "
            f"Dataset v{dataset_version} | "
            f"Best F1={new_f1} | "
            f"Model version={new_model_version} | "
            f"{promotion_result.get('message')} | "
            f"Inference status={inference_result.get('status')} rows={inference_result.get('rows_stored')}"
        )

        log_id = _write_retrain_log(
            triggered_at=triggered_at,
            trigger_reason="; ".join(trigger_reasons),
            old_model_version=old_champion.get("version") if old_champion else None,
            new_model_version=new_model_version,
            new_f1=new_f1,
            promoted=promoted,
            notes=notes,
        )

        return {
            "workflow": {
                "dataset_version": dataset_version,
                "training_result": training_result,
                "promotion_result": promotion_result,
                "inference_result": inference_result,
            },
            "log_id": log_id,
            "old_model_version": old_champion.get("version") if old_champion else None,
            "new_model_version": new_model_version,
            "new_f1": new_f1,
            "promoted": promoted,
            "notes": notes,
        }
    except Exception as exc:
        logger.exception("Retraining workflow failed")
        notes = f"FAILED: {exc} | Reasons: {'; '.join(trigger_reasons)}"
        log_id = _write_retrain_log(
            triggered_at=triggered_at,
            trigger_reason="; ".join(trigger_reasons),
            old_model_version=old_champion.get("version") if old_champion else None,
            new_model_version=new_model_version,
            new_f1=new_f1,
            promoted=False,
            notes=notes,
        )
        raise


def _write_retrain_log(
    triggered_at: datetime,
    trigger_reason: str,
    old_model_version: str | None,
    new_model_version: str | None,
    new_f1: float | None,
    promoted: bool,
    notes: str,
) -> int:
    with SessionLocal() as session:
        result = session.execute(
            text(
                """
                INSERT INTO retrain_log (
                    triggered_at,
                    trigger_reason,
                    old_model_version,
                    new_model_version,
                    new_f1,
                    promoted,
                    notes
                )
                VALUES (
                    :triggered_at,
                    :trigger_reason,
                    :old_model_version,
                    :new_model_version,
                    :new_f1,
                    :promoted,
                    :notes
                )
                """
            ),
            {
                "triggered_at": triggered_at,
                "trigger_reason": trigger_reason,
                "old_model_version": old_model_version,
                "new_model_version": new_model_version,
                "new_f1": new_f1,
                "promoted": int(promoted),
                "notes": notes,
            },
        )
        session.commit()
        return int(result.lastrowid)


def _latest_dataset_version() -> int:
    with SessionLocal() as session:
        version = session.execute(text("SELECT MAX(version) FROM dataset_versions")).scalar()
    if version is None:
        raise RuntimeError("No dataset versions available for retraining")
    return int(version)


def _model_version_for_run(run_id: str | None) -> str | None:
    if run_id is None:
        return None
    versions = registry_manager.list_model_versions()
    for version in versions:
        if version.get("run_id") == run_id:
            return str(version.get("version"))
    return None


def _latest_training_timestamp() -> str | None:
    try:
        import mlflow
        from mlflow.tracking import MlflowClient

        from ml.training.mlflow_logger import EXPERIMENT_NAME, get_default_uri

        mlflow.set_tracking_uri(get_default_uri())
        client = MlflowClient()
        experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
        if experiment is None:
            return None
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=1,
        )
        if not runs:
            return None
        timestamp_ms = runs[0].info.start_time
        return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat()
    except Exception:
        return None


def _utcnow_naive() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None)
