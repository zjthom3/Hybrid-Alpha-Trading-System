"""
Pipeline to build rule-based signals from features and persist to data/signals/.
"""

import sys
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.io import read_parquet, write_parquet  # noqa: E402
from src.core.utils import ensure_directory, get_logger, load_config  # noqa: E402
from src.signals.mean_reversion_alpha import compute_mean_reversion_alpha  # noqa: E402
from src.signals.relative_strength_alpha import compute_relative_strength_alpha  # noqa: E402
from src.signals.trend_alpha import compute_trend_alpha  # noqa: E402
from src.signals.volatility_alpha import compute_volatility_alpha  # noqa: E402

logger = get_logger(__name__)


def build_signals(
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
    signals_dir = Path(settings.get("paths", {}).get("signals_dir", "data/signals"))
    ensure_directory(signals_dir)

    written: List[Path] = []
    for ticker in tickers_to_process:
        feature_path = features_dir / f"{ticker}.parquet"
        if not feature_path.exists():
            raise FileNotFoundError(f"Features file not found for {ticker}: {feature_path}")

        feats = read_parquet(feature_path)
        feats["trend_alpha"] = compute_trend_alpha(feats)
        feats["mean_reversion_alpha"] = compute_mean_reversion_alpha(feats)
        feats["vol_alpha"] = compute_volatility_alpha(feats)
        feats["rel_strength_alpha"] = compute_relative_strength_alpha(feats)

        signals = feats[
            [
                "date",
                "ticker",
                "trend_alpha",
                "mean_reversion_alpha",
                "vol_alpha",
                "rel_strength_alpha",
            ]
        ]
        out_path = signals_dir / f"{ticker}.parquet"
        write_parquet(signals, out_path)
        written.append(out_path)
        logger.info(f"Wrote signals for {ticker} to {out_path}")

    return written


if __name__ == "__main__":
    build_signals()
