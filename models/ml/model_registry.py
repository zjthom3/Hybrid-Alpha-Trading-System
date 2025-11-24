"""
Simple model registry for saving/loading LightGBM models keyed by ticker/horizon/version.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import joblib


@dataclass
class ModelKey:
    model_name: str
    ticker: str
    horizon: int
    version: str = "v1"

    def filename(self) -> str:
        return f"{self.model_name}_{self.ticker}_h{self.horizon}_{self.version}.pkl"


def save_model(model, artifacts_dir: str | Path, key: ModelKey) -> Path:
    artifacts_path = Path(artifacts_dir)
    artifacts_path.mkdir(parents=True, exist_ok=True)
    path = artifacts_path / key.filename()
    joblib.dump(model, path)
    return path


def load_model(artifacts_dir: str | Path, key: ModelKey):
    path = Path(artifacts_dir) / key.filename()
    if not path.exists():
        raise FileNotFoundError(f"Model artifact not found: {path}")
    return joblib.load(path)


__all__ = ["ModelKey", "save_model", "load_model"]
