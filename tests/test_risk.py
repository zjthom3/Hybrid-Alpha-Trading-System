import pandas as pd

from src.risk.position_sizing import compute_positions


def test_compute_positions_scales_and_clips():
    alpha = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "ticker": ["TST", "TST"],
            "alpha_score": [0.5, 2.0],
        }
    )
    vol = pd.Series([0.25, 0.05], index=alpha["date"])

    positions = compute_positions(alpha, vol, target_vol=0.1, max_weight=0.2)
    # First: 0.5 * 0.1 / 0.25 = 0.2 (clip at max)
    assert positions.loc[0, "target_weight"] == 0.2
    # Second would be > max_weight; must be clipped
    assert positions.loc[1, "target_weight"] == 0.2
    assert positions["max_weight_applied"].iloc[1]
