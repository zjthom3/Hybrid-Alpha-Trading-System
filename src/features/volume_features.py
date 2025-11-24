"""
Volume-based features: z-score and volume relative to rolling average.
"""

import pandas as pd

from src.core.types import DataFrame


def build_volume_features(bars: DataFrame, lookback: int) -> DataFrame:
    df = bars.copy()
    rolling_mean = df["volume"].rolling(window=lookback, min_periods=lookback).mean()
    rolling_std = df["volume"].rolling(window=lookback, min_periods=lookback).std()

    df[f"volume_z_{lookback}"] = (df["volume"] - rolling_mean) / rolling_std
    df[f"volume_to_{lookback}d_avg"] = df["volume"] / rolling_mean

    return df[
        [
            "date",
            "ticker",
            f"volume_z_{lookback}",
            f"volume_to_{lookback}d_avg",
        ]
    ]


__all__ = ["build_volume_features"]
