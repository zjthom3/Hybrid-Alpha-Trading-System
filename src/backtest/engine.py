"""
Simple daily backtest engine: applies target weights to next-day returns.
Assumes positions are end-of-day target weights applied to next day's close-to-close return.
"""

import pandas as pd

from src.core.types import DataFrame


def run_backtest(
    prices: DataFrame,
    positions: DataFrame,
    strategy_name: str,
) -> tuple[DataFrame, DataFrame]:
    # Align on date/ticker
    df = positions.merge(
        prices[["date", "ticker", "close"]],
        on=["date", "ticker"],
        how="left",
        suffixes=("", "_price"),
    )
    df = df.sort_values(["ticker", "date"])

    # Compute forward returns (next day close / current close - 1)
    df["next_close"] = df.groupby("ticker")["close"].shift(-1)
    df["ret_1d_fwd"] = df["next_close"] / df["close"] - 1.0

    # Shift PnL to the day the return is realized (next day)
    df["pnl"] = df["target_weight"] * df["ret_1d_fwd"]
    df["pnl_effective_date"] = df["date"].shift(-1)

    # Aggregate by effective date to avoid first day PnL; drop NaN effective dates
    daily = (
        df.dropna(subset=["pnl_effective_date"])
        .groupby("pnl_effective_date")["pnl"]
        .sum()
        .rename_axis("date")
        .reset_index()
        .rename(columns={"pnl": "daily_return"})
    )

    # Recompute exposures by calendar date
    exposures = df.groupby("date")["target_weight"].agg(
        gross_exposure=lambda s: s.abs().sum(), net_exposure="sum"
    ).reset_index()
    portfolio = exposures.merge(daily, on="date", how="left").fillna({"daily_return": 0.0})
    portfolio = portfolio.sort_values("date").reset_index(drop=True)
    portfolio["strategy_name"] = strategy_name

    trades = df[
        [
            "date",
            "ticker",
            "strategy_name",
            "target_weight",
            "ret_1d_fwd",
            "pnl",
        ]
    ]
    return portfolio, trades


__all__ = ["run_backtest"]
