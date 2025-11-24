"""
Utility helpers for configuration loading, logging, and filesystem convenience.
These functions should be reused across pipeline modules to keep behavior consistent.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_config(path: str | Path) -> Dict[str, Any]:
    """
    Load a YAML configuration file and return it as a dictionary.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed configuration as a dictionary.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    return config


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Return a logger with a simple, consistent formatter.

    Args:
        name: Logger name, typically __name__ of the caller.
        level: Logging level (defaults to INFO).
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


def ensure_directory(path: str | Path) -> Path:
    """
    Create a directory (and parents) if it does not exist.

    Args:
        path: Directory path to create.

    Returns:
        The resolved directory path.
    """
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


__all__ = ["load_config", "get_logger", "ensure_directory"]
