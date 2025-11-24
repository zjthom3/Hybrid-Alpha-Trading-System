"""
Backtest reporting: compute metrics and write outputs.
"""

import json
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from src.backtest.metrics import max_drawdown, sharpe_ratio, sortino_ratio, win_rate
from src.core.io import write_parquet
from src.core.utils import ensure_directory, get_logger

logger = get_logger(__name__)


def summarize_backtest(
    portfolio: pd.DataFrame,
    trades: pd.DataFrame,
    out_dir: Path,
    strategy_name: str,
) -> Dict:
    ensure_directory(out_dir)

    portfolio["cum_return"] = (1 + portfolio["daily_return"].fillna(0.0)).cumprod()

    pnl_by_regime = {}
    if "regime_label" in portfolio.columns:
        pnl_by_regime = (
            portfolio.groupby("regime_label")["daily_return"].sum().to_dict()
        )

    summary = {
        "strategy_name": strategy_name,
        "start_date": str(portfolio["date"].min()),
        "end_date": str(portfolio["date"].max()),
        "sharpe": float(sharpe_ratio(portfolio["daily_return"].fillna(0.0))),
        "sortino": float(sortino_ratio(portfolio["daily_return"].fillna(0.0))),
        "max_drawdown": float(max_drawdown(portfolio["cum_return"])),
        "win_rate": float(win_rate(portfolio["daily_return"].fillna(0.0))),
        "num_trades": int(len(trades)),
        "pnl_by_regime": pnl_by_regime,
    }

    write_parquet(portfolio, out_dir / "pnl_timeseries.parquet")
    write_parquet(trades, out_dir / "trades.parquet")
    with (out_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Backtest summary written to {out_dir}/summary.json")
    return summary


__all__ = ["summarize_backtest"]
