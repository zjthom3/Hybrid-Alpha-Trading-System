"""
Feature pipeline: load processed bars, compute feature sets, and persist to data/features/.
"""

import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.io import read_parquet, write_parquet  # noqa: E402
from src.core.utils import ensure_directory, get_logger, load_config  # noqa: E402
from src.data.preprocessing import CANONICAL_COLUMNS  # noqa: E402
from src.features.relative_strength_features import build_relative_strength_features  # noqa: E402
from src.features.trend_features import build_trend_features  # noqa: E402
from src.features.volatility_features import build_volatility_features  # noqa: E402
from src.features.volume_features import build_volume_features  # noqa: E402

logger = get_logger(__name__)


def _resolve_path(directory: str, pattern: str, ticker: str, data_root: str | None) -> Path:
    base_dir = Path(directory)
    if not base_dir.is_absolute() and data_root:
        root = Path(data_root)
        if base_dir.parts and base_dir.parts[0] == root.name:
            base_dir = root / Path(*base_dir.parts[1:])
        else:
            base_dir = root / base_dir
    ensure_directory(base_dir)
    return base_dir / pattern.format(ticker=ticker)


def _load_processed_bars(
    ticker: str,
    data_sources: Dict,
) -> pd.DataFrame:
    proc_cfg = data_sources.get("processed_files", {})
    pattern = proc_cfg.get("pattern", "{ticker}.parquet")
    directory = proc_cfg.get("directory", "data/processed")
    data_root = data_sources.get("data_root")
    path = _resolve_path(directory, pattern, ticker, data_root)
    if not path.exists():
        raise FileNotFoundError(f"Processed bars not found for {ticker}: {path}")
    df = read_parquet(path)
    missing = [c for c in CANONICAL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Processed bars for {ticker} missing columns: {missing}")
    return df


def _build_base_features(bars: pd.DataFrame, feature_cfg: Dict) -> pd.DataFrame:
    lookbacks = feature_cfg.get("lookbacks", {})
    realized_vol = lookbacks.get("realized_vol", [])
    atr_period = feature_cfg.get("atr_period", 14)
    volume_lookback = feature_cfg.get("volume_lookback", 20)

    vol_df = build_volatility_features(bars, realized_vol_windows=list(realized_vol), atr_period=atr_period)
    bars_for_trend = bars.merge(vol_df, on=["date", "ticker"], how="left")
    trend_df = build_trend_features(bars_for_trend, lookbacks=lookbacks)
    volume_df = build_volume_features(bars, lookback=volume_lookback)

    # Keep price columns for downstream signals that need them
    features = bars[["date", "ticker", "close"]].copy()
    for df in [trend_df, vol_df, volume_df]:
        features = features.merge(df, on=["date", "ticker"], how="left")
    return features


def build_features(
    tickers: Iterable[str] | None = None,
    settings_path: str | Path = "config/settings.yaml",
    data_sources_path: str | Path = "config/data_sources.yaml",
) -> List[Path]:
    """
    Build features for configured tickers (defaults to config tickers) and save to data/features/.
    """
    settings = load_config(settings_path)
    data_sources = load_config(data_sources_path)
    feature_cfg = settings.get("features", {})

    tickers_to_process: List[str] = list(settings.get("tickers", []))
    if tickers:
        tickers_to_process = list(dict.fromkeys(list(tickers) + tickers_to_process))

    benchmark = settings.get("benchmark")
    if benchmark and benchmark not in tickers_to_process:
        tickers_to_process.append(benchmark)

    logger.info(f"Building features for tickers: {tickers_to_process}")

    # Load processed bars
    processed_cache: Dict[str, pd.DataFrame] = {}
    for t in tickers_to_process:
        processed_cache[t] = _load_processed_bars(t, data_sources)

    # Precompute benchmark base features for relative strength
    if not benchmark:
        raise ValueError("Benchmark must be set in settings.yaml to compute relative strength features.")
    benchmark_base = _build_base_features(processed_cache[benchmark], feature_cfg)

    written_paths: List[Path] = []
    features_dir = Path(settings.get("paths", {}).get("features_dir", "data/features"))
    ensure_directory(features_dir)

    for ticker in tickers_to_process:
        bars = processed_cache[ticker]
        base_features = _build_base_features(bars, feature_cfg)

        # Relative strength features need returns present
        ret_lookbacks = feature_cfg.get("lookbacks", {}).get("returns", [])
        rel_lookbacks = [lb for lb in [20, 60] if lb in ret_lookbacks]
        rs_df = build_relative_strength_features(
            ticker_features=base_features,
            benchmark_features=benchmark_base,
            lookbacks=rel_lookbacks,
            beta_window=60,
        )
        features_df = base_features.merge(rs_df, on=["date", "ticker"], how="left")

        # Save
        output_path = features_dir / f"{ticker}.parquet"
        write_parquet(features_df, output_path)
        written_paths.append(output_path)
        logger.info(f"Wrote features for {ticker} to {output_path}")

    return written_paths


if __name__ == "__main__":
    build_features()
