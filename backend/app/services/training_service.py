"""
Training service — wraps MLflow client queries and background job management.
"""
from __future__ import annotations

import logging
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Monorepo import ────────────────────────────────────────────────────────────
_PROJECT_ROOT = str(Path(__file__).parents[3])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ── In-memory job store ────────────────────────────────────────────────────────
_jobs: dict[str, dict[str, Any]] = {}

# ── MLflow paths (must agree with ml/training/mlflow_logger.py) ───────────────
_ML_DIR    = Path(__file__).parents[3] / "ml"
_MLFLOW_DB = _ML_DIR / "artifacts" / "mlflow.db"

EXPERIMENT_NAME       = "algotrade-sentinel-signals"
REGISTERED_MODEL_NAME = "signal-predictor"


def _mlflow_uri() -> str:
    path = str(_MLFLOW_DB).replace("\\", "/")
    return f"sqlite:///{path}"


def _get_mlflow_client():
    import mlflow
    from mlflow.tracking import MlflowClient
    mlflow.set_tracking_uri(_mlflow_uri())
    return MlflowClient(_mlflow_uri())


def _ms_to_iso(ts_ms: Optional[int]) -> Optional[str]:
    if ts_ms is None:
        return None
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Background training job
# ---------------------------------------------------------------------------

def start_training_job(
    dataset_version: int,
    model_list:      Optional[list[str]],
    run_name:        str,
    n_optuna_trials: int,
) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "message": "Training started…", "result": None, "error": None}

    def _run():
        try:
            from ml.training.trainer import train_all_models
            result = train_all_models(
                dataset_version=dataset_version,
                model_list=model_list,
                run_name=run_name,
                n_optuna_trials=n_optuna_trials,
            )
            _jobs[job_id].update({
                "status":  "complete",
                "message": f"Training complete — best: {result.get('best_model')} F1={result.get('best_f1', 0):.4f}",
                "result":  result,
            })
        except Exception as exc:
            logger.exception("Training job %s failed", job_id)
            _jobs[job_id].update({"status": "failed", "message": "Training failed", "error": str(exc)})

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return job_id


def get_job_status(job_id: str) -> Optional[dict[str, Any]]:
    return _jobs.get(job_id)


# ---------------------------------------------------------------------------
# Experiment queries
# ---------------------------------------------------------------------------

def list_experiment_runs(limit: int = 100) -> list[dict]:
    try:
        client = _get_mlflow_client()
        exp = client.get_experiment_by_name(EXPERIMENT_NAME)
        if exp is None:
            return []
        runs = client.search_runs(
            experiment_ids=[exp.experiment_id],
            order_by=["start_time DESC"],
            max_results=limit,
        )
        result = []
        for r in runs:
            m = r.data.metrics
            p = r.data.params
            start_ms = r.info.start_time
            end_ms   = r.info.end_time
            dur = (end_ms - start_ms) / 1000.0 if (end_ms and start_ms) else None
            result.append({
                "run_id":          r.info.run_id,
                "run_name":        r.info.run_name or "",
                "model_name":      p.get("model_name", ""),
                "status":          r.info.status,
                "start_time":      _ms_to_iso(start_ms),
                "end_time":        _ms_to_iso(end_ms),
                "duration_s":      round(dur, 1) if dur else None,
                "dataset_version": _int(p.get("dataset_version")),
                "train_size":      _int(p.get("train_size")),
                "test_size":       _int(p.get("test_size")),
                "accuracy":        m.get("accuracy"),
                "precision_macro": m.get("precision_macro"),
                "recall_macro":    m.get("recall_macro"),
                "f1_macro":        m.get("f1_macro"),
                "roc_auc":         m.get("roc_auc"),
            })
        return result
    except Exception as exc:
        logger.warning("list_experiment_runs failed: %s", exc)
        return []


def get_run_details(run_id: str) -> Optional[dict]:
    try:
        client = _get_mlflow_client()
        r = client.get_run(run_id)
        m = r.data.metrics
        p = r.data.params

        start_ms = r.info.start_time
        end_ms   = r.info.end_time
        dur = (end_ms - start_ms) / 1000.0 if (end_ms and start_ms) else None

        # Reconstruct confusion matrix from metrics
        label_names = ["BUY", "HOLD", "SELL"]
        cm_data = _extract_cm(m, label_names)

        # Classification report from metrics
        report = _extract_report(m, label_names)

        return {
            "run_id":               r.info.run_id,
            "run_name":             r.info.run_name or "",
            "model_name":           p.get("model_name", ""),
            "status":               r.info.status,
            "start_time":           _ms_to_iso(start_ms),
            "end_time":             _ms_to_iso(end_ms),
            "duration_s":           round(dur, 1) if dur else None,
            "params":               dict(p),
            "metrics":              {k: float(v) for k, v in m.items()},
            "confusion_matrix":     cm_data,
            "classification_report": report,
            "dataset_version":      _int(p.get("dataset_version")),
            "train_size":           _int(p.get("train_size")),
            "test_size":            _int(p.get("test_size")),
        }
    except Exception as exc:
        logger.warning("get_run_details(%s) failed: %s", run_id, exc)
        return None


def get_best_run() -> Optional[dict]:
    runs = list_experiment_runs(limit=200)
    if not runs:
        return None
    finished = [r for r in runs if r.get("f1_macro") is not None]
    if not finished:
        return None
    return max(finished, key=lambda r: r["f1_macro"])


def get_feature_importances(run_id: str) -> Optional[dict]:
    try:
        client = _get_mlflow_client()
        r = client.get_run(run_id)
        m = r.data.metrics
        p = r.data.params
        fi_items = [
            {"feature": k[3:], "score": float(v)}
            for k, v in m.items()
            if k.startswith("fi_")
        ]
        fi_items.sort(key=lambda x: x["score"], reverse=True)
        return {
            "run_id":      run_id,
            "model_name":  p.get("model_name", ""),
            "importances": fi_items,
        }
    except Exception as exc:
        logger.warning("get_feature_importances(%s) failed: %s", run_id, exc)
        return None


# ---------------------------------------------------------------------------
# Model Registry queries
# ---------------------------------------------------------------------------

def get_registered_models() -> list[dict]:
    try:
        client = _get_mlflow_client()
        models = client.search_registered_models()
        result = []
        for rm in models:
            latest = rm.latest_versions[0] if rm.latest_versions else None
            result.append({
                "name":              rm.name,
                "latest_version":    latest.version if latest else None,
                "stage":             latest.current_stage if latest else None,
                "best_model_name":   rm.tags.get("best_model"),
                "description":       rm.description,
                "creation_time":     _ms_to_iso(rm.creation_timestamp),
                "last_updated_time": _ms_to_iso(rm.last_updated_timestamp),
            })
        return result
    except Exception as exc:
        logger.warning("get_registered_models failed: %s", exc)
        return []


def get_model_versions(model_name: str) -> list[dict]:
    try:
        client = _get_mlflow_client()
        versions = client.search_model_versions(f"name='{model_name}'")
        result = []
        for v in versions:
            result.append({
                "version":       v.version,
                "stage":         v.current_stage,
                "run_id":        v.run_id,
                "creation_time": _ms_to_iso(v.creation_timestamp),
                "description":   v.description,
                "status":        v.status,
            })
        result.sort(key=lambda x: int(x["version"]), reverse=True)
        return result
    except Exception as exc:
        logger.warning("get_model_versions(%s) failed: %s", model_name, exc)
        return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _int(val) -> Optional[int]:
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _extract_cm(metrics: dict, label_names: list[str]) -> Optional[dict]:
    matrix = []
    for true_lbl in label_names:
        row = []
        for pred_lbl in label_names:
            key = f"cm_{true_lbl}_{pred_lbl}"
            row.append(int(metrics.get(key, 0)))
        matrix.append(row)
    if all(v == 0 for row in matrix for v in row):
        return None
    return {"matrix": matrix, "labels": label_names}


def _extract_report(metrics: dict, label_names: list[str]) -> Optional[dict]:
    report: dict = {}
    for cls in label_names:
        entry: dict = {}
        for metric in ("precision", "recall", "f1_score"):
            key = f"report_{cls}_{metric}"
            if key in metrics:
                entry[metric.replace("_score", "-score")] = round(float(metrics[key]), 4)
        if entry:
            report[cls] = entry
    return report if report else None
