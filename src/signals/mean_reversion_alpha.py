"""
Rule-based mean reversion alpha: looks for short-term overextension relative to recent mean.
Outputs a score in [-1, 1]; positive when price is below short-term mean by > threshold.
"""

import numpy as np
import pandas as pd

from src.core.types import DataFrame


def compute_mean_reversion_alpha(
    features: DataFrame,
    lookback: int = 5,
    z_threshold: float = 1.0,
) -> pd.Series:
    ret_col = f"ret_{lookback}d"
    if ret_col not in features:
        raise KeyError(f"Missing return column {ret_col} for mean reversion alpha")

    returns = features[ret_col]
    rolling_mean = returns.rolling(window=lookback, min_periods=lookback).mean()
    rolling_std = returns.rolling(window=lookback, min_periods=lookback).std()

    zscore = (returns - rolling_mean) / rolling_std
    # Negative zscore means oversold; positive alpha
    score = -zscore / z_threshold
    score = score.clip(-1.0, 1.0)
    return score.fillna(0.0)


__all__ = ["compute_mean_reversion_alpha"]
