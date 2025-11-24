"""
Simple rule-based regime classifier using trend and volatility.
Labels: bull, bear, choppy, crash
"""

import pandas as pd

from src.core.types import DataFrame
from src.core.utils import get_logger

logger = get_logger(__name__)


def compute_drawdown(close: pd.Series) -> pd.Series:
    cum_max = close.cummax()
    return (close - cum_max) / cum_max


def assign_regime(
    bars: DataFrame,
    trend_ma_short: int,
    trend_ma_long: int,
    vol_lookback: int,
    high_vol_zscore: float,
    crash_drawdown_threshold: float,
) -> DataFrame:
    df = bars.copy()
    df["sma_short"] = df["close"].rolling(trend_ma_short, min_periods=trend_ma_short).mean()
    df["sma_long"] = df["close"].rolling(trend_ma_long, min_periods=trend_ma_long).mean()

    returns = df["close"].pct_change()
    vol = returns.rolling(vol_lookback, min_periods=vol_lookback).std() * (252 ** 0.5)
    vol_mean = vol.rolling(vol_lookback, min_periods=vol_lookback).mean()
    vol_std = vol.rolling(vol_lookback, min_periods=vol_lookback).std()
    vol_z = (vol - vol_mean) / vol_std

    drawdown = compute_drawdown(df["close"])

    labels = []
    ids = []
    for price, s_short, s_long, vz, dd in zip(df["close"], df["sma_short"], df["sma_long"], vol_z, drawdown):
        if pd.isna(price) or pd.isna(s_short) or pd.isna(s_long) or pd.isna(vz):
            labels.append("choppy")
            ids.append(2)
            continue
        if dd <= crash_drawdown_threshold:
            labels.append("crash")
            ids.append(3)
        elif price > s_long and vz <= high_vol_zscore:
            labels.append("bull")
            ids.append(0)
        elif price < s_long and vz <= high_vol_zscore:
            labels.append("bear")
            ids.append(1)
        else:
            labels.append("choppy")
            ids.append(2)

    df_out = pd.DataFrame(
        {
            "date": df["date"],
            "benchmark": df["ticker"],
            "regime_label": labels,
            "regime_id": ids,
            "regime_prob_bull": [1.0 if l == "bull" else 0.0 for l in labels],
            "regime_prob_bear": [1.0 if l == "bear" else 0.0 for l in labels],
            "regime_prob_choppy": [1.0 if l == "choppy" else 0.0 for l in labels],
            "regime_prob_crash": [1.0 if l == "crash" else 0.0 for l in labels],
        }
    )
    return df_out


__all__ = ["assign_regime"]
