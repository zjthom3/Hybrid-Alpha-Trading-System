"""
Volatility-related features: realized volatility, ATR, intraday range.
"""

import numpy as np
import pandas as pd

from src.core.types import DataFrame


def _realized_vol(df: DataFrame, window: int) -> pd.Series:
    returns = df["close"].pct_change()
    return returns.rolling(window=window, min_periods=window).std() * np.sqrt(252)


def _true_range(df: DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - prev_close).abs()
    tr3 = (df["low"] - prev_close).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def build_volatility_features(
    bars: DataFrame,
    realized_vol_windows: list[int],
    atr_period: int,
) -> DataFrame:
    df = bars.copy()

    # Realized volatility (annualized)
    for w in realized_vol_windows:
        df[f"realized_vol_{w}"] = _realized_vol(df, w)

    # Average True Range (normalized by close)
    tr = _true_range(df)
    df[f"atr_{atr_period}"] = tr.rolling(window=atr_period, min_periods=atr_period).mean()
    df[f"atr_{atr_period}"] = df[f"atr_{atr_period}"] / df["close"]

    # Intraday range percent
    df["intraday_range_pct"] = (df["high"] - df["low"]) / df["close"]

    return df[
        [
            "date",
            "ticker",
            *[f"realized_vol_{w}" for w in realized_vol_windows],
            f"atr_{atr_period}",
            "intraday_range_pct",
        ]
    ]


__all__ = ["build_volatility_features"]
