"""
Prefect flow: Model Training Pipeline

Trains all models on the latest dataset version and logs to MLflow.
Can be scheduled after feature_flow completes.
"""
import logging
import sys
from pathlib import Path

from prefect import flow, task

_PROJECT_ROOT = str(Path(__file__).parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logger = logging.getLogger(__name__)


@task(retries=1, retry_delay_seconds=30, name="train-models")
def train_models_task(
    dataset_version: int,
    model_list: list[str] | None,
    run_name: str,
    n_optuna_trials: int,
) -> dict:
    """Train all models and log to MLflow."""
    from ml.training.trainer import train_all_models

    result = train_all_models(
        dataset_version=dataset_version,
        model_list=model_list,
        run_name=run_name,
        n_optuna_trials=n_optuna_trials,
    )
    return result


@task(name="log-summary")
def log_summary_task(result: dict) -> None:
    """Log training summary."""
    logger.info(
        "Training complete | best=%s | F1=%.4f | run_id=%s | dataset_v%d",
        result.get("best_model"),
        result.get("best_f1", 0),
        result.get("best_run_id"),
        result.get("dataset_version", 0),
    )

    for r in result.get("results", []):
        m = r["metrics"]
        logger.info(
            "  %-35s  F1=%.4f  Acc=%.4f  AUC=%.4f",
            r["model_name"],
            m.get("f1_macro", 0),
            m.get("accuracy", 0),
            m.get("roc_auc", 0),
        )


@flow(name="model-training-pipeline")
def model_training_pipeline(
    dataset_version: int = 1,
    model_list: list[str] | None = None,
    run_name: str = "prefect_run",
    n_optuna_trials: int = 20,
) -> dict:
    """
    Full model training pipeline:
    1. Train 6+ classifiers on versioned dataset
    2. Optuna HPO for top-2 models
    3. Evaluate on held-out test set
    4. Log all runs to MLflow
    5. Register best model in Model Registry
    """
    result = train_models_task(
        dataset_version=dataset_version,
        model_list=model_list,
        run_name=run_name,
        n_optuna_trials=n_optuna_trials,
    )
    log_summary_task(result)
    return result


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--version",  type=int,  default=1)
    parser.add_argument("--run-name", default="prefect_run")
    parser.add_argument("--trials",   type=int,  default=20)
    args = parser.parse_args()

    model_training_pipeline(
        dataset_version=args.version,
        run_name=args.run_name,
        n_optuna_trials=args.trials,
    )
