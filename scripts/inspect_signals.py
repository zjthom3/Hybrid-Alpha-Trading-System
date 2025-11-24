"""
Inspect signals/alpha scores for a given ticker and optional date range.

Usage:
    python scripts/inspect_signals.py --ticker SPY --start 2024-01-01 --end 2024-03-01
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core.utils import get_logger, load_config  # noqa: E402

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect signals/alpha scores for a ticker.")
    parser.add_argument("--ticker", required=True, help="Ticker symbol to inspect")
    parser.add_argument("--config", default="config/settings.yaml", help="Path to settings.yaml")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--alpha", action="store_true", help="Inspect alpha scores instead of raw signals")
    return parser.parse_args()


def load_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def main():
    args = parse_args()
    cfg = load_config(args.config)
    paths = cfg.get("paths", {})

    if args.alpha:
        base_dir = Path(paths.get("alpha_scores_dir", "data/meta/alpha_scores"))
        path = base_dir / f"{args.ticker}.parquet"
    else:
        base_dir = Path(paths.get("signals_dir", "data/signals"))
        path = base_dir / f"{args.ticker}.parquet"

    df = load_table(path)
    if args.start:
        df = df[df["date"] >= args.start]
    if args.end:
        df = df[df["date"] <= args.end]

    print(df.head(20))


if __name__ == "__main__":
    main()
