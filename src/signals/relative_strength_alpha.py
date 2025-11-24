"""
Relative strength alpha: favors assets outperforming the benchmark.
Outputs a score in [-1, 1] based on relative returns.
"""

import pandas as pd

from src.core.types import DataFrame


def compute_relative_strength_alpha(
    features: DataFrame,
    lookback: int = 20,
    scale: float = 0.1,
) -> pd.Series:
    col = f"rel_ret_vs_benchmark_{lookback}"
    if col not in features:
        raise KeyError(f"Missing relative return column {col} for relative strength alpha")

    rel_ret = features[col]
    score = rel_ret / scale
    score = score.clip(-1.0, 1.0)
    return score.fillna(0.0)


__all__ = ["compute_relative_strength_alpha"]
