"""
Rule-based trend alpha: favors prices above longer-term moving averages.
Outputs a score in [-1, 1] based on distance to SMA.
"""

import numpy as np
import pandas as pd

from src.core.types import DataFrame


def compute_trend_alpha(features: DataFrame, fast: int = 20, slow: int = 50) -> pd.Series:
    fast_col = f"sma_{fast}"
    slow_col = f"sma_{slow}"
    required = [fast_col, slow_col, "close"]
    missing = [c for c in required if c not in features]
    if missing:
        raise KeyError(f"Missing columns for trend alpha: {missing}")

    price = features["close"]
    fast_ma = features[fast_col]
    slow_ma = features[slow_col]

    # Distance to MAs normalized by price; combine fast/slow signals
    dist_fast = (price - fast_ma) / price
    dist_slow = (price - slow_ma) / price
    score = 0.6 * dist_fast + 0.4 * dist_slow
    score = score.clip(-1.0, 1.0)
    return score.fillna(0.0)


__all__ = ["compute_trend_alpha"]
