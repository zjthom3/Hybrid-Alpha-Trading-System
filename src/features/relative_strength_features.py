"""
Relative strength features comparing a ticker to a benchmark.
"""

import pandas as pd

from src.core.types import DataFrame


def _rolling_beta(asset_ret: pd.Series, bench_ret: pd.Series, window: int) -> pd.Series:
    cov = asset_ret.rolling(window=window, min_periods=window).cov(bench_ret)
    var = bench_ret.rolling(window=window, min_periods=window).var()
    return cov / var


def build_relative_strength_features(
    ticker_features: DataFrame,
    benchmark_features: DataFrame,
    lookbacks: list[int],
    beta_window: int,
) -> DataFrame:
    df = ticker_features.copy()

    bench_cols = ["date"]
    if "ret_20d" in benchmark_features:
        bench_cols.append("ret_20d")
    if "ret_60d" in benchmark_features:
        bench_cols.append("ret_60d")
    if "ret_1d" in benchmark_features:
        bench_cols.append("ret_1d")

    bench = benchmark_features[bench_cols].rename(
        columns={
            "ret_20d": "bench_ret_20d",
            "ret_60d": "bench_ret_60d",
            "ret_1d": "bench_ret_1d",
        }
    )
    df = df.merge(bench, on="date", how="left")

    # Relative returns
    if 20 in lookbacks and "ret_20d" in df and "bench_ret_20d" in df:
        df["rel_ret_vs_benchmark_20"] = df["ret_20d"] - df["bench_ret_20d"]
    else:
        df["rel_ret_vs_benchmark_20"] = pd.NA
    if 60 in lookbacks and "ret_60d" in df and "bench_ret_60d" in df:
        df["rel_ret_vs_benchmark_60"] = df["ret_60d"] - df["bench_ret_60d"]
    else:
        df["rel_ret_vs_benchmark_60"] = pd.NA

    # Rolling beta
    asset_returns = df["ret_1d"] if "ret_1d" in df else df["close"].pct_change()
    if "bench_ret_1d" in df:
        bench_returns = df["bench_ret_1d"]
    else:
        bench_returns = benchmark_features["close"].pct_change()
    df["beta_vs_benchmark_60"] = _rolling_beta(asset_returns, bench_returns, beta_window)

    return df[
        [
            "date",
            "ticker",
            "rel_ret_vs_benchmark_20",
            "rel_ret_vs_benchmark_60",
            "beta_vs_benchmark_60",
        ]
    ]


__all__ = ["build_relative_strength_features"]
