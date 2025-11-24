"""
Pipeline orchestrator for data preprocessing.
Loads raw OHLCV files, standardizes them, and writes processed bars to disk.
"""

import sys
from pathlib import Path
from typing import Iterable, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.utils import get_logger, load_config  # noqa: E402
from src.data.loaders import load_raw_ohlcv, save_processed_bars  # noqa: E402
from src.data.preprocessing import preprocess_ohlcv, validate_processed_schema  # noqa: E402

logger = get_logger(__name__)


def _unique_tickers(config: dict, tickers: Sequence[str] | None) -> List[str]:
    configured = list(config.get("tickers", []))
    benchmark = config.get("benchmark")
    if benchmark and benchmark not in configured:
        configured.append(benchmark)
    if tickers:
        configured = list(dict.fromkeys(list(tickers) + configured))
    return configured


def preprocess_data(
    tickers: Iterable[str] | None = None,
    settings_path: str | Path = "config/settings.yaml",
    data_sources_path: str | Path = "config/data_sources.yaml",
) -> List[Path]:
    """
    Run preprocessing for the provided tickers (defaults to config tickers + benchmark).

    Returns:
        List of paths written.
    """
    settings = load_config(settings_path)
    data_sources = load_config(data_sources_path)
    tickers_to_process = _unique_tickers(settings, tickers)

    written_paths: List[Path] = []
    for ticker in tickers_to_process:
        logger.info(f"Preprocessing ticker {ticker}")
        raw_df = load_raw_ohlcv(ticker, data_sources)
        processed = preprocess_ohlcv(raw_df, ticker)
        validate_processed_schema(processed)
        output_path = save_processed_bars(processed, ticker, data_sources)
        written_paths.append(output_path)
    return written_paths


if __name__ == "__main__":
    preprocess_data()
