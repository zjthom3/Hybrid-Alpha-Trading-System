import pandas as pd

import json
from pathlib import Path

from src.backtest.engine import run_backtest
from src.backtest.metrics import max_drawdown, sharpe_ratio, sortino_ratio, win_rate
from src.backtest.reports import summarize_backtest


def test_backtest_engine_simple():
    prices = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "ticker": ["TST", "TST", "TST"],
            "close": [100, 101, 103],
        }
    )
    positions = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "ticker": ["TST", "TST"],
            "target_weight": [1.0, 1.0],
            "strategy_name": ["demo", "demo"],
        }
    )
    portfolio, trades = run_backtest(prices, positions, strategy_name="demo")
    # Two days with forward returns: (101/100-1)=0.01 and (103/101-1)=0.0198; first day PnL realized on next day
    assert abs(portfolio["daily_return"].iloc[1] - 0.01) < 1e-6


def test_metrics_functions():
    returns = pd.Series([0.01, -0.02, 0.03, 0.0])
    assert max_drawdown((1 + returns).cumprod()) <= 0
    assert sharpe_ratio(returns) != 0
    assert sortino_ratio(returns) != 0
    assert win_rate(returns) == 0.5


def test_summarize_backtest_with_regime(tmp_path):
    portfolio = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03"],
            "daily_return": [0.01, -0.02],
            "gross_exposure": [1.0, 1.0],
            "net_exposure": [1.0, 1.0],
            "strategy_name": ["demo", "demo"],
            "regime_label": ["bull", "bear"],
        }
    )
    trades = pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03"],
            "ticker": ["TST", "TST"],
            "strategy_name": ["demo", "demo"],
            "target_weight": [1.0, 1.0],
            "ret_1d_fwd": [0.01, -0.02],
            "pnl": [0.01, -0.02],
            "regime_label": ["bull", "bear"],
        }
    )
    summary = summarize_backtest(portfolio, trades, out_dir=tmp_path, strategy_name="demo")
    with (tmp_path / "summary.json").open() as f:
        saved = json.load(f)
    assert "pnl_by_regime" in summary
    assert "bull" in saved["pnl_by_regime"]
