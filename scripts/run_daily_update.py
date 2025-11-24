"""
Daily update pipeline (assumes models already trained and raw data up to date).

Usage:
    python scripts/run_daily_update.py --config config/settings.yaml
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.pipeline.preprocess_data import preprocess_data  # noqa: E402
from src.pipeline.build_features import build_features  # noqa: E402
from src.pipeline.build_signals import build_signals  # noqa: E402
from src.pipeline.run_regime_engine import run_regime_engine  # noqa: E402
from src.pipeline.run_predictions import run_predictions  # noqa: E402
from src.pipeline.run_meta_model import run_meta_model  # noqa: E402
from src.pipeline.run_position_sizing import run_position_sizing  # noqa: E402
from src.core.utils import get_logger  # noqa: E402

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run daily update pipeline.")
    parser.add_argument("--config", default="config/settings.yaml", help="Path to settings.yaml")
    parser.add_argument("--data-sources", default="config/data_sources.yaml", help="Path to data_sources.yaml")
    parser.add_argument("--regimes", default="config/regimes.yaml", help="Path to regimes.yaml")
    return parser.parse_args()


def main():
    args = parse_args()
    logger.info("Starting daily update pipeline")
    preprocess_data(settings_path=args.config, data_sources_path=args.data_sources)
    build_features(settings_path=args.config, data_sources_path=args.data_sources)
    build_signals(settings_path=args.config, data_sources_path=args.data_sources)
    run_regime_engine(settings_path=args.config, data_sources_path=args.data_sources, regimes_config_path=args.regimes)
    run_predictions(settings_path=args.config, data_sources_path=args.data_sources)
    run_meta_model(settings_path=args.config, regimes_config_path=args.regimes)
    run_position_sizing(settings_path=args.config, data_sources_path=args.data_sources)
    logger.info("Daily update pipeline completed")


if __name__ == "__main__":
    main()
