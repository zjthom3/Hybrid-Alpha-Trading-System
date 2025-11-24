"""
Shared type aliases and typed structures used across the Hybrid Alpha Trading System.
Keeping these in one place ensures consistent schemas between modules.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Optional, TypedDict

import pandas as pd

# Core aliases for convenience
DataFrame = pd.DataFrame
Series = pd.Series


class Bar(TypedDict):
    date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: float
    ticker: str


class FeatureRow(TypedDict, total=False):
    date: date
    ticker: str
    ret_1d: float
    ret_5d: float
    ret_20d: float
    sma_10: float
    sma_20: float
    sma_50: float
    sma_200: float
    dist_to_sma_20: float
    dist_to_sma_50: float
    dist_to_sma_200: float
    momentum_20: float
    realized_vol_10: float
    realized_vol_20: float
    realized_vol_60: float
    atr_14: float
    intraday_range_pct: float
    volume_z_20: float
    volume_to_20d_avg: float
    rel_ret_vs_benchmark_20: float
    rel_ret_vs_benchmark_60: float
    beta_vs_benchmark_60: float


class SignalRow(TypedDict, total=False):
    date: date
    ticker: str
    trend_alpha: float
    mean_reversion_alpha: float
    vol_alpha: float
    rel_strength_alpha: float


class PredictionRow(TypedDict, total=False):
    date: date
    ticker: str
    horizon: int
    model_name: str
    pred_state: int
    prob_pred_state: float
    prob_state_m2: float
    prob_state_m1: float
    prob_state_0: float
    prob_state_p1: float
    prob_state_p2: float
    prob_state_p3: float


class RegimeRow(TypedDict, total=False):
    date: date
    benchmark: str
    regime_label: str
    regime_id: int
    regime_prob_bull: float
    regime_prob_bear: float
    regime_prob_choppy: float
    regime_prob_crash: float


class AlphaScoreRow(TypedDict, total=False):
    date: date
    ticker: str
    alpha_score: float
    alpha_confidence: float
    contrib_trend: float
    contrib_mean_rev: float
    contrib_vol: float
    contrib_rel_strength: float
    contrib_ml: float
    regime_label: str


@dataclass
class Position:
    date: date
    ticker: str
    strategy_name: str
    target_weight: float
    target_dollar_pos: Optional[float] = None
    realized_vol_lookback: Optional[float] = None
    max_weight_applied: Optional[bool] = None


@dataclass
class Trade:
    datetime: datetime
    ticker: str
    strategy_name: str
    side: str
    quantity: float
    price: float
    notional: float
    fees: float = 0.0
    reason: Optional[str] = None


@dataclass
class BacktestResult:
    strategy_name: str
    start_date: date
    end_date: date
    sharpe: float
    sortino: float
    max_drawdown: float
    cagr: Optional[float] = None
    win_rate: Optional[float] = None
    num_trades: Optional[int] = None
    pnl_by_regime: Optional[Dict[str, float]] = None


__all__ = [
    "DataFrame",
    "Series",
    "Bar",
    "FeatureRow",
    "SignalRow",
    "PredictionRow",
    "RegimeRow",
    "AlphaScoreRow",
    "Position",
    "Trade",
    "BacktestResult",
]
