"""
Pipeline to combine signals, predictions, and regimes into alpha scores.
"""

import sys
from pathlib import Path
from typing import Iterable, List

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.io import read_parquet, write_parquet  # noqa: E402
from src.core.utils import ensure_directory, get_logger, load_config  # noqa: E402
from src.meta.rule_based_meta import combine_signals  # noqa: E402

logger = get_logger(__name__)


def run_meta_model(
    tickers: Iterable[str] | None = None,
    settings_path: str | Path = "config/settings.yaml",
    regimes_config_path: str | Path = "config/regimes.yaml",
) -> List[Path]:
    settings = load_config(settings_path)
    regimes_cfg = load_config(regimes_config_path)

    tickers_to_process: List[str] = list(settings.get("tickers", []))
    if tickers:
        tickers_to_process = list(dict.fromkeys(list(tickers) + tickers_to_process))

    paths_cfg = settings.get("paths", {})
    signals_dir = Path(paths_cfg.get("signals_dir", "data/signals"))
    preds_dir = Path(paths_cfg.get("predictions_dir", "data/predictions"))
    regimes_dir = Path(paths_cfg.get("regimes_dir", "data/regimes"))
    alpha_dir = Path(paths_cfg.get("alpha_scores_dir", "data/meta/alpha_scores"))
    ensure_directory(alpha_dir)

    horizon = settings.get("ml", {}).get("horizons", [1])[0]
    weights = regimes_cfg.get("weights", {})
    benchmark = settings.get("benchmark")
    regime_path = regimes_dir / f"{benchmark}.parquet"
    if not regime_path.exists():
        raise FileNotFoundError(f"Regime file not found: {regime_path}")
    regimes = read_parquet(regime_path)

    written: List[Path] = []
    for ticker in tickers_to_process:
        signals_path = signals_dir / f"{ticker}.parquet"
        preds_path = preds_dir / f"{ticker}.parquet"
        if not signals_path.exists() or not preds_path.exists():
            raise FileNotFoundError(f"Signals or predictions missing for {ticker}")

        signals = read_parquet(signals_path)
        preds = read_parquet(preds_path)
        alpha_df = combine_signals(signals, preds, regimes, weights=weights, horizon=horizon)
        out_path = alpha_dir / f"{ticker}.parquet"
        write_parquet(alpha_df, out_path)
        written.append(out_path)
        logger.info(f"Wrote alpha scores for {ticker} to {out_path}")

    return written


if __name__ == "__main__":
    run_meta_model()
