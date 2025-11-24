"""
Pipeline to compute benchmark regimes using the rule-based engine and persist to data/regimes/.
"""

import sys
from pathlib import Path
from typing import List

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.io import read_parquet, write_parquet  # noqa: E402
from src.core.utils import ensure_directory, get_logger, load_config  # noqa: E402
from models.regime.rule_based_regime import assign_regime  # noqa: E402

logger = get_logger(__name__)


def _resolve_path(directory: str, pattern: str, ticker: str, data_root: str | None) -> Path:
    base_dir = Path(directory)
    if not base_dir.is_absolute() and data_root:
        root = Path(data_root)
        if base_dir.parts and base_dir.parts[0] == root.name:
            base_dir = root / Path(*base_dir.parts[1:])
        else:
            base_dir = root / base_dir
    return base_dir / pattern.format(ticker=ticker)


def run_regime_engine(
    settings_path: str | Path = "config/settings.yaml",
    data_sources_path: str | Path = "config/data_sources.yaml",
    regimes_config_path: str | Path = "config/regimes.yaml",
) -> List[Path]:
    settings = load_config(settings_path)
    data_sources = load_config(data_sources_path)
    regimes_cfg = load_config(regimes_config_path)

    benchmark = settings.get("benchmark")
    if not benchmark:
        raise ValueError("Benchmark must be set in settings.yaml")

    proc_cfg = data_sources.get("processed_files", {})
    pattern = proc_cfg.get("pattern", "{ticker}.parquet")
    directory = proc_cfg.get("directory", "data/processed")
    data_root = data_sources.get("data_root")
    proc_path = _resolve_path(directory, pattern, benchmark, data_root)

    if not proc_path.exists():
        raise FileNotFoundError(f"Processed benchmark file not found: {proc_path}")

    bars = read_parquet(proc_path)

    rules = regimes_cfg.get("rules", {})
    regimes_dir = Path(settings.get("paths", {}).get("regimes_dir", "data/regimes"))
    ensure_directory(regimes_dir)

    regime_df = assign_regime(
        bars,
        trend_ma_short=rules.get("trend_ma_short", 50),
        trend_ma_long=rules.get("trend_ma_long", 200),
        vol_lookback=rules.get("vol_lookback", 20),
        high_vol_zscore=rules.get("high_vol_zscore", 1.5),
        crash_drawdown_threshold=rules.get("crash_drawdown_threshold", -0.2),
    )

    out_path = regimes_dir / f"{benchmark}.parquet"
    write_parquet(regime_df, out_path)
    logger.info(f"Wrote regimes for {benchmark} to {out_path}")
    return [out_path]


if __name__ == "__main__":
    run_regime_engine()
