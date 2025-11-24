"""
Risk utilities: realized volatility, drawdown.
"""

import numpy as np
import pandas as pd


def realized_vol(returns: pd.Series, lookback: int) -> pd.Series:
    return returns.rolling(window=lookback, min_periods=lookback).std() * np.sqrt(252)


def drawdown(series: pd.Series) -> pd.Series:
    cum_max = series.cummax()
    return (series - cum_max) / cum_max


__all__ = ["realized_vol", "drawdown"]
