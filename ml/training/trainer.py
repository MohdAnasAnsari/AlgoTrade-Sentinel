"""
Model training pipeline for AlgoTrade Sentinel.

Loads versioned parquet dataset → trains 6+ classifiers →
runs Optuna HPO on top-2 models → evaluates on held-out test set →
logs everything to MLflow → registers best model.
"""
import json
import logging
import random
import sys
import warnings
from pathlib import Path
from typing import Callable, Optional

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
import optuna

optuna.logging.set_verbosity(optuna.logging.WARNING)

# ── Global reproducibility seed ───────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ── Optional ensemble imports ──────────────────────────────────────────────
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

# ── Paths ─────────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).parents[2]   # AlgoTrade-Sentinel/
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

DATASETS_DIR = _PROJECT_ROOT / "ml" / "artifacts" / "datasets"
MODELS_DIR   = _PROJECT_ROOT / "ml" / "artifacts" / "models"

from ml.features.feature_engineer import ALL_FEATURES  # noqa: E402

logger = logging.getLogger(__name__)

# Fixed label order for consistent encoding
LABEL_ORDER = ["BUY", "HOLD", "SELL"]

# Models that support Optuna HPO (first 2 present in the run get optimized)
OPTUNA_TARGETS = ["RandomForestClassifier", "LGBMClassifier", "XGBClassifier"]


# ---------------------------------------------------------------------------
# Model factory
# ---------------------------------------------------------------------------

def get_available_models(model_list: Optional[list[str]] = None) -> dict:
    """Return ordered dict of {name: model} for available + requested models."""
    models: dict = {
        "LogisticRegression": LogisticRegression(
            max_iter=1000, random_state=42, solver="lbfgs"
        ),
        "DecisionTreeClassifier": DecisionTreeClassifier(
            max_depth=8, random_state=42
        ),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=200, random_state=42, n_jobs=-1
        ),
        "GradientBoostingClassifier": GradientBoostingClassifier(
            n_estimators=100, random_state=42
        ),
    }
    if HAS_XGBOOST:
        models["XGBClassifier"] = XGBClassifier(
            n_estimators=100, random_state=42,
            eval_metric="mlogloss", verbosity=0, use_label_encoder=False,
        )
    if HAS_LGBM:
        models["LGBMClassifier"] = LGBMClassifier(
            n_estimators=100, random_state=42, verbose=-1
        )
    if HAS_CATBOOST:
        models["CatBoostClassifier"] = CatBoostClassifier(
            iterations=100, random_state=42, verbose=0
        )

    if model_list:
        models = {k: v for k, v in models.items() if k in model_list}
    return models


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_model(
    model, X_test: np.ndarray, y_test: np.ndarray, label_names: list[str]
) -> tuple[dict, np.ndarray, dict]:
    y_pred = model.predict(X_test)

    metrics: dict = {
        "accuracy":        float(accuracy_score(y_test, y_pred)),
        "precision_macro": float(precision_score(y_test, y_pred, average="macro", zero_division=0)),
        "recall_macro":    float(recall_score(y_test, y_pred, average="macro", zero_division=0)),
        "f1_macro":        float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
    }

    if hasattr(model, "predict_proba"):
        try:
            probas = model.predict_proba(X_test)
            metrics["roc_auc"] = float(
                roc_auc_score(y_test, probas, multi_class="ovr", average="macro")
            )
        except Exception:
            metrics["roc_auc"] = 0.0
    else:
        metrics["roc_auc"] = 0.0

    cm     = confusion_matrix(y_test, y_pred)
    report = classification_report(
        y_test, y_pred,
        target_names=label_names,
        output_dict=True,
        zero_division=0,
    )
    return metrics, cm, report


# ---------------------------------------------------------------------------
# Optuna HPO objectives
# ---------------------------------------------------------------------------

def _optimize_rf(X: np.ndarray, y: np.ndarray, tscv, n_trials: int):
    def obj(trial):
        m = RandomForestClassifier(
            n_estimators     = trial.suggest_int("n_estimators",    50, 200),
            max_depth        = trial.suggest_int("max_depth",        3,  15),
            min_samples_split= trial.suggest_int("min_samples_split",2,  20),
            min_samples_leaf = trial.suggest_int("min_samples_leaf", 1,  10),
            max_features     = trial.suggest_categorical("max_features", ["sqrt", "log2"]),
            random_state=42, n_jobs=-1,
        )
        return cross_val_score(m, X, y, cv=tscv, scoring="f1_macro", n_jobs=-1).mean()
    s = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED))
    s.optimize(obj, n_trials=n_trials, show_progress_bar=False)
    return RandomForestClassifier(**s.best_params, random_state=SEED, n_jobs=-1)


def _optimize_lgbm(X: np.ndarray, y: np.ndarray, tscv, n_trials: int):
    def obj(trial):
        m = LGBMClassifier(
            n_estimators     = trial.suggest_int("n_estimators",       50, 200),
            max_depth        = trial.suggest_int("max_depth",           3,  10),
            learning_rate    = trial.suggest_float("learning_rate",   0.01, 0.3, log=True),
            num_leaves       = trial.suggest_int("num_leaves",        20,  80),
            min_child_samples= trial.suggest_int("min_child_samples",  5,  50),
            random_state=42, verbose=-1,
        )
        return cross_val_score(m, X, y, cv=tscv, scoring="f1_macro").mean()
    s = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED))
    s.optimize(obj, n_trials=n_trials, show_progress_bar=False)
    return LGBMClassifier(**s.best_params, random_state=SEED, verbose=-1)


def _optimize_xgb(X: np.ndarray, y: np.ndarray, tscv, n_trials: int):
    def obj(trial):
        m = XGBClassifier(
            n_estimators    = trial.suggest_int("n_estimators",    50, 200),
            max_depth       = trial.suggest_int("max_depth",        3,  10),
            learning_rate   = trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            subsample       = trial.suggest_float("subsample",      0.6,  1.0),
            colsample_bytree= trial.suggest_float("colsample_bytree", 0.6, 1.0),
            random_state=42, eval_metric="mlogloss", verbosity=0,
        )
        return cross_val_score(m, X, y, cv=tscv, scoring="f1_macro").mean()
    s = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED))
    s.optimize(obj, n_trials=n_trials, show_progress_bar=False)
    return XGBClassifier(**s.best_params, random_state=SEED, eval_metric="mlogloss", verbosity=0)


_OPTIMIZERS: dict[str, Callable] = {
    "RandomForestClassifier": _optimize_rf,
    "LGBMClassifier":         _optimize_lgbm,
    "XGBClassifier":          _optimize_xgb,
}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def train_all_models(
    dataset_version:   int = 1,
    model_list:        Optional[list[str]] = None,
    run_name:          str = "training_run",
    n_optuna_trials:   int = 20,
    mlflow_uri:        Optional[str] = None,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """
    Train all models on dataset vN, log to MLflow, register best model.
    Returns summary dict with results list, best_model, best_f1, best_run_id.
    """
    from ml.training.mlflow_logger import (
        get_default_uri, log_training_run, register_best_model, setup_mlflow
    )
    from ml.training.explainability import compute_feature_importances

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # ── MLflow setup ─────────────────────────────────────────────────────
    setup_mlflow(mlflow_uri or get_default_uri())

    # ── Load dataset ─────────────────────────────────────────────────────
    dataset_path = DATASETS_DIR / f"dataset_v{dataset_version}.parquet"
    meta_path    = DATASETS_DIR / f"dataset_v{dataset_version}_meta.json"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset v{dataset_version} not found at {dataset_path}")

    df   = pd.read_parquet(dataset_path)
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    # ── Features and labels ──────────────────────────────────────────────
    feature_cols = [c for c in ALL_FEATURES if c in df.columns]
    X_raw        = df[feature_cols].values.astype(float)
    y_raw        = df["signal_label"].values

    le = LabelEncoder()
    le.fit(LABEL_ORDER)
    y           = le.transform(y_raw)
    label_names = le.classes_.tolist()

    # ── Time-aware split ─────────────────────────────────────────────────
    split_date = meta.get("split_date", "2023-01-01")
    df_dates   = pd.to_datetime(df["date"])
    split_dt   = pd.to_datetime(split_date)

    train_mask = (df_dates < split_dt).values
    test_mask  = (df_dates >= split_dt).values

    X_train_raw, X_test_raw = X_raw[train_mask], X_raw[test_mask]
    y_train,     y_test     = y[train_mask],     y[test_mask]

    if len(X_train_raw) == 0 or len(X_test_raw) == 0:
        raise ValueError("Empty train or test split — check split_date in metadata")

    # ── Scale (fit on train only) ─────────────────────────────────────────
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_test  = scaler.transform(X_test_raw)

    # ── Models ───────────────────────────────────────────────────────────
    models        = get_available_models(model_list)
    total_models  = len(models)
    to_optimize   = [m for m in OPTUNA_TARGETS if m in models][:2]
    tscv          = TimeSeriesSplit(n_splits=5)

    logger.info(
        "Training %d models | dataset v%d | train=%d test=%d | Optuna→%s",
        total_models, dataset_version, len(X_train), len(X_test), to_optimize,
    )

    results: list[dict] = []
    best_f1          = -1.0
    best_run_id: Optional[str]      = None
    best_model_name: Optional[str]  = None

    for idx, (model_name, model) in enumerate(models.items()):
        logger.info("[%d/%d] %s", idx + 1, total_models, model_name)

        # ── Optuna HPO ───────────────────────────────────────────────────
        if model_name in to_optimize and n_optuna_trials > 0:
            logger.info("  Optuna HPO (%d trials) …", n_optuna_trials)
            optimizer = _OPTIMIZERS.get(model_name)
            if optimizer:
                try:
                    model = optimizer(X_train, y_train, tscv, n_optuna_trials)
                    logger.info("  best_params: %s", model.get_params())
                except Exception as exc:
                    logger.warning("  Optuna failed: %s — using default", exc)

        # ── Train ─────────────────────────────────────────────────────────
        model.fit(X_train, y_train)

        # ── Evaluate ─────────────────────────────────────────────────────
        metrics, cm, report = evaluate_model(model, X_test, y_test, label_names)

        # ── Feature importances ──────────────────────────────────────────
        fi = compute_feature_importances(model, X_test, y_test, feature_cols)

        # ── Collect hyperparams ──────────────────────────────────────────
        try:
            hp = {k: str(v) for k, v in model.get_params().items() if not callable(v)}
        except Exception:
            hp = {}

        # ── MLflow log ────────────────────────────────────────────────────
        run_id = log_training_run(
            run_name          = f"{run_name}_{model_name}",
            model             = model,
            model_name        = model_name,
            params            = hp,
            metrics           = metrics,
            cm                = cm,
            report            = report,
            feature_importances = fi if fi else None,
            scaler            = scaler,
            feature_names     = feature_cols,
            dataset_version   = dataset_version,
            train_size        = len(X_train),
            test_size         = len(X_test),
            label_names       = label_names,
            artifacts_dir     = MODELS_DIR,
        )

        results.append({
            "model_name": model_name,
            "run_id":     run_id,
            "metrics":    metrics,
        })

        if metrics["f1_macro"] > best_f1:
            best_f1          = metrics["f1_macro"]
            best_run_id      = run_id
            best_model_name  = model_name

        logger.info(
            "  ✓ F1=%.4f  Acc=%.4f  AUC=%.4f",
            metrics["f1_macro"], metrics["accuracy"], metrics.get("roc_auc", 0),
        )

        if progress_callback:
            progress_callback(model_name, idx + 1, total_models)

    # ── Register best model ───────────────────────────────────────────────
    if best_run_id:
        try:
            ver = register_best_model(best_run_id, best_model_name)
            logger.info("Registered %s v%d [Staging]", best_model_name, ver)
        except Exception as exc:
            logger.warning("Model registration failed: %s", exc)

    return {
        "results":         results,
        "best_model":      best_model_name,
        "best_f1":         round(best_f1, 4),
        "best_run_id":     best_run_id,
        "dataset_version": dataset_version,
        "train_size":      int(len(X_train)),
        "test_size":       int(len(X_test)),
        "label_names":     label_names,
    }


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--version",  type=int,   default=1)
    parser.add_argument("--models",   nargs="*",  default=None)
    parser.add_argument("--run-name", default="cli_run")
    parser.add_argument("--trials",   type=int,   default=20)
    args = parser.parse_args()

    result = train_all_models(
        dataset_version=args.version,
        model_list=args.models,
        run_name=args.run_name,
        n_optuna_trials=args.trials,
    )
    print(f"\nBest: {result['best_model']}  F1={result['best_f1']:.4f}  run={result['best_run_id']}")
