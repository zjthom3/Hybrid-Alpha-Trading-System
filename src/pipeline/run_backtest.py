"""
Pipeline to run backtest: loads prices and positions, executes engine, writes reports.
"""

import sys
from pathlib import Path
from typing import Iterable, List

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.backtest.engine import run_backtest  # noqa: E402
from src.backtest.reports import summarize_backtest  # noqa: E402
from src.core.io import read_parquet  # noqa: E402
from src.core.utils import ensure_directory, get_logger, load_config  # noqa: E402

logger = get_logger(__name__)


def run_backtest_pipeline(
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
    processed_dir = Path(paths_cfg.get("data_root", "data")) / "processed"
    positions_dir_root = Path(paths_cfg.get("positions_dir", "data/positions"))
    backtests_dir = Path(paths_cfg.get("backtests_dir", "data/backtests"))
    strategy_name = settings.get("backtest", {}).get("strategy_name", "hybrid_alpha_mvp")
    positions_dir = positions_dir_root / strategy_name
    out_dir = backtests_dir / strategy_name
    ensure_directory(out_dir)

    # Load regimes for benchmark if available
    benchmark = settings.get("benchmark")
    regimes_path = Path(paths_cfg.get("regimes_dir", "data/regimes")) / f"{benchmark}.parquet"
    regimes_df = None
    if regimes_path.exists():
        regimes_df = read_parquet(regimes_path)[["date", "regime_label"]]

    # Load prices and positions
    prices_list = []
    positions_list = []
    for t in tickers_to_process:
        prices_path = processed_dir / f"{t}.parquet"
        pos_path = positions_dir / f"{t}.parquet"
        if not prices_path.exists() or not pos_path.exists():
            raise FileNotFoundError(f"Missing prices or positions for {t}")
        prices_list.append(read_parquet(prices_path))
        positions_list.append(read_parquet(pos_path))
    prices_df = pd.concat(prices_list, ignore_index=True)
    positions_df = pd.concat(positions_list, ignore_index=True)

    portfolio, trades = run_backtest(prices_df, positions_df, strategy_name=strategy_name)
    if regimes_df is not None:
        portfolio = portfolio.merge(regimes_df, on="date", how="left")
        trades = trades.merge(regimes_df, left_on="date", right_on="date", how="left")

    summary = summarize_backtest(portfolio, trades, out_dir=out_dir, strategy_name=strategy_name)
    logger.info(f"Backtest complete: {summary}")
    return [out_dir / "summary.json", out_dir / "pnl_timeseries.parquet", out_dir / "trades.parquet"]


if __name__ == "__main__":
    run_backtest_pipeline()
