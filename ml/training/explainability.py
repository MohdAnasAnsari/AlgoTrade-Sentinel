"""
Feature importance computation for trained models.

Supports:
- Tree-based models: built-in feature_importances_
- LogisticRegression: abs(coef).mean(axis=0)
- Fallback: permutation importance (n_repeats=5)
"""
import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


def compute_feature_importances(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: list[str],
    n_perm_repeats: int = 5,
) -> dict[str, float]:
    """
    Compute feature importances for a trained model.
    Returns dict {feature: score} sorted descending, normalized to [0, 1].
    """
    scores: Optional[np.ndarray] = None

    # Tree-based: built-in importances
    if hasattr(model, "feature_importances_"):
        scores = np.array(model.feature_importances_)

    # Logistic Regression: abs(coef) averaged over classes
    elif hasattr(model, "coef_"):
        coef = model.coef_
        if coef.ndim == 2:
            scores = np.abs(coef).mean(axis=0)
        else:
            scores = np.abs(coef)

    # Fallback: permutation importance
    else:
        try:
            from sklearn.inspection import permutation_importance
            result = permutation_importance(
                model, X_test, y_test,
                n_repeats=n_perm_repeats,
                random_state=42,
                scoring="f1_macro",
            )
            scores = result.importances_mean
        except Exception as e:
            logger.warning("Permutation importance failed: %s", e)
            return {}

    if scores is None or len(scores) != len(feature_names):
        return {}

    # Normalize to [0, 1]
    total = scores.sum()
    if total > 0:
        scores = scores / total

    # Clip negatives (permutation importance can be slightly negative)
    scores = np.clip(scores, 0, None)

    # Sort descending
    paired = list(zip(feature_names, scores.tolist()))
    paired.sort(key=lambda x: x[1], reverse=True)

    return {feat: round(score, 6) for feat, score in paired}
