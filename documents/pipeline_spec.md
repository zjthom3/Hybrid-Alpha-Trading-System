# Hybrid Alpha Trading System — Pipeline Spec

This document defines the **end-to-end pipelines** for:

1. Full historical **backtest pipeline**
2. Daily **live/update pipeline**

Each step is designed so a VS Code / Codex-style agent can implement and orchestrate them using the repo’s structure and config files.

---

## 1. Overview

### 1.1 Pipeline Layers

Both backtest and daily pipelines pass through these layers:

1. Data loading & preprocessing
2. Feature generation
3. Signal computation (rule-based alphas)
4. Regime engine (market state)
5. ML prediction (next-state forecasts)
6. Meta-model aggregation (combined alpha)
7. Risk & position sizing
8. Backtest / Output

Each layer should be callable as:
- A **Python module** in `src/pipeline/`
- A **script entrypoint** in `scripts/`

Configuration is centralized in `config/settings.yaml` and related config files.

---

## 2. Config-Driven Execution

### 2.1 Global Config (`config/settings.yaml`)

Expected keys (example):

tickers:
  - NVDA
  - MSFT
  - SPY

benchmark: SPY

backtest:
  start_date: "2015-01-01"
  end_date: "2025-01-01"
  strategy_name: "hybrid_alpha_mvp"

features:
  lookbacks:
    sma: [10, 20, 50, 200]
    returns: [1, 5, 20]
    realized_vol: [10, 20, 60]

ml:
  horizons: [1, 3, 5]
  model_name: "lightgbm_v1"

risk:
  target_vol: 0.15
  max_weight: 0.10

paths:
  data_root: "data"

All pipeline steps should:

Load config once

Use the provided paths and parameters

Avoid hard-coded constants where possible

3. Backtest Pipeline
3.1 High-Level Flow
1) Load & preprocess raw data
2) Build features
3) Build signals
4) Run regime engine
5) Train ML models (if needed)
6) Run ML predictions
7) Run meta-model (alpha scores)
8) Run position sizing
9) Run backtest
10) Save reports


Each numbered step maps to a src/pipeline/* module and is callable from scripts/run_full_backtest.py.

3.2 Step-by-Step Spec
Step 1 — Data Preprocessing

Module: src/data/preprocessing.py
Orchestrator: src/pipeline/build_features.py (first stage) or a dedicated src/pipeline/preprocess_data.py if desired.

Inputs:

data/raw/<ticker>_raw.* per ticker

Behavior:

Clean and standardize OHLCV fields into canonical schema.

Enforce a unique (date, ticker) index.

Optionally adjust for splits/dividends.

Outputs:

data/processed/<ticker>.parquet

Step 2 — Feature Generation

Module: src/features/*.py
Orchestrator: src/pipeline/build_features.py

Inputs:

data/processed/<ticker>.parquet for each ticker

data/processed/<benchmark>.parquet for benchmark

Behavior:

Load processed bars.

Compute trend, volatility, volume, and relative-strength features.

Merge into a single feature DataFrame per ticker.

Optionally attach ML labels (target states) if configured.

Outputs:

data/features/<ticker>.parquet

Step 3 — Signal Computation

Module: src/signals/*.py
Orchestrator: src/pipeline/build_signals.py

Inputs:

data/features/<ticker>.parquet

Behavior:

For each ticker:

Compute trend_alpha, mean_reversion_alpha, vol_alpha, rel_strength_alpha.

Ensure all signals are continuous scores in [-1, 1].

Outputs:

data/signals/<ticker>.parquet

Step 4 — Regime Engine

Module: models/regime/*.py
Orchestrator: src/pipeline/run_regime_engine.py

Inputs:

data/processed/<benchmark>.parquet

Optional: benchmark features if needed

Behavior:

Train or load regime model (HMM or rule-based).

Infer regime labels and probabilities per date for the benchmark.

Outputs:

data/regimes/<benchmark>.parquet

Step 5 — Train ML Models (Optional in Backtest Run)

Module: models/ml/lightgbm_next_state.py, models/ml/model_registry.py
Orchestrator: src/pipeline/train_ml_models.py

Inputs:

data/features/<ticker>.parquet with label columns (e.g., target_state_h1, etc.)

Config specifying:

ml.horizons

ml.model_name

Train/test split rules (walk-forward)

Behavior:

Prepare training datasets per ticker or global model.

Train LightGBM models for each horizon.

Run walk-forward validation and log metrics.

Save model artifacts under models/ml/artifacts/.

Outputs:

models/ml/artifacts/<model_name>_<ticker>_h<horizon>_v<version>.pkl (or similar)

Training logs and basic metrics (stdout/log file)

Note: In repeated backtests, this step can be skipped if models already exist.

Step 6 — ML Predictions

Module: models/ml/lightgbm_next_state.py
Orchestrator: src/pipeline/run_predictions.py

Inputs:

Latest data/features/<ticker>.parquet

Pre-trained model artifacts from models/ml/artifacts/

Config ml.horizons, ml.model_name

Behavior:

Load trained models.

For each ticker, for each horizon:

Generate state probability distribution at each date within backtest window.

Align predictions with feature dates.

Outputs:

data/predictions/<ticker>.parquet

One row per (date, horizon) or per design choice.

Step 7 — Meta-Model (Alpha Aggregation)

Module: src/meta/rule_based_meta.py
Orchestrator: src/pipeline/run_meta_model.py

Inputs:

data/signals/<ticker>.parquet

data/predictions/<ticker>.parquet

data/regimes/<benchmark>.parquet

Config with regime weighting table (config/regimes.yaml or inside settings.yaml)

Behavior:

Join signals, predictions, and regimes on date.

Based on regime, apply weights to:

trend_alpha

mean_reversion_alpha

vol_alpha

rel_strength_alpha

ML prediction signal(s)

Compute:

alpha_score in [-1, 1]

Optional contribution columns

Outputs:

data/meta/alpha_scores/<ticker>.parquet

Step 8 — Position Sizing

Module: src/risk/position_sizing.py, src/risk/risk_metrics.py
Orchestrator: src/pipeline/run_position_sizing.py

Inputs:

data/meta/alpha_scores/<ticker>.parquet

data/features/<ticker>.parquet (to derive realized vol)

Risk settings from config/settings.yaml:

risk.target_vol

risk.max_weight

Behavior:

Compute realized vol per ticker/date.

Map alpha_score → target_weight using volatility targeting:

target_weight ≈ alpha_score * (target_vol / realized_vol) (clamped)

Enforce:

Max weight per ticker

Optional global exposure rules (if implemented in this step)

Outputs:

data/positions/<strategy_name>/<ticker>.parquet

Step 9 — Backtest Engine

Module: src/backtest/engine.py, src/backtest/metrics.py, src/backtest/reports.py
Orchestrator: src/pipeline/run_backtest.py

Inputs:

data/processed/<ticker>.parquet (price series)

data/positions/<strategy_name>/<ticker>.parquet

Config:

Execution assumption (e.g., “trade at next open”)

Behavior:

Generate trades that move from yesterday’s position → today’s target position.

Compute daily PnL, portfolio value, drawdowns.

Compute key metrics (Sharpe, max DD, win rate, etc.).

Optionally segment PnL by regime and by alpha type.

Outputs:

data/backtests/<strategy_name>/trades.parquet

data/backtests/<strategy_name>/pnl_timeseries.parquet

data/backtests/<strategy_name>/summary.json

3.3 Backtest Script: scripts/run_full_backtest.py

Behavior:

Parse CLI args (optional):

--config config/settings.yaml

--strategy hybrid_alpha_mvp

Execute pipeline steps in order (1–9).

Log progress and key metrics.

Example Pseudocode:

def main():
    config = load_config("config/settings.yaml")
    tickers = config["tickers"]

    preprocess_data(tickers, config)
    build_features(tickers, config)
    build_signals(tickers, config)
    run_regime_engine(config)
    train_ml_models(tickers, config)      # optional if pre-trained
    run_predictions(tickers, config)
    run_meta_model(tickers, config)
    run_position_sizing(tickers, config)
    run_backtest(tickers, config)

if __name__ == "__main__":
    main()

4. Daily / Live Update Pipeline
4.1 High-Level Flow
1) Fetch latest raw data (new bars)
2) Update processed data
3) Rebuild latest features (incremental)
4) Rebuild latest signals
5) Update regime state for latest date
6) Run ML predictions for latest date
7) Run meta-model for latest date
8) Compute new positions for next session
9) Persist outputs for consumption (UI or execution system)


This pipeline assumes:

Models are already trained.

Historical artifacts exist.

4.2 Step-by-Step Spec (Daily Mode)
Step 1 — Fetch & Update Raw Data

Module: may be external or a helper in src/data/loaders.py
Orchestrator: scripts/run_daily_update.py

Inputs:

Data provider (not implemented here; user handles fetching)

Behavior:

Append latest bar(s) to data/raw/<ticker>_raw.*

Or maintain a replacement file with full history.

Step 2 — Update Processed Bars

Module: src/data/preprocessing.py
Orchestrator: scripts/run_daily_update.py or src/pipeline/preprocess_data.py

Inputs:

updated data/raw/<ticker>_raw.*

Behavior:

Re-run preprocessing for latest date(s) only if possible.

Save updated processed files.

Outputs:

updated data/processed/<ticker>.parquet

Step 3 — Rebuild Latest Features

Module: src/features/*.py
Orchestrator: src/pipeline/build_features.py (with incremental capability)

Inputs:

updated data/processed/<ticker>.parquet

updated data/processed/<benchmark>.parquet

Behavior:

Recompute features window for latest date(s).

Append or update data/features/<ticker>.parquet.

Step 4 — Rebuild Latest Signals

Module: src/signals/*.py
Orchestrator: src/pipeline/build_signals.py (incremental)

Inputs:

updated data/features/<ticker>.parquet

Behavior:

Compute signal values for latest date(s).

Append/update data/signals/<ticker>.parquet.

Step 5 — Update Regime State

Module: models/regime/*.py
Orchestrator: src/pipeline/run_regime_engine.py

Inputs:

updated data/processed/<benchmark>.parquet

Behavior:

Using pre-trained regime model or rule set:

Infer regime for the new date(s) only.

Append/update data/regimes/<benchmark>.parquet.

Step 6 — Run ML Predictions (Latest Date)

Module: models/ml/lightgbm_next_state.py
Orchestrator: src/pipeline/run_predictions.py

Inputs:

updated data/features/<ticker>.parquet

ML models from models/ml/artifacts/

Behavior:

Extract last available feature rows for each ticker.

Run prediction across configured horizons.

Append/update data/predictions/<ticker>.parquet with latest rows.

Step 7 — Meta-Model (Latest Date)

Module: src/meta/rule_based_meta.py
Orchestrator: src/pipeline/run_meta_model.py

Inputs:

latest rows from:

data/signals/<ticker>.parquet

data/predictions/<ticker>.parquet

data/regimes/<benchmark>.parquet

Behavior:

Combine signals, predictions, and regime for the latest date.

Compute alpha_score and optional contributions.

Outputs:

updated data/meta/alpha_scores/<ticker>.parquet

Step 8 — Position Sizing (Latest Date)

Module: src/risk/position_sizing.py
Orchestrator: src/pipeline/run_position_sizing.py

Inputs:

latest alpha scores

latest realized vol

Behavior:

Compute target_weight (and optional target_dollar_pos) for next session.

Append/update data/positions/<strategy_name>/<ticker>.parquet.

Outputs:

latest position instructions

4.3 Daily Script: scripts/run_daily_update.py

Behavior:

Run steps 2–8 (and optionally step 1 if data fetching is scripted).

Designed to be run once per day (e.g., after market close).

Example Pseudocode:

def main():
    config = load_config("config/settings.yaml")
    tickers = config["tickers"]

    # 1. Assume raw data already updated by external job, or implement here.
    preprocess_data(tickers, config)
    build_features(tickers, config, incremental=True)
    build_signals(tickers, config, incremental=True)
    run_regime_engine(config, incremental=True)
    run_predictions(tickers, config, incremental=True)
    run_meta_model(tickers, config, incremental=True)
    run_position_sizing(tickers, config, incremental=True)

if __name__ == "__main__":
    main()

5. Error Handling & Logging

All pipeline steps should:

Use a shared logging utility (e.g., src/core/utils.py).

Fail fast if:

Required files are missing.

Key inputs are empty or misaligned.

Provide clear error messages, e.g.:

Missing features for ticker NVDA on date 2024-03-01

No ML model found for horizon=3, ticker=SPY, model=lightgbm_v1

6. Agent Implementation Notes

For a VS Code / Codex-style agent:

Implement each pipeline step as pure functions in src/pipeline/ that:

Read config + IO paths.

Call lower-level modules (src/data/, src/features/, etc.).

Log progress.

Scripts in scripts/ should be thin wrappers that:

Load config.

Call pipeline functions in correct order.
