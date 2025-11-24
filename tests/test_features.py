import pandas as pd
import numpy as np
import yaml

from src.features.trend_features import build_trend_features
from src.features.volatility_features import build_volatility_features
from src.features.volume_features import build_volume_features
from src.pipeline.build_features import build_features


def test_trend_features_basic():
    bars = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=4, freq="D").date,
            "open": [1, 2, 3, 4],
            "high": [1, 2, 3, 4],
            "low": [1, 2, 3, 4],
            "close": [1, 2, 3, 4],
            "adj_close": [1, 2, 3, 4],
            "volume": [100, 100, 100, 100],
            "ticker": ["TEST"] * 4,
            "realized_vol_2": [np.nan, 0.1, 0.1, 0.1],
        }
    )
    feats = build_trend_features(bars, {"sma": [2], "returns": [1, 2]})
    assert "ret_1d" in feats.columns
    assert feats.loc[2, "ret_1d"] == 0.5  # (3-2)/2
    assert "sma_2" in feats.columns
    assert feats.loc[3, "sma_2"] == 3.5
    assert "dist_to_sma_2" in feats.columns


def test_volatility_and_volume_features():
    bars = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=3, freq="D").date,
            "open": [100, 102, 101],
            "high": [102, 103, 102],
            "low": [99, 100, 99],
            "close": [101, 102, 101],
            "adj_close": [101, 102, 101],
            "volume": [10, 20, 30],
            "ticker": ["TEST"] * 3,
        }
    )
    vol_feats = build_volatility_features(bars, realized_vol_windows=[2], atr_period=2)
    assert "realized_vol_2" in vol_feats.columns
    assert "intraday_range_pct" in vol_feats.columns
    assert vol_feats["intraday_range_pct"].iloc[1] == (103 - 100) / 102

    vol_feats = vol_feats.merge(build_volume_features(bars, lookback=2), on=["date", "ticker"])
    assert "volume_z_2" in vol_feats.columns
    # Last z-score should be positive
    assert vol_feats["volume_z_2"].iloc[-1] > 0


def test_feature_pipeline_integration(tmp_path):
    data_root = tmp_path / "data"
    processed_dir = data_root / "processed"
    features_dir = data_root / "features"
    processed_dir.mkdir(parents=True)
    features_dir.mkdir(parents=True)

    # Minimal processed bars for ticker and benchmark
    dates = pd.date_range("2024-01-01", periods=10, freq="D").date
    def make_df(ticker, base):
        return pd.DataFrame(
            {
                "date": dates,
                "open": base + np.arange(10),
                "high": base + np.arange(10) + 1,
                "low": base + np.arange(10) - 1,
                "close": base + np.arange(10),
                "adj_close": base + np.arange(10),
                "volume": 1_000_000 + 10_000 * np.arange(10),
                "ticker": [ticker] * 10,
            }
        )

    make_df("TST", 100).to_parquet(processed_dir / "TST.parquet", index=False)
    make_df("BMK", 200).to_parquet(processed_dir / "BMK.parquet", index=False)

    settings_path = tmp_path / "settings.yaml"
    yaml.safe_dump(
        {
            "tickers": ["TST"],
            "benchmark": "BMK",
            "features": {
                "lookbacks": {"sma": [2], "returns": [1, 2], "realized_vol": [2]},
                "atr_period": 2,
                "volume_lookback": 2,
            },
            "paths": {"features_dir": str(features_dir)},
        },
        settings_path.open("w"),
    )

    data_sources_path = tmp_path / "data_sources.yaml"
    yaml.safe_dump(
        {
            "data_root": str(data_root),
            "processed_files": {"pattern": "{ticker}.parquet", "directory": "processed"},
        },
        data_sources_path.open("w"),
    )

    written_paths = build_features(
        tickers=["TST"],
        settings_path=settings_path,
        data_sources_path=data_sources_path,
    )
    assert written_paths
    output_path = next(p for p in written_paths if p.name.startswith("TST"))
    df = pd.read_parquet(output_path)
    expected_cols = {"ret_1d", "sma_2", "dist_to_sma_2", "realized_vol_2", "volume_z_2", "rel_ret_vs_benchmark_20"}
    assert expected_cols.issubset(set(df.columns))
    # Returns should be numeric and not all NaN after sufficient history
    assert df["ret_1d"].dropna().shape[0] > 0
