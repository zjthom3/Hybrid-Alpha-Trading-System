"""
Pipeline to compute position sizes from alpha scores and realized volatility.
"""

import sys
from pathlib import Path
from typing import Iterable, List

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.io import read_parquet, write_parquet  # noqa: E402
from src.core.utils import ensure_directory, get_logger, load_config  # noqa: E402
from src.risk.position_sizing import compute_positions  # noqa: E402

logger = get_logger(__name__)


def run_position_sizing(
    tickers: Iterable[str] | None = None,
    settings_path: str | Path = "config/settings.yaml",
    data_sources_path: str | Path = "config/data_sources.yaml",
) -> List[Path]:
    settings = load_config(settings_path)
    data_sources = load_config(data_sources_path)

    tickers_to_process: List[str] = list(settings.get("tickers", []))
    if tickers:
        tickers_to_process = list(dict.fromkeys(list(tickers) + tickers_to_process))

    paths_cfg = settings.get("paths", {})
    alpha_dir = Path(paths_cfg.get("alpha_scores_dir", "data/meta/alpha_scores"))
    features_dir = Path(paths_cfg.get("features_dir", "data/features"))
    positions_root = Path(paths_cfg.get("positions_dir", "data/positions"))

    strategy_name = settings.get("backtest", {}).get("strategy_name", "hybrid_alpha_mvp")
    positions_dir = positions_root / strategy_name
    ensure_directory(positions_dir)

    target_vol = settings.get("risk", {}).get("target_vol", 0.15)
    max_weight = settings.get("risk", {}).get("max_weight", 0.1)

    written: List[Path] = []
    for ticker in tickers_to_process:
        alpha_path = alpha_dir / f"{ticker}.parquet"
        feats_path = features_dir / f"{ticker}.parquet"
        if not alpha_path.exists() or not feats_path.exists():
            raise FileNotFoundError(f"Alpha or features missing for {ticker}")

        alpha = read_parquet(alpha_path)
        feats = read_parquet(feats_path)
        if "ret_1d" not in feats:
            feats["ret_1d"] = feats["close"].pct_change()
        vol = feats["ret_1d"].rolling(window=20, min_periods=20).std() * (252 ** 0.5)
        vol.index = feats["date"]

        positions = compute_positions(alpha, vol, target_vol=target_vol, max_weight=max_weight)
        positions["strategy_name"] = strategy_name
        out_path = positions_dir / f"{ticker}.parquet"
        write_parquet(positions, out_path)
        written.append(out_path)
        logger.info(f"Wrote positions for {ticker} to {out_path}")

    return written


if __name__ == "__main__":
    run_position_sizing()
