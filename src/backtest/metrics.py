"""
Backtest metrics: Sharpe, Sortino, max drawdown, win rate.
"""

import numpy as np
import pandas as pd

from src.risk.risk_metrics import drawdown


def sharpe_ratio(returns: pd.Series, risk_free: float = 0.0, periods_per_year: int = 252) -> float:
    excess = returns - risk_free / periods_per_year
    if excess.std() == 0 or len(excess) == 0:
        return 0.0
    return np.sqrt(periods_per_year) * excess.mean() / excess.std()


def sortino_ratio(returns: pd.Series, risk_free: float = 0.0, periods_per_year: int = 252) -> float:
    excess = returns - risk_free / periods_per_year
    downside = excess[excess < 0]
    if downside.std() == 0 or len(downside) == 0:
        return 0.0
    return np.sqrt(periods_per_year) * excess.mean() / downside.std()


def max_drawdown(series: pd.Series) -> float:
    dd = drawdown(series)
    return dd.min() if not dd.empty else 0.0


def win_rate(returns: pd.Series) -> float:
    if len(returns) == 0:
        return 0.0
    return (returns > 0).mean()


__all__ = ["sharpe_ratio", "sortino_ratio", "max_drawdown", "win_rate"]
