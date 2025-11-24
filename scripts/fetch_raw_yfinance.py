"""
Fetch historical OHLCV for configured tickers using yfinance and write to data/raw/.
Defaults to 5 years; falls back to max if not available.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.utils import get_logger, load_config  # noqa: E402
from src.data.yfinance_fetch import fetch_and_save_raw  # noqa: E402

logger = get_logger(__name__)


def main():
    settings = load_config("config/settings.yaml")
    data_sources = load_config("config/data_sources.yaml")

    tickers = list(settings.get("tickers", []))
    benchmark = settings.get("benchmark")
    if benchmark and benchmark not in tickers:
        tickers.append(benchmark)

    written = fetch_and_save_raw(tickers, data_sources_config=data_sources, period="5y")
    logger.info(f"Wrote raw files: {written}")


if __name__ == "__main__":
    main()
