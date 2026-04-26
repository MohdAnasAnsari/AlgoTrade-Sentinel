from __future__ import annotations

import argparse
import json
import pickle
import shutil
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
for path in (PROJECT_ROOT, BACKEND_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

from app.database import SessionLocal
from app.models.features import DatasetVersion
from ml.training.mlflow_logger import REGISTERED_MODEL_NAME, setup_mlflow

MODELS_DIR = PROJECT_ROOT / "ml" / "artifacts" / "models"
LABELS = ("BUY", "HOLD", "SELL")


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore the MLflow registry from local model artifacts.")
    parser.add_argument("--artifact-run-id", help="Existing local artifact directory to restore. Defaults to the newest one.")
    parser.add_argument("--stage", default="Production", choices=["Staging", "Production"], help="Target registry stage.")
    args = parser.parse_args()

    source_dir = _resolve_source_dir(args.artifact_run_id)
    payload = _load_artifact_payload(source_dir)
    dataset_version = _latest_dataset_version()

    setup_mlflow()
    client = MlflowClient()

    with mlflow.start_run(run_name=f"restore_{source_dir.name}") as run:
        run_id = run.info.run_id
        model = payload["model"]
        scaler = payload["scaler"]
        feature_names = payload["feature_names"]
        metrics = payload["metrics"]
        model_name = type(model).__name__

        mlflow.set_tags(
            {
                "run_type": "restore",
                "restored_from_local_artifacts": "true",
                "source_artifact_run_id": source_dir.name,
                "model_name": model_name,
            }
        )
        mlflow.log_params(
            {
                "model_name": model_name,
                "dataset_version": dataset_version,
                "n_features": len(feature_names),
                "restored_from_local_artifacts": True,
                "source_artifact_run_id": source_dir.name,
            }
        )
        if metrics:
            mlflow.log_metrics(metrics)

        mlflow.sklearn.log_model(model, "sklearn_model")
        for artifact_name in (
            "classification_report.json",
            "confusion_matrix.json",
            "feature_importances.json",
            "feature_importances.png",
            "confusion_matrix.png",
        ):
            artifact_path = source_dir / artifact_name
            if artifact_path.exists():
                mlflow.log_artifact(str(artifact_path), "restored_artifacts")

        restored_dir = MODELS_DIR / run_id
        restored_dir.mkdir(parents=True, exist_ok=False)
        _persist_runtime_artifacts(restored_dir, model, scaler, feature_names, source_dir)

    _ensure_registered_model(client)
    existing_production = client.get_latest_versions(REGISTERED_MODEL_NAME, stages=["Production"])
    mv = mlflow.register_model(f"runs:/{run_id}/sklearn_model", REGISTERED_MODEL_NAME)
    if args.stage == "Production":
        for version in existing_production:
            if version.version != mv.version:
                client.transition_model_version_stage(
                    name=REGISTERED_MODEL_NAME,
                    version=version.version,
                    stage="Archived",
                )
    client.transition_model_version_stage(
        name=REGISTERED_MODEL_NAME,
        version=mv.version,
        stage=args.stage,
    )
    client.update_registered_model(
        REGISTERED_MODEL_NAME,
        description="Restored from local on-disk model artifacts.",
    )
    client.set_registered_model_tag(REGISTERED_MODEL_NAME, "restored_from_local_artifacts", "true")
    client.set_registered_model_tag(REGISTERED_MODEL_NAME, "source_artifact_run_id", source_dir.name)

    print(f"Restored {source_dir.name} into MLflow run {run_id} and registered {REGISTERED_MODEL_NAME} v{mv.version} in {args.stage}.")


def _resolve_source_dir(artifact_run_id: str | None) -> Path:
    if artifact_run_id:
        candidate = MODELS_DIR / artifact_run_id
        if not candidate.exists():
            raise FileNotFoundError(f"Artifact directory not found: {candidate}")
        return candidate

    candidates = sorted(
        [path for path in MODELS_DIR.iterdir() if path.is_dir() and (path / "model.pkl").exists()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No model artifacts found under {MODELS_DIR}")
    return candidates[0]


def _load_artifact_payload(source_dir: Path) -> dict[str, Any]:
    with open(source_dir / "model.pkl", "rb") as handle:
        model = pickle.load(handle)
    with open(source_dir / "scaler.pkl", "rb") as handle:
        scaler = pickle.load(handle)

    feature_names = json.loads((source_dir / "features.json").read_text(encoding="utf-8"))
    report = _load_json(source_dir / "classification_report.json", {})
    confusion_matrix = _load_json(source_dir / "confusion_matrix.json", {})
    feature_importances = _load_json(source_dir / "feature_importances.json", {})

    metrics: dict[str, float] = {}
    accuracy = report.get("accuracy")
    if accuracy is not None:
        metrics["accuracy"] = float(accuracy)

    macro_avg = report.get("macro avg", {})
    weighted_avg = report.get("weighted avg", {})
    for key, metric_name in (
        ("precision", "precision_macro"),
        ("recall", "recall_macro"),
        ("f1-score", "f1_macro"),
    ):
        if macro_avg.get(key) is not None:
            metrics[metric_name] = float(macro_avg[key])
        if weighted_avg.get(key) is not None:
            metrics[f"{metric_name}_weighted"] = float(weighted_avg[key])

    for label in LABELS:
        label_metrics = report.get(label, {})
        for key, suffix in (("precision", "precision"), ("recall", "recall"), ("f1-score", "f1_score")):
            if label_metrics.get(key) is not None:
                metrics[f"report_{label}_{suffix}"] = float(label_metrics[key])

    matrix = confusion_matrix.get("matrix")
    labels = confusion_matrix.get("labels") or list(LABELS)
    if matrix:
        for row_idx, true_label in enumerate(labels):
            for col_idx, pred_label in enumerate(labels):
                try:
                    metrics[f"cm_{true_label}_{pred_label}"] = float(matrix[row_idx][col_idx])
                except Exception:
                    continue

    for feature, score in list(feature_importances.items())[:20]:
        metrics[f"fi_{feature}"] = float(score)

    return {
        "model": model,
        "scaler": scaler,
        "feature_names": feature_names,
        "metrics": metrics,
    }


def _persist_runtime_artifacts(restored_dir: Path, model: Any, scaler: Any, feature_names: list[str], source_dir: Path) -> None:
    with open(restored_dir / "model.pkl", "wb") as handle:
        pickle.dump(model, handle)
    with open(restored_dir / "scaler.pkl", "wb") as handle:
        pickle.dump(scaler, handle)
    (restored_dir / "features.json").write_text(json.dumps(feature_names, indent=2), encoding="utf-8")

    for artifact_name in (
        "classification_report.json",
        "confusion_matrix.json",
        "feature_importances.json",
        "feature_importances.png",
        "confusion_matrix.png",
    ):
        artifact_path = source_dir / artifact_name
        if artifact_path.exists():
            shutil.copy2(artifact_path, restored_dir / artifact_name)


def _latest_dataset_version() -> int:
    db = SessionLocal()
    try:
        row = db.query(DatasetVersion).order_by(DatasetVersion.version.desc()).first()
        return int(row.version) if row else 0
    finally:
        db.close()


def _ensure_registered_model(client: MlflowClient) -> None:
    try:
        client.create_registered_model(REGISTERED_MODEL_NAME)
    except Exception:
        pass


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
