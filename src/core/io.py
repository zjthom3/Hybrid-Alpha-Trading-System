"""
I/O helpers for reading and writing Parquet/CSV files in a consistent manner.
All functions should respect the configured data root to keep paths portable.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from .types import DataFrame
from .utils import ensure_directory, get_logger

logger = get_logger(__name__)


def resolve_path(path: str | Path, data_root: Optional[str | Path] = None) -> Path:
    """
    Resolve a file path relative to a configurable data root.

    Args:
        path: File path (absolute or relative).
        data_root: Optional root directory for data files.

    Returns:
        Resolved absolute path.
    """
    path_obj = Path(path)
    if data_root:
        root = Path(data_root)
        path_obj = root / path_obj
    return path_obj


def read_parquet(path: str | Path, data_root: Optional[str | Path] = None) -> DataFrame:
    """
    Read a Parquet file into a DataFrame.

    Args:
        path: Path to the Parquet file.
        data_root: Optional data root used to resolve relative paths.
    """
    resolved = resolve_path(path, data_root)
    logger.info(f"Reading Parquet file from {resolved}")
    return pd.read_parquet(resolved)


def write_parquet(
    df: DataFrame, path: str | Path, data_root: Optional[str | Path] = None
) -> Path:
    """
    Write a DataFrame to Parquet, creating parent directories as needed.

    Args:
        df: DataFrame to write.
        path: Destination path.
        data_root: Optional data root used to resolve relative paths.

    Returns:
        The resolved path that was written.
    """
    resolved = resolve_path(path, data_root)
    ensure_directory(resolved.parent)
    logger.info(f"Writing Parquet file to {resolved}")
    df.to_parquet(resolved, index=False)
    return resolved


def read_csv(path: str | Path, data_root: Optional[str | Path] = None) -> DataFrame:
    """
    Read a CSV file into a DataFrame.
    """
    resolved = resolve_path(path, data_root)
    logger.info(f"Reading CSV file from {resolved}")
    return pd.read_csv(resolved)


def write_csv(
    df: DataFrame, path: str | Path, data_root: Optional[str | Path] = None
) -> Path:
    """
    Write a DataFrame to CSV, creating parent directories as needed.
    """
    resolved = resolve_path(path, data_root)
    ensure_directory(resolved.parent)
    logger.info(f"Writing CSV file to {resolved}")
    df.to_csv(resolved, index=False)
    return resolved


__all__ = ["read_parquet", "write_parquet", "read_csv", "write_csv", "resolve_path"]
