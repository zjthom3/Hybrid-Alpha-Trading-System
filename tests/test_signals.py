import pandas as pd

from src.signals.mean_reversion_alpha import compute_mean_reversion_alpha
from src.signals.relative_strength_alpha import compute_relative_strength_alpha
from src.signals.trend_alpha import compute_trend_alpha
from src.signals.volatility_alpha import compute_volatility_alpha


def test_trend_alpha_direction():
    df = pd.DataFrame(
        {
            "close": [100, 102, 104, 106],
            "sma_20": [99, 99, 100, 101],
            "sma_50": [98, 98, 99, 100],
        }
    )
    score = compute_trend_alpha(df, fast=20, slow=50)
    assert score.iloc[-1] > 0
    df["close"] = [90, 88, 87, 86]
    score_neg = compute_trend_alpha(df, fast=20, slow=50)
    assert score_neg.iloc[-1] < 0


def test_mean_reversion_alpha_oversold_positive():
    df = pd.DataFrame({"ret_5d": [0.0, -0.02, -0.03, -0.04, -0.05]})
    score = compute_mean_reversion_alpha(df, lookback=5, z_threshold=1.0)
    assert score.iloc[-1] > 0


def test_volatility_alpha_penalizes_high_vol():
    df = pd.DataFrame({"realized_vol_20": [0.1] * 50 + [0.4] * 10})
    score = compute_volatility_alpha(df, vol_col="realized_vol_20", lookback=30, z_threshold=1.0)
    assert score.iloc[-1] < 0


def test_relative_strength_alpha():
    df = pd.DataFrame({"rel_ret_vs_benchmark_20": [0.0, 0.02, -0.01]})
    score = compute_relative_strength_alpha(df, lookback=20, scale=0.05)
    assert score.iloc[1] > 0
    assert score.iloc[2] < 0
