"""
Utility helpers for meta-model weighting.
"""

import pandas as pd


def clamp(series: pd.Series, lower: float = -1.0, upper: float = 1.0) -> pd.Series:
    return series.clip(lower, upper)


__all__ = ["clamp"]
