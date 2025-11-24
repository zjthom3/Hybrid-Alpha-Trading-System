"""
Volatility-context alpha: prefers lower realized vol; penalizes elevated vol.
Outputs a score in [-1, 1], scaled by z-score of realized vol.
"""

import pandas as pd

from src.core.types import DataFrame


def compute_volatility_alpha(
    features: DataFrame,
    vol_col: str = "realized_vol_20",
    lookback: int = 60,
    z_threshold: float = 1.0,
) -> pd.Series:
    if vol_col not in features:
        raise KeyError(f"Missing volatility column {vol_col} for volatility alpha")

    vol = features[vol_col]
    mean = vol.rolling(window=lookback, min_periods=lookback).mean()
    std = vol.rolling(window=lookback, min_periods=lookback).std()

    zscore = (vol - mean) / std
    score = -zscore / z_threshold  # lower vol → positive alpha
    score = score.clip(-1.0, 1.0)
    return score.fillna(0.0)


__all__ = ["compute_volatility_alpha"]
