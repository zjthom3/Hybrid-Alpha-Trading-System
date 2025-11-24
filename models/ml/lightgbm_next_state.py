"""
LightGBM classifier utilities for next-state prediction.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from models.ml.model_registry import ModelKey, save_model, load_model


@dataclass
class TrainResult:
    model: lgb.LGBMClassifier
    scaler: StandardScaler
    feature_columns: List[str]
    classes_: np.ndarray


def _prepare_xy(features: pd.DataFrame, label_col: str, drop_cols: Iterable[str]) -> Tuple[pd.DataFrame, pd.Series]:
    drop_set = set(drop_cols)
    X = features.drop(columns=[c for c in features.columns if c in drop_set])
    y = features[label_col]
    return X, y


def train_model(
    features: pd.DataFrame,
    label_col: str,
    params: Dict,
    test_size: float = 0.2,
    random_state: int = 42,
) -> TrainResult:
    # Drop labels with too few samples to avoid unseen classes in validation
    label_counts = features[label_col].value_counts()
    rare_labels = label_counts[label_counts < 2].index
    if len(rare_labels) > 0:
        features = features[~features[label_col].isin(rare_labels)]

    if features.empty:
        raise ValueError("Not enough samples after dropping rare labels for training.")

    X, y = _prepare_xy(features, label_col, drop_cols=["date", "ticker"])
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X.fillna(0.0))
    X_scaled_df = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)

    # Stratify only if all classes have at least 2 samples
    value_counts = y.value_counts()
    stratify = y if (value_counts.min() >= 2 and len(value_counts) > 1) else None

    X_train, X_val, y_train, y_val = train_test_split(
        X_scaled_df, y, test_size=test_size, random_state=random_state, stratify=stratify
    )

    clf = lgb.LGBMClassifier(**params)
    clf.fit(X_train, y_train, eval_set=[(X_val, y_val)])

    return TrainResult(model=clf, scaler=scaler, feature_columns=list(X.columns), classes_=clf.classes_)


def predict_proba(
    model: lgb.LGBMClassifier,
    scaler: StandardScaler,
    features: pd.DataFrame,
    feature_columns: List[str],
) -> np.ndarray:
    X = features.copy()
    missing = [c for c in feature_columns if c not in X.columns]
    for c in missing:
        X[c] = 0.0
    X = X[feature_columns]
    X_scaled = scaler.transform(X.fillna(0.0))
    X_scaled = pd.DataFrame(X_scaled, columns=feature_columns, index=X.index)
    return model.predict_proba(X_scaled)


def save_trained_model(train_result: TrainResult, artifacts_dir: str, key: ModelKey):
    payload = {
        "model": train_result.model,
        "scaler": train_result.scaler,
        "feature_columns": train_result.feature_columns,
        "classes_": train_result.classes_,
    }
    return save_model(payload, artifacts_dir, key)


def load_trained_model(artifacts_dir: str, key: ModelKey) -> TrainResult:
    payload = load_model(artifacts_dir, key)
    return TrainResult(
        model=payload["model"],
        scaler=payload["scaler"],
        feature_columns=payload["feature_columns"],
        classes_=payload["classes_"],
    )


__all__ = [
    "TrainResult",
    "train_model",
    "predict_proba",
    "save_trained_model",
    "load_trained_model",
]
