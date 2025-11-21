# Hybrid Alpha Trading System — Agent Instructions

This document defines how an AI coding agent should work inside this repository:
what to read, how to implement features, how to test, and how to keep the project
consistent with the design.

The goal: **build a modular, testable Hybrid Alpha Trading System** as specified in:

- `docs/prd.md`
- `docs/architecture.md`
- `docs/data_model.md`
- `docs/pipeline_spec.md`

---

## 1. Primary Responsibilities

As the coding agent, you are responsible for:

1. Implementing Python modules under `src/` and `models/` according to specs.
2. Wiring pipeline orchestration under `src/pipeline/` and `scripts/`.
3. Ensuring I/O and schemas match `docs/data_model.md`.
4. Adding and maintaining tests under `tests/`.
5. Keeping the codebase consistent, modular, and easy to debug.

You **must not** silently change the data model, paths, or core contracts without
updating the appropriate docs and/or configuration.

---

## 2. Read This First (Boot Sequence)

Before writing any code in a session:

1. Read `docs/prd.md` — understand the product goals and success metrics.
2. Read `docs/architecture.md` — understand repo layout and module responsibilities.
3. Read `docs/data_model.md` — understand all schemas.
4. Read `docs/pipeline_spec.md` — understand backtest & daily pipelines.

When you implement or modify a module, always cross-check against these documents.

---

## 3. Coding Standards

### 3.1 Language & Style

- Language: **Python 3.x**
- Follow **PEP8** for style.
- Use **type hints** for all public functions.
- Use **docstrings** to explain inputs/outputs, especially for pipeline steps.

Example:

from typing import Dict, List
import pandas as pd

def build_features(bars: pd.DataFrame, benchmark: pd.DataFrame, config: Dict) -> pd.DataFrame:
    """
    Build features for a single ticker.

    Args:
        bars: Processed OHLCV data for one ticker, indexed or keyed by date.
        benchmark: Processed OHLCV data for benchmark index.
        config: Dictionary of feature configuration (lookbacks, etc.).

    Returns:
        DataFrame with one row per date and feature columns as defined in docs/data_model.md.
    """
    ...

3.2 Dependencies

Define dependencies in pyproject.toml or requirements.txt (as appropriate).

Prefer pandas, numpy, lightgbm for ML, and standard library.

Avoid adding heavy or obscure dependencies unless necessary.

4. Files & Responsibilities
4.1 src/core/

types.py

Define typed structures or aliases (e.g., DataFrame = pd.DataFrame or TypedDict for schemas).

utils.py

Logging utilities, date/time helpers, simple config loaders.

io.py

Functions to read/write Parquet/CSV using paths from config.

Ensure consistent date parsing and column types.

4.2 src/data/

loaders.py

Load raw data from data/raw/.

Provide helpers for fetching per-ticker data.

preprocessing.py

Standardize OHLCV into canonical schema as defined in docs/data_model.md.

Write to data/processed/<ticker>.parquet.

4.3 src/features/

Implement:

trend_features.py

volatility_features.py

volume_features.py

relative_strength_features.py

Each should export a function that takes a processed bars DataFrame (and possibly benchmark DataFrame) and returns a feature DataFrame as described in docs/data_model.md.

4.4 src/signals/

Implement rule-based alpha signals:

trend_alpha.py

mean_reversion_alpha.py

volatility_alpha.py

relative_strength_alpha.py

Each module should provide a compute_signal(features: pd.DataFrame) -> pd.Series
function or equivalent.

4.5 models/regime/

Implement:

hmm_regime_model.py

rule_based_regime.py

Follow docs/pipeline_spec.md:

Train or apply an HMM or rule-based model over benchmark returns + vol.

Output regimes per date, following the schema in docs/data_model.md.

4.6 models/ml/

Implement:

lightgbm_next_state.py

model_registry.py

Behaviors:

Train LightGBM models using features + labels (target states).

Save/load models from models/ml/artifacts/.

Predict next state probabilities as per docs/data_model.md.

4.7 src/meta/

rule_based_meta.py

Combine rule-based signals, ML predictions, and regimes into alpha_score.

meta_utils.py

Helpers for weighting, clipping, scaling.

4.8 src/risk/

position_sizing.py

Map alpha_score + realized vol → target_weight.

risk_metrics.py

Compute realized volatility, drawdowns, and other risk stats.

4.9 src/backtest/

engine.py

Event-driven backtest, daily resolution.

metrics.py

Sharpe, Sortino, max drawdown, win rate, etc.

reports.py

Wrap metrics into reporting artifacts (e.g., summary JSON).

4.10 src/pipeline/

Each file here is a coordinator that:

Loads config.

Uses src/core/io.py to read/write data.

Calls functions from other src/ and models/ modules.

Logs high-level progress.

Example modules:

build_features.py

build_signals.py

run_regime_engine.py

train_ml_models.py

run_predictions.py

run_meta_model.py

run_position_sizing.py

run_backtest.py

5. Scripts / Entry Points

Under scripts/:

run_full_backtest.py

run_daily_update.py

inspect_signals.py

Scripts should be thin wrappers that:

Parse command-line arguments (if any).

Load config/settings.yaml.

Call the appropriate src/pipeline/* functions in sequence.

Log completion or errors.

Do not put core business logic inside scripts — keep it in src/.

6. Configuration Handling

All configurable values (tickers, horizons, paths, risk settings) must come from:

config/settings.yaml

config/data_sources.yaml

config/regimes.yaml

Rules:

Never hard-code tickers or paths directly in modules.

Use a small config loader in src/core/utils.py (or similar).

Validate required keys at startup of each pipeline step and fail early with clear errors.

7. Testing Requirements

Place tests in tests/:

tests/test_features.py

tests/test_signals.py

tests/test_models.py

tests/test_meta.py

tests/test_risk.py

tests/test_backtest.py

7.1 Testing Rules

Use small synthetic datasets to validate logic:

A few rows of OHLCV.

Known feature values.

Simple regimes.

Test both expected outputs and edge cases:

Missing data.

Short time series.

Extreme values (e.g., huge gaps, no volatility).

Example expectations:

Trend signal should be positive when price is clearly above MA and vice versa.

Position sizing should clip at max_weight.

Backtest engine should produce known PnL for a trivial strategy
(e.g., always fully invested).

8. Data Model Compliance

You must ensure that:

All tables conform to docs/data_model.md.

Column names, types, and meanings are preserved.

New columns are additive and do not break existing contracts.

If you need to change the data model:

Update docs/data_model.md.

Update affected modules.

Update tests.

Do not make silent schema changes.

9. Incremental & Idempotent Design

Pipelines (especially daily update) should be:

Incremental:

Able to run only for the most recent dates when possible.

Idempotent:

If run twice for the same date range, results should match (or be safely overwritten).

Use append-or-upsert patterns when writing Parquet/CSV, or overwrite entire files in a controlled way.

10. Logging & Error Handling

Use Python’s built-in logging module (or a simple wrapper in src/core/utils.py).

Log:

Start and end of each pipeline step.

Ticker names and date ranges being processed.

Summary stats (e.g., number of rows written).

When failing:

Raise explicit exceptions with helpful messages, e.g.:

raise ValueError("No features found for NVDA between 2020-01-01 and 2020-06-01.")


Avoid silent failure or pass blocks that hide issues.

11. Performance Considerations

MVP focus:

Correctness and clarity > micro-optimization.

Use vectorized pandas operations where practical.

Keep API boundaries clear (functions with well-defined inputs/outputs).

Only optimize after baseline correctness, testing, and metrics are in place.

12. Extension Guidance

When adding new functionality:

Check if it belongs:

A new signal → src/signals/

A new ML model → models/ml/

New risk logic → src/risk/

Update:

docs/architecture.md if a new module/file is added.

docs/data_model.md if the data schema changes.

Add or update tests in tests/.

13. Summary for the Agent

When you start a coding task:

Identify the relevant spec section:

PRD → what & why

Architecture → where

Data model → how the data looks

Pipeline spec → when & in what order

Implement or update the corresponding module under src/ or models/.

Wire it into the pipeline under src/pipeline/ and scripts if needed.

Add/update tests to validate behavior.

Run tests (e.g., pytest) and fix issues before moving on.
