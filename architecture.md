# Hybrid Alpha Trading System — Architecture

## 1. Repository Structure

The project is organized into clearly separated layers: data, features, signals, models, meta-model, risk, backtesting, and CLI entrypoints.

├── docs/
│   ├── prd.md
│   └── architecture.md
├── config/
│   ├── settings.yaml
│   ├── data_sources.yaml
│   └── regimes.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   ├── features/
│   ├── signals/
│   ├── regimes/
│   ├── predictions/
│   ├── meta/
│   │   └── alpha_scores/
│   └── backtests/
├── models/
│   ├── ml/
│   │   ├── lightgbm_next_state.py
│   │   └── model_registry.py
│   └── regime/
│       ├── hmm_regime_model.py
│       └── rule_based_regime.py
├── src/
│   ├── core/
│   │   ├── types.py
│   │   ├── utils.py
│   │   └── io.py
│   ├── data/
│   │   ├── loaders.py
│   │   └── preprocessing.py
│   ├── features/
│   │   ├── trend_features.py
│   │   ├── volatility_features.py
│   │   ├── volume_features.py
│   │   └── relative_strength_features.py
│   ├── signals/
│   │   ├── trend_alpha.py
│   │   ├── mean_reversion_alpha.py
│   │   ├── volatility_alpha.py
│   │   └── relative_strength_alpha.py
│   ├── meta/
│   │   ├── rule_based_meta.py
│   │   └── meta_utils.py
│   ├── risk/
│   │   ├── position_sizing.py
│   │   └── risk_metrics.py
│   ├── backtest/
│   │   ├── engine.py
│   │   ├── metrics.py
│   │   └── reports.py
│   └── pipeline/
│       ├── build_features.py
│       ├── build_signals.py
│       ├── run_regime_engine.py
│       ├── train_ml_models.py
│       ├── run_predictions.py
│       ├── run_meta_model.py
│       ├── run_position_sizing.py
│       └── run_backtest.py
├── scripts/
│   ├── run_full_backtest.py
│   ├── run_daily_update.py
│   └── inspect_signals.py
├── tests/
│   ├── test_features.py
│   ├── test_signals.py
│   ├── test_models.py
│   ├── test_meta.py
│   ├── test_risk.py
│   └── test_backtest.py
└── pyproject.toml / requirements.txt
The Codex/AI agent should read docs/prd.md and this file first, then implement modules under src/, models/, and scripts/ according to the contracts below.

2. Data Flow Overview

High-level pipeline:

Raw Market Data
  → Data Preprocessing
  → Feature Engine
  → Alpha Signal Layer
  → Regime Engine
  → ML Prediction Layer
  → Meta-Model Aggregation
  → Position Sizing
  → Backtest / Live Output


Each stage reads from and writes to structured Parquet/CSV files under /data/ and can be run independently or chained.

3. Core Modules & Responsibilities
3.1 src/core/

Goal: shared types, utilities, and IO helpers.

types.py

Define dataclasses / TypedDicts for:

Bar, FeatureRow, SignalRow, PredictionRow, RegimeRow, AlphaScore, Position, Trade, BacktestResult.

utils.py

Time/date helpers, config loading, logging helpers.

io.py

Functions to read/write Parquet/CSV from /data/*.

Standardized naming conventions per asset + frequency.

3.2 src/data/

Goal: ingest, clean, and normalize raw market data.

loaders.py

Functions:

load_raw_ohlcv(ticker: str) -> DataFrame

save_processed_bars(df: DataFrame, ticker: str) -> None

Handle missing data, alignment, and basic sanity checks.

preprocessing.py

Adjustments (splits/dividends if needed).

Return clean OHLCV with consistent date indices.

Output to: data/processed/<ticker>.parquet

3.3 src/features/

Goal: build reusable feature library per (ticker, date).

trend_features.py

Moving averages (10/20/50/200), distance from MA, rolling returns, momentum.

volatility_features.py

Realized vol, ATR, intraday range %, rolling std.

volume_features.py

Volume z-score, volume/float, money-flow style metrics.

relative_strength_features.py

Ticker vs SPY/QQQ: relative returns, rolling beta.

Each module exposes a function like:

def build_features(bars: DataFrame, benchmark: DataFrame, **kwargs) -> DataFrame:
    ...


Pipeline wrapper:

src/pipeline/build_features.py

Orchestrates:

Load processed bars

Build all feature sets

Merge into single feature frame keyed by (ticker, date)

Writes to: data/features/<ticker>.parquet

3.4 src/signals/

Goal: compute interpretable rule-based alpha signals.

Files:

trend_alpha.py

mean_reversion_alpha.py

volatility_alpha.py

relative_strength_alpha.py

Each module should expose something like:

def compute_signal(features: DataFrame) -> Series:
    """Return continuous signal in [-1, 1]."""


Pipeline wrapper:

src/pipeline/build_signals.py

For each ticker:

Load features

Compute each signal

Combine into signals_df with columns:

trend_alpha, mean_rev_alpha, vol_alpha, rel_strength_alpha

Save to: data/signals/<ticker>.parquet

3.5 models/regime/

Goal: classify market regime at index level (SPY/QQQ/etc.).

hmm_regime_model.py

HMM-based regime detection (returns + vol).

Train + infer functions:

train_hmm_regime(bars: DataFrame) -> FittedModel

infer_regime(model, bars: DataFrame) -> DataFrame

rule_based_regime.py

Simple rule-based fallback using MA + VIX (if available).

Pipeline wrapper:

src/pipeline/run_regime_engine.py

For the chosen benchmark:

Load bars/features

Run regime model

Output DataFrame with columns:

regime_label in {bull, bear, choppy, crash}

regime_prob_bull, regime_prob_bear, etc.

Save to: data/regimes/<benchmark>.parquet

3.6 models/ml/

Goal: predict next state probabilities using ML.

lightgbm_next_state.py

Transform (features, labels) into train/val splits (walk-forward).

Train LightGBM classifier for one or more horizons (e.g., 1, 3, 5 days).

Save model artifacts to models/ml/artifacts/.

Inference function:

predict_next_state(features_today: DataFrame, model) -> DataFrame

With columns: pred_state, prob_pred_state, and probability columns per state.

model_registry.py

Simple interface to load/save versioned models by:

ticker, horizon, model_name, version.

Pipeline wrapper:

src/pipeline/train_ml_models.py

Load features + historical labels (from state labeler or derived).

Train models per ticker or global model.

Save artifacts.

src/pipeline/run_predictions.py

Load latest features and ML model.

Run predictions for configured tickers.

Output to: data/predictions/<ticker>.parquet

3.7 src/meta/

Goal: combine signals, regimes, and ML predictions into a single alpha score.

rule_based_meta.py

Implement regime-dependent weighting table.

Function:

def combine_signals(
    signals: DataFrame,
    predictions: DataFrame,
    regimes: DataFrame,
    config: Dict
) -> DataFrame:
    """Return alpha_score in [-1, 1] and optional confidence metrics."""


meta_utils.py

Helper functions for scaling, normalization, clipping, etc.

Pipeline wrapper:

src/pipeline/run_meta_model.py

Load:

signals/<ticker>.parquet

predictions/<ticker>.parquet

regimes/<benchmark>.parquet

Join on dates and apply meta-model.

Save to: data/meta/alpha_scores/<ticker>.parquet

3.8 src/risk/

Goal: convert alpha scores into position sizes with risk constraints.

position_sizing.py

Implements vol targeting and clamping:

def compute_positions(
    alpha_scores: DataFrame,
    realized_vol: Series,
    config: Dict
) -> DataFrame:
    """Return desired position (e.g., weight) per date."""


risk_metrics.py

Functions to compute:

rolling volatility

drawdowns

risk budgets per ticker/portfolio.

Pipeline wrapper:

src/pipeline/run_position_sizing.py

Load:

alpha scores

realized vol from features

Compute positions.

Save to: data/positions/<strategy_name>/<ticker>.parquet (or similar).

3.9 src/backtest/

Goal: simulate strategy performance historically.

engine.py

Event-driven engine on daily bars:

Read positions over time.

Simulate entries/exits at open/close (configurable).

Generate trades and PnL.

metrics.py

Compute:

Sharpe

Sortino

max drawdown

win rate

PnL by regime

PnL by signal bucket (optional).

reports.py

Summarize backtest results.

Save summary JSON/Markdown to data/backtests/<strategy_name>/summary.*

Pipeline wrapper:

src/pipeline/run_backtest.py

Orchestrate:

Load bars + positions

Run engine

Compute metrics

Write results.

4. Scripts (CLI Entry Points)

Located in scripts/. These should be simple Python entrypoints that glue together the pipeline.

run_full_backtest.py

Steps (for a given config/strategy):

build_features

build_signals

run_regime_engine

train_ml_models (optional if already trained)

run_predictions

run_meta_model

run_position_sizing

run_backtest

run_daily_update.py

For live/rolling mode (assumes models trained):

Load latest raw data

Update processed bars

Rebuild most recent features

Rebuild signals for latest date

Run regime engine for latest date

Run ML predictions for latest date

Run meta-model

Compute positions for next session

inspect_signals.py

Debugging tool:

Load signals/alpha scores for a ticker/date range.

Print or plot sample rows for inspection.

5. Configuration

Central configuration under config/:

settings.yaml

Global settings:

tickers

benchmark symbol

feature settings (lookback windows, etc.)

horizons for prediction

volatility target, max position size

data_sources.yaml

How to locate/load raw data (paths, file names).

regimes.yaml

Regime thresholds or HMM parameters (if using rule-based approach).

All pipeline and script modules should read configuration from these files rather than hard-coding constants.

6. Testing Strategy

tests/ will include unit tests for each layer:

test_features.py

Verify feature calculations given small synthetic price series.

test_signals.py

Verify signal sign/direction under known scenarios.

test_models.py

Smoke tests for ML training and prediction API.

test_meta.py

Check that regime weighting is applied correctly.

test_risk.py

Check that position sizing respects caps and volatility targeting.

test_backtest.py

Backtest engine on a tiny synthetic dataset with known outcomes.

7. Extension Points (Future)

Add new alpha modules under src/signals/.

Add new ML models under models/ml/ and register them in model_registry.py.

Replace rule_based_meta.py with a learned stacking model later.

Extend risk layer to multi-asset portfolio optimizer.
