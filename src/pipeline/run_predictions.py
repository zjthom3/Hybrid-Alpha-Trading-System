"""
Pipeline to run predictions using trained LightGBM models and persist to data/predictions/.
"""

import sys
from pathlib import Path
from typing import Iterable, List

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models.ml.lightgbm_next_state import load_trained_model, predict_proba  # noqa: E402
from models.ml.model_registry import ModelKey  # noqa: E402
from src.core.io import read_parquet, write_parquet  # noqa: E402
from src.core.utils import ensure_directory, get_logger, load_config  # noqa: E402

logger = get_logger(__name__)


def run_predictions(
    tickers: Iterable[str] | None = None,
    settings_path: str | Path = "config/settings.yaml",
    data_sources_path: str | Path = "config/data_sources.yaml",
) -> List[Path]:
    settings = load_config(settings_path)
    data_sources = load_config(data_sources_path)

    tickers_to_process: List[str] = list(settings.get("tickers", []))
    if tickers:
        tickers_to_process = list(dict.fromkeys(list(tickers) + tickers_to_process))

    features_dir = Path(settings.get("paths", {}).get("features_dir", "data/features"))
    preds_dir = Path(settings.get("paths", {}).get("predictions_dir", "data/predictions"))
    ensure_directory(preds_dir)

    horizons = settings.get("ml", {}).get("horizons", [1, 3, 5])
    model_name = settings.get("ml", {}).get("model_name", "lightgbm_v1")
    artifacts_dir = Path("models/ml/artifacts")

    written: List[Path] = []
    for ticker in tickers_to_process:
        feats_path = features_dir / f"{ticker}.parquet"
        if not feats_path.exists():
            raise FileNotFoundError(f"Features file not found for {ticker}: {feats_path}")
        feats = read_parquet(feats_path)

        preds_rows = []
        for h in horizons:
            key = ModelKey(model_name=model_name, ticker=ticker, horizon=h, version="v1")
            trained = load_trained_model(str(artifacts_dir), key)
            # Align feature columns
            X = feats.copy()
            missing_cols = [c for c in trained.feature_columns if c not in X.columns]
            for c in missing_cols:
                X[c] = 0.0
            X = X[trained.feature_columns]

            proba = predict_proba(trained.model, trained.scaler, X, trained.feature_columns)
            classes = trained.classes_
            # For each row, find pred_state and prob_pred_state
            for dt, row_proba in zip(feats["date"], proba):
                pred_idx = row_proba.argmax()
                pred_state = classes[pred_idx]
                preds_rows.append(
                    {
                        "date": dt,
                        "ticker": ticker,
                        "horizon": h,
                        "model_name": model_name,
                        "pred_state": int(pred_state),
                        "prob_pred_state": float(row_proba[pred_idx]),
                        "prob_state_m3": float(row_proba[classes.tolist().index(-3)]) if -3 in classes else None,
                        "prob_state_m2": float(row_proba[classes.tolist().index(-2)]) if -2 in classes else None,
                        "prob_state_m1": float(row_proba[classes.tolist().index(-1)]) if -1 in classes else None,
                        "prob_state_0": float(row_proba[classes.tolist().index(0)]) if 0 in classes else None,
                        "prob_state_p1": float(row_proba[classes.tolist().index(1)]) if 1 in classes else None,
                        "prob_state_p2": float(row_proba[classes.tolist().index(2)]) if 2 in classes else None,
                        "prob_state_p3": float(row_proba[classes.tolist().index(3)]) if 3 in classes else None,
                    }
                )

        preds_df = pd.DataFrame(preds_rows)
        out_path = preds_dir / f"{ticker}.parquet"
        write_parquet(preds_df, out_path)
        written.append(out_path)
        logger.info(f"Wrote predictions for {ticker} to {out_path}")

    return written


if __name__ == "__main__":
    run_predictions()
