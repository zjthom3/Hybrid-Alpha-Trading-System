"""
Position sizing based on alpha_score and realized volatility.
"""

import numpy as np
import pandas as pd

from src.meta.meta_utils import clamp


def compute_positions(
    alpha_scores: pd.DataFrame,
    realized_vol: pd.Series,
    target_vol: float,
    max_weight: float,
) -> pd.DataFrame:
    df = alpha_scores.copy()
    df = df.merge(realized_vol.rename("realized_vol_lookback"), left_on="date", right_index=True, how="left")

    vol = df["realized_vol_lookback"].replace(0, np.nan)
    scaling = target_vol / vol
    scaled = df["alpha_score"] * scaling
    df["target_weight"] = clamp(scaled, -max_weight, max_weight).fillna(0.0)
    df["max_weight_applied"] = (df["target_weight"].abs() >= max_weight).astype(bool)
    df["strategy_name"] = df.get("strategy_name", "hybrid_alpha_mvp")

    return df[
        [
            "date",
            "ticker",
            "strategy_name",
            "target_weight",
            "realized_vol_lookback",
            "max_weight_applied",
        ]
    ]


__all__ = ["compute_positions"]
