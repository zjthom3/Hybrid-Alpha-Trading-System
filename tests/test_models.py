import numpy as np
import pandas as pd

from models.ml.lightgbm_next_state import (
    TrainResult,
    load_trained_model,
    predict_proba,
    save_trained_model,
    train_model,
)
from models.ml.model_registry import ModelKey
from src.features.label_targets import _default_thresholds, label_future_states


def test_label_future_states_buckets_returns():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=6, freq="D").date,
            "ticker": ["TST"] * 6,
            "close": [100, 101, 99, 100, 106, 105],
        }
    )
    labeled = label_future_states(df, horizons=[1, 2], thresholds=_default_thresholds())
    assert "target_state_h1" in labeled.columns
    assert "target_state_h2" in labeled.columns
    # Future up move should give positive state
    assert labeled.loc[0, "target_state_h1"] > 0


def test_lightgbm_training_and_save_load(tmp_path):
    # Simple synthetic dataset
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=50, freq="D").date,
            "ticker": ["TST"] * 50,
            "feat1": np.linspace(0, 1, 50),
            "feat2": np.linspace(1, 0, 50),
        }
    )
    df["close"] = 100 + df["feat1"] * 2
    df = label_future_states(df, horizons=[1], thresholds=_default_thresholds())
    params = {
        "n_estimators": 50,
        "learning_rate": 0.1,
        "max_depth": -1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "objective": "multiclass",
        "num_class": 7,
        "random_state": 42,
    }
    result: TrainResult = train_model(df, label_col="target_state_h1", params=params, test_size=0.2)
    key = ModelKey(model_name="test_model", ticker="TST", horizon=1, version="vtest")
    path = save_trained_model(result, artifacts_dir=tmp_path, key=key)
    loaded = load_trained_model(artifacts_dir=tmp_path, key=key)
    proba = predict_proba(loaded.model, loaded.scaler, df[loaded.feature_columns], loaded.feature_columns)
    assert proba.shape[0] == len(df)
