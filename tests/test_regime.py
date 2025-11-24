import pandas as pd

from models.regime.rule_based_regime import assign_regime


def test_rule_based_regime_labels_trend_and_crash():
    dates = pd.date_range("2024-01-01", periods=250, freq="D").date
    # Build an uptrend then sharp drop
    prices = list(range(100, 225)) + list(range(224, 174, -1)) + [150] * 25
    df = pd.DataFrame(
        {
            "date": dates[:len(prices)],
            "open": prices,
            "high": prices,
            "low": prices,
            "close": prices,
            "adj_close": prices,
            "volume": [1_000_000] * len(prices),
            "ticker": ["BMK"] * len(prices),
        }
    )
    regimes = assign_regime(
        df,
        trend_ma_short=20,
        trend_ma_long=50,
        vol_lookback=20,
        high_vol_zscore=1.5,
        crash_drawdown_threshold=-0.15,
    )
    assert "regime_label" in regimes
    # After long uptrend, should see bull
    assert "bull" in regimes["regime_label"].values
    # After drop, expect crash labels
    assert "crash" in regimes["regime_label"].values
