"""
MLflow logging utilities for AlgoTrade Sentinel training runs.
All runs are logged to experiment "algotrade-sentinel-signals".
Best model is registered under "signal-predictor" in Staging stage.
"""
import json
import logging
import os
import pickle
import platform
import socket
import warnings
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
_ML_DIR       = Path(__file__).parents[1]            # ml/
_ARTIFACTS    = _ML_DIR / "artifacts"
_MLFLOW_DB    = _ARTIFACTS / "mlflow.db"

EXPERIMENT_NAME        = "algotrade-sentinel-signals"
REGISTERED_MODEL_NAME  = "signal-predictor"


@lru_cache(maxsize=1)
def get_default_uri() -> str:
    uri = os.getenv("MLFLOW_TRACKING_URI")
    if uri and _uri_reachable(uri):
        return uri
    path = str(_MLFLOW_DB).replace("\\", "/")
    return f"sqlite:///{path}"


def _uri_reachable(uri: str) -> bool:
    parsed = urlparse(uri)
    if parsed.scheme not in {"http", "https"}:
        return True
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not parsed.hostname:
        return False
    try:
        with socket.create_connection((parsed.hostname, port), timeout=3.0):
            return True
    except OSError:
        logger.warning("MLflow URI %s is unreachable, falling back to local sqlite store", uri)
        return False


def setup_mlflow(tracking_uri: Optional[str] = None) -> None:
    import mlflow
    _ARTIFACTS.mkdir(parents=True, exist_ok=True)
    uri = tracking_uri or get_default_uri()
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(EXPERIMENT_NAME)
    logger.info("MLflow tracking URI: %s", uri)


# ---------------------------------------------------------------------------
# Confusion matrix plot helper
# ---------------------------------------------------------------------------

def _save_cm_plot(cm: np.ndarray, label_names: list[str], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    plt.colorbar(im, ax=ax)
    ax.set(
        xticks=range(len(label_names)),
        yticks=range(len(label_names)),
        xticklabels=label_names,
        yticklabels=label_names,
        xlabel="Predicted",
        ylabel="True",
        title="Confusion Matrix",
    )
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black",
                    fontsize=11, fontweight="bold")
    plt.tight_layout()
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def _save_fi_plot(importances: dict, path: Path, top_n: int = 20) -> None:
    top   = dict(list(importances.items())[:top_n])
    names = list(top.keys())[::-1]
    vals  = list(top.values())[::-1]

    fig, ax = plt.subplots(figsize=(9, 7))
    bars = ax.barh(names, vals, color="#06b6d4")
    ax.set_xlabel("Importance Score")
    ax.set_title(f"Top {min(top_n, len(top))} Feature Importances")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main log function
# ---------------------------------------------------------------------------

def log_training_run(
    run_name:          str,
    model,
    model_name:        str,
    params:            dict,
    metrics:           dict,
    cm:                np.ndarray,
    report:            dict,
    feature_importances: Optional[dict],
    scaler,
    feature_names:     list[str],
    dataset_version:   int,
    train_size:        int,
    test_size:         int,
    label_names:       list[str],
    artifacts_dir:     Path,
) -> str:
    """Log a single training run to MLflow. Returns run_id."""
    import mlflow
    import mlflow.sklearn

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    with mlflow.start_run(run_name=run_name) as run:
        run_id = run.info.run_id

        # ── Tags ────────────────────────────────────────────────────────
        mlflow.set_tags({
            "run_type":    "training",
            "phase":       "4",
            "model_name":  model_name,
        })

        # ── Params ──────────────────────────────────────────────────────
        mlflow.log_param("model_name",      model_name)
        mlflow.log_param("dataset_version", dataset_version)
        mlflow.log_param("train_size",      train_size)
        mlflow.log_param("test_size",       test_size)
        mlflow.log_param("n_features",      len(feature_names))
        mlflow.log_param("label_names",     ",".join(label_names))
        for k, v in list(params.items())[:30]:          # MLflow param limit guard
            mlflow.log_param(k, str(v)[:250])

        # ── Scalar metrics ───────────────────────────────────────────────
        mlflow.log_metrics({k: float(v) for k, v in metrics.items() if v is not None})

        # ── Confusion matrix as metrics (for easy backend reconstruction) ─
        for i, true_lbl in enumerate(label_names):
            for j, pred_lbl in enumerate(label_names):
                val = int(cm[i, j]) if i < cm.shape[0] and j < cm.shape[1] else 0
                mlflow.log_metric(f"cm_{true_lbl}_{pred_lbl}", val)

        # ── Top-20 feature importances as metrics ─────────────────────────
        if feature_importances:
            for feat, score in list(feature_importances.items())[:20]:
                safe_key = f"fi_{feat}"
                mlflow.log_metric(safe_key, float(score))

        # ── Classification report metrics ────────────────────────────────
        for cls in label_names:
            cls_data = report.get(cls, {})
            for metric_key in ("precision", "recall", "f1-score"):
                val = cls_data.get(metric_key)
                if val is not None:
                    mlflow.log_metric(f"report_{cls}_{metric_key.replace('-', '_')}", float(val))

        # ── Artifacts ────────────────────────────────────────────────────
        run_dir = artifacts_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Model (pickle) — save locally always; upload to MLflow artifact store best-effort
        model_pkl = run_dir / "model.pkl"
        with open(model_pkl, "wb") as f:
            pickle.dump(model, f)
        try:
            mlflow.log_artifact(str(model_pkl), "model")
        except Exception as e:
            logger.warning("log_artifact model.pkl failed (non-fatal): %s", e)

        # Scaler
        scaler_pkl = run_dir / "scaler.pkl"
        with open(scaler_pkl, "wb") as f:
            pickle.dump(scaler, f)
        try:
            mlflow.log_artifact(str(scaler_pkl), "scaler")
        except Exception as e:
            logger.warning("log_artifact scaler.pkl failed (non-fatal): %s", e)

        # Feature list
        feat_json = run_dir / "features.json"
        feat_json.write_text(json.dumps(feature_names, indent=2))
        try:
            mlflow.log_artifact(str(feat_json), "features")
        except Exception as e:
            logger.warning("log_artifact features.json failed (non-fatal): %s", e)

        # Confusion matrix JSON + plot
        cm_json = run_dir / "confusion_matrix.json"
        cm_json.write_text(json.dumps({"matrix": cm.tolist(), "labels": label_names}))
        try:
            mlflow.log_artifact(str(cm_json), "confusion_matrix")
        except Exception as e:
            logger.warning("log_artifact confusion_matrix.json failed (non-fatal): %s", e)

        try:
            cm_png = run_dir / "confusion_matrix.png"
            _save_cm_plot(cm, label_names, cm_png)
            mlflow.log_artifact(str(cm_png), "plots")
        except Exception as e:
            logger.warning("CM plot failed: %s", e)

        # Classification report JSON
        report_json = run_dir / "classification_report.json"
        report_json.write_text(json.dumps(report, indent=2))
        try:
            mlflow.log_artifact(str(report_json), "reports")
        except Exception as e:
            logger.warning("log_artifact classification_report.json failed (non-fatal): %s", e)

        # Feature importances
        if feature_importances:
            fi_json = run_dir / "feature_importances.json"
            fi_json.write_text(json.dumps(feature_importances, indent=2))
            try:
                mlflow.log_artifact(str(fi_json), "importances")
            except Exception as e:
                logger.warning("log_artifact feature_importances.json failed (non-fatal): %s", e)

            try:
                fi_png = run_dir / "feature_importances.png"
                _save_fi_plot(feature_importances, fi_png)
                mlflow.log_artifact(str(fi_png), "plots")
            except Exception as e:
                logger.warning("FI plot failed: %s", e)

        # Register model with MLflow (sklearn flavour)
        try:
            mlflow.sklearn.log_model(model, "sklearn_model")
        except Exception as e:
            logger.warning("sklearn log_model failed (non-fatal): %s", e)

        logger.info("MLflow run %s logged: F1=%.4f", run_id, metrics.get("f1_macro", 0))
        return run_id


# ---------------------------------------------------------------------------
# Model Registry
# ---------------------------------------------------------------------------

def register_best_model(run_id: str, model_name: str) -> int:
    """Register best model in MLflow Model Registry under REGISTERED_MODEL_NAME."""
    import mlflow
    from mlflow.tracking import MlflowClient

    model_uri = f"runs:/{run_id}/sklearn_model"
    mv = mlflow.register_model(model_uri, REGISTERED_MODEL_NAME)

    client = MlflowClient()
    client.update_registered_model(
        REGISTERED_MODEL_NAME,
        description=f"Best signal predictor — {model_name}",
    )
    client.set_registered_model_tag(REGISTERED_MODEL_NAME, "best_model", model_name)
    client.transition_model_version_stage(
        name=REGISTERED_MODEL_NAME,
        version=mv.version,
        stage="Staging",
    )
    logger.info("Registered %s v%s in [Staging]", REGISTERED_MODEL_NAME, mv.version)
    return int(mv.version)
