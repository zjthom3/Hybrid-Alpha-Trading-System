import pandas as pd
import yaml

from src.data.preprocessing import CANONICAL_COLUMNS, preprocess_ohlcv
from src.pipeline.preprocess_data import preprocess_data


def test_preprocess_ohlcv_enforces_schema_and_sorts():
    raw = pd.DataFrame(
        {
            "date": ["2024-01-03", "2024-01-01", "2024-01-01"],
            "open": [102, 100, 101],
            "high": [103, 101, 102],
            "low": [99, 98, 99],
            "close": [101, 100, 100.5],
            "volume": [1_000_000, 900_000, 950_000],
        }
    )

    processed = preprocess_ohlcv(raw, ticker="TEST")

    assert list(processed.columns) == CANONICAL_COLUMNS
    assert processed["ticker"].unique().tolist() == ["TEST"]
    # Duplicated date should be removed, last occurrence kept
    assert len(processed) == 2
    assert processed.iloc[0]["date"].isoformat() == "2024-01-01"
    assert processed.iloc[0]["adj_close"] == processed.iloc[0]["close"]
    assert processed["date"].is_monotonic_increasing


def test_preprocess_pipeline_writes_processed_file(tmp_path):
    data_root = tmp_path / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)

    raw_df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "open": [100, 101],
            "high": [102, 103],
            "low": [99, 100],
            "close": [101, 102],
            "volume": [1_000_000, 1_100_000],
        }
    )
    raw_path = raw_dir / "TEST_raw.parquet"
    raw_df.to_parquet(raw_path, index=False)

    settings_path = tmp_path / "settings.yaml"
    yaml.safe_dump({"tickers": ["TEST"], "benchmark": "TEST"}, settings_path.open("w"))

    data_sources_path = tmp_path / "data_sources.yaml"
    yaml.safe_dump(
        {
            "data_root": str(data_root),
            "raw_files": {"pattern": "{ticker}_raw.parquet", "directory": "raw"},
            "processed_files": {"pattern": "{ticker}.parquet", "directory": "processed"},
            "options": {"file_format": "parquet"},
        },
        data_sources_path.open("w"),
    )

    written = preprocess_data(
        tickers=["TEST"],
        settings_path=settings_path,
        data_sources_path=data_sources_path,
    )

    assert written, "No files were written by preprocess_data"
    output_path = written[0]
    assert output_path.exists()

    processed = pd.read_parquet(output_path)
    assert list(processed.columns) == CANONICAL_COLUMNS
    assert processed["ticker"].unique().tolist() == ["TEST"]
    assert processed["date"].is_monotonic_increasing
