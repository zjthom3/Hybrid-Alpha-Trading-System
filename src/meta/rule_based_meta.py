"""
Combine rule-based signals, ML predictions, and regime weights into alpha_score.
"""

from pathlib import Path
from typing import Dict

import pandas as pd

from src.meta.meta_utils import clamp


def _ml_signal(predictions: pd.DataFrame, horizon: int = 1) -> pd.DataFrame:
    preds = predictions[predictions["horizon"] == horizon].copy()
    if preds.empty:
        preds["ml_signal"] = 0.0
        return preds[["date", "ticker", "ml_signal"]]

    def _sum_prob(row, keys):
        return sum(float(row[k]) for k in keys if k in row and pd.notna(row[k]))

    pos_keys = ["prob_state_p1", "prob_state_p2", "prob_state_p3"]
    neg_keys = ["prob_state_m1", "prob_state_m2", "prob_state_m3"]
    preds["ml_signal"] = preds.apply(lambda r: _sum_prob(r, pos_keys) - _sum_prob(r, neg_keys), axis=1)
    preds["ml_signal"] = clamp(preds["ml_signal"], -1.0, 1.0)
    return preds[["date", "ticker", "ml_signal"]]


def combine_signals(
    signals: pd.DataFrame,
    predictions: pd.DataFrame,
    regimes: pd.DataFrame,
    weights: Dict[str, Dict[str, float]],
    horizon: int = 1,
) -> pd.DataFrame:
    ml = _ml_signal(predictions, horizon=horizon)

    df = signals.merge(ml, on=["date", "ticker"], how="left")
    regimes_min = regimes[["date", "regime_label"]]
    df = df.merge(regimes_min, on="date", how="left")
    df["regime_label"] = df["regime_label"].fillna("choppy")

    contribs = {
        "contrib_trend": [],
        "contrib_mean_rev": [],
        "contrib_vol": [],
        "contrib_rel_strength": [],
        "contrib_ml": [],
    }
    alpha_scores = []

    for _, row in df.iterrows():
        regime = row["regime_label"]
        w = weights.get(regime, weights.get("choppy", {}))
        c_trend = row.get("trend_alpha", 0.0) * w.get("trend_alpha", 0.0)
        c_mean = row.get("mean_reversion_alpha", 0.0) * w.get("mean_reversion_alpha", 0.0)
        c_vol = row.get("vol_alpha", 0.0) * w.get("vol_alpha", 0.0)
        c_rel = row.get("rel_strength_alpha", 0.0) * w.get("rel_strength_alpha", 0.0)
        c_ml = row.get("ml_signal", 0.0) * w.get("ml", 0.0)
        contribs["contrib_trend"].append(c_trend)
        contribs["contrib_mean_rev"].append(c_mean)
        contribs["contrib_vol"].append(c_vol)
        contribs["contrib_rel_strength"].append(c_rel)
        contribs["contrib_ml"].append(c_ml)
        alpha_scores.append(c_trend + c_mean + c_vol + c_rel + c_ml)

    df["contrib_trend"] = contribs["contrib_trend"]
    df["contrib_mean_rev"] = contribs["contrib_mean_rev"]
    df["contrib_vol"] = contribs["contrib_vol"]
    df["contrib_rel_strength"] = contribs["contrib_rel_strength"]
    df["contrib_ml"] = contribs["contrib_ml"]

    df["alpha_score"] = clamp(pd.Series(alpha_scores), -1.0, 1.0)
    df["alpha_confidence"] = df["alpha_score"].abs()

    return df[
        [
            "date",
            "ticker",
            "alpha_score",
            "alpha_confidence",
            "contrib_trend",
            "contrib_mean_rev",
            "contrib_vol",
            "contrib_rel_strength",
            "contrib_ml",
            "regime_label",
        ]
    ]


__all__ = ["combine_signals"]
