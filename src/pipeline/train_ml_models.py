"""
Pipeline to train LightGBM models for next-state prediction and persist artifacts.
"""

import sys
from pathlib import Path
from typing import Iterable, List

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models.ml.lightgbm_next_state import (
    TrainResult,
    load_trained_model,
    save_trained_model,
    train_model,
)
from models.ml.model_registry import ModelKey
from src.core.io import read_parquet  # noqa: E402
from src.core.utils import ensure_directory, get_logger, load_config  # noqa: E402
from src.features.label_targets import label_future_states  # noqa: E402

logger = get_logger(__name__)


def train_ml_models(
    tickers: Iterable[str] | None = None,
    settings_path: str | Path = "config/settings.yaml",
    data_sources_path: str | Path = "config/data_sources.yaml",
) -> List[Path]:
    settings = load_config(settings_path)
    data_sources = load_config(data_sources_path)

    tickers_to_process: List[str] = list(settings.get("tickers", []))
    if tickers:
        tickers_to_process = list(dict.fromkeys(list(tickers) + tickers_to_process))

    features_dir = Path(settings.get("paths", {}).get("features_dir", "data/features"))
    artifacts_dir = Path("models/ml/artifacts")
    ensure_directory(artifacts_dir)

    horizons = settings.get("ml", {}).get("horizons", [1, 3, 5])
    model_name = settings.get("ml", {}).get("model_name", "lightgbm_v1")
    test_size = settings.get("ml", {}).get("test_size", 0.2)

    written: List[Path] = []
    for ticker in tickers_to_process:
        feats_path = features_dir / f"{ticker}.parquet"
        if not feats_path.exists():
            raise FileNotFoundError(f"Features file not found for {ticker}: {feats_path}")
        feats = read_parquet(feats_path)

        # Add labels if not already present
        label_cols = [f"target_state_h{h}" for h in horizons]
        if not set(label_cols).issubset(set(feats.columns)):
            feats = label_future_states(feats, horizons=horizons)

        for h in horizons:
            label_col = f"target_state_h{h}"
            # Drop rows without label
            train_df = feats.dropna(subset=[label_col])
            params = {
                "n_estimators": 400,
                "learning_rate": 0.05,
                "num_leaves": 63,
                "max_depth": -1,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "objective": "multiclass",
                "num_class": 7,  # states -3..+3
                "random_state": 42,
                "min_child_samples": 50,
                "reg_lambda": 1.0,
                "reg_alpha": 0.1,
                "class_weight": "balanced",
            }
            result: TrainResult = train_model(train_df, label_col=label_col, params=params, test_size=test_size)
            key = ModelKey(model_name=model_name, ticker=ticker, horizon=h, version="v1")
            path = save_trained_model(result, artifacts_dir=str(artifacts_dir), key=key)
            written.append(path)
            logger.info(f"Trained model for {ticker} h{h} -> {path}")

    return written


if __name__ == "__main__":
    train_ml_models()
