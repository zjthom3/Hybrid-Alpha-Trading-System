"""
Trend and return-based features (SMAs, returns, momentum).
"""

from typing import Dict, Iterable, Sequence

import pandas as pd

from src.core.types import DataFrame


def _sma(df: DataFrame, window: int) -> pd.Series:
    return df["close"].rolling(window=window, min_periods=window).mean()


def _returns(df: DataFrame, window: int) -> pd.Series:
    return df["close"].pct_change(periods=window)


def build_trend_features(
    bars: DataFrame,
    lookbacks: Dict[str, Iterable[int]],
) -> DataFrame:
    """
    Build trend-related features: SMAs, distance to SMAs, and rolling returns.
    """
    sma_windows: Sequence[int] = lookbacks.get("sma", [])
    ret_windows: Sequence[int] = lookbacks.get("returns", [])

    df = bars.copy()

    # Moving averages
    for w in sma_windows:
        df[f"sma_{w}"] = _sma(df, w)

    # Distances to SMAs
    for w in sma_windows:
        df[f"dist_to_sma_{w}"] = (df["close"] - df[f"sma_{w}"]) / df[f"sma_{w}"]

    # Rolling returns
    for w in ret_windows:
        df[f"ret_{w}d"] = _returns(df, w)

    # Momentum example: 20-day return over 20-day vol if available
    if "ret_20d" in df and "realized_vol_20" in df:
        df["momentum_20"] = df["ret_20d"] / df["realized_vol_20"]

    columns = ["date", "ticker"]
    columns += [c for w in ret_windows for c in [f"ret_{w}d"] if f"ret_{w}d" in df]
    columns += [c for w in sma_windows for c in [f"sma_{w}"] if f"sma_{w}" in df]
    columns += [c for w in sma_windows for c in [f"dist_to_sma_{w}"] if f"dist_to_sma_{w}" in df]
    if "momentum_20" in df:
        columns.append("momentum_20")

    return df[columns]


__all__ = ["build_trend_features"]
