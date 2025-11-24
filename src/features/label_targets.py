"""
Helper to derive discrete target states from future returns for multiple horizons.
"""

from typing import Dict, Iterable, List

import numpy as np
import pandas as pd

from src.core.types import DataFrame


def _bucket_return(ret: float, thresholds: Dict[str, float]) -> int:
    """
    Map return into discrete states using thresholds.
    thresholds expects keys: neg3, neg2, neg1, pos1, pos2, pos3 (symmetric by default).
    """
    if np.isnan(ret):
        return 0
    neg3, neg2, neg1 = thresholds["neg3"], thresholds["neg2"], thresholds["neg1"]
    pos1, pos2, pos3 = thresholds["pos1"], thresholds["pos2"], thresholds["pos3"]
    if ret <= neg3:
        return -3
    if ret <= neg2:
        return -2
    if ret <= neg1:
        return -1
    if ret >= pos3:
        return 3
    if ret >= pos2:
        return 2
    if ret >= pos1:
        return 1
    return 0


def _default_thresholds() -> Dict[str, float]:
    return {
        "neg3": -0.05,
        "neg2": -0.03,
        "neg1": -0.01,
        "pos1": 0.01,
        "pos2": 0.03,
        "pos3": 0.05,
    }


def label_future_states(
    features: DataFrame,
    horizons: Iterable[int],
    thresholds: Dict[str, float] | None = None,
) -> DataFrame:
    """
    Add discrete target state labels for each horizon based on future returns.
    """
    thresholds = thresholds or _default_thresholds()
    df = features.copy()
    close = df["close"]
    for h in horizons:
        future_ret = (close.shift(-h) / close - 1.0)
        df[f"target_state_h{h}"] = future_ret.apply(lambda r: _bucket_return(r, thresholds))
    return df


__all__ = ["label_future_states", "_default_thresholds"]
