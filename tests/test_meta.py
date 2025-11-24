import pandas as pd

from src.meta.rule_based_meta import combine_signals


def test_combine_signals_applies_regime_weights():
    signals = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "ticker": ["TST", "TST"],
            "trend_alpha": [0.5, -0.5],
            "mean_reversion_alpha": [0.0, 0.0],
            "vol_alpha": [0.0, 0.0],
            "rel_strength_alpha": [0.0, 0.0],
        }
    )
    preds = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "ticker": ["TST", "TST"],
            "horizon": [1, 1],
            "prob_state_p1": [0.6, 0.1],
            "prob_state_p2": [0.0, 0.0],
            "prob_state_p3": [0.0, 0.0],
            "prob_state_m1": [0.1, 0.6],
            "prob_state_m2": [0.0, 0.0],
            "prob_state_m3": [0.0, 0.0],
        }
    )
    regimes = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "regime_label": ["bull", "bear"],
        }
    )
    weights = {
        "bull": {"trend_alpha": 0.5, "mean_reversion_alpha": 0.1, "vol_alpha": 0.1, "rel_strength_alpha": 0.1, "ml": 0.4},
        "bear": {"trend_alpha": 0.2, "mean_reversion_alpha": 0.4, "vol_alpha": 0.3, "rel_strength_alpha": 0.2, "ml": 0.4},
    }

    alpha = combine_signals(signals, preds, regimes, weights, horizon=1)
    # In bull: trend 0.5*0.5 = 0.25; ml_signal ~0.5*0.4=0.2 -> positive alpha
    assert alpha.loc[0, "alpha_score"] > 0
    # In bear: trend negative with lower weight, ml negative -> should be negative alpha
    assert alpha.loc[1, "alpha_score"] < 0
