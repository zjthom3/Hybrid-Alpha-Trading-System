# Hybrid Alpha Trading System — Implementation Backlog

This backlog is organized into **phases** so a VS Code / Codex-style agent can
implement the system iteratively while staying aligned with:

- `docs/prd.md`
- `docs/architecture.md`
- `docs/data_model.md`
- `docs/pipeline_spec.md`
- `docs/agent_instructions.md`

Each task is actionable and can usually be done in a single coding session.

---

## Phase 0 — Repo & Config Foundation

**Goal:** Establish a clean, working skeleton for the project.

### 0.1 Repo Setup

- [ ] Create base folder structure:
  - `docs/`, `config/`, `data/`, `models/`, `src/`, `scripts/`, `tests/`
- [ ] Add `pyproject.toml` or `requirements.txt` with baseline deps:
  - `pandas`, `numpy`, `pyarrow` or `fastparquet`, `lightgbm`, `scikit-learn`, `pyyaml`
- [ ] Add `.gitignore` (ignore `data/`, `models/ml/artifacts/`, `__pycache__/`, etc.)

### 0.2 Config Basics

- [ ] Implement `config/settings.yaml` with:
  - `tickers`, `benchmark`, `backtest` dates, `features`, `ml`, `risk`, `paths`
- [ ] Implement `config/data_sources.yaml` (raw data paths/names)
- [ ] Implement `config/regimes.yaml` (regime labels, ids, default weights)

### 0.3 Core Utilities

- [ ] Implement `src/core/utils.py`:
  - Config loader (`load_config(path: str) -> Dict`)
  - Logger setup (`get_logger(name: str) -> logging.Logger`)
  - Date helpers if needed
- [ ] Implement `src/core/io.py`:
  - `read_parquet(path: str) -> pd.DataFrame`
  - `write_parquet(df: pd.DataFrame, path: str) -> None`
  - Helper to build paths from `config["paths"]["data_root"]`
- [ ] Implement `src/core/types.py`:
  - Type aliases (e.g., `DataFrame = pd.DataFrame`)
  - Optional dataclasses / TypedDicts for core entities (Bars, Positions, etc.)

---

## Phase 1 — Data & Feature Layer

**Goal:** Get from raw OHLCV → processed bars → full feature library.

### 1.1 Data Preprocessing

- [ ] Implement `src/data/loaders.py`:
  - `load_raw_ohlcv(ticker: str, config: Dict) -> pd.DataFrame`
- [ ] Implement `src/data/preprocessing.py`:
  - `preprocess_ohlcv(raw_df: pd.DataFrame, ticker: str) -> pd.DataFrame`
  - Map to canonical schema in `docs/data_model.md`
- [ ] Implement pipeline wrapper `src/pipeline/preprocess_data.py`:
  - For each ticker in config:
    - Load raw data
    - Preprocess
    - Save to `data/processed/<ticker>.parquet`
- [ ] Add tests to `tests/test_data_preprocessing.py`:
  - Validate schema, date uniqueness, and type correctness

### 1.2 Feature Generators

- [ ] Implement `src/features/trend_features.py`:
  - SMAs (10/20/50/200), distances, rolling returns, momentum
- [ ] Implement `src/features/volatility_features.py`:
  - Realized vol (10/20/60), ATR, intraday range %
- [ ] Implement `src/features/volume_features.py`:
  - Volume z-score, volume vs 20d avg
- [ ] Implement `src/features/relative_strength_features.py`:
  - Relative returns vs benchmark, rolling beta

### 1.3 Feature Pipeline

- [ ] Implement `src/pipeline/build_features.py`:
  - Load processed bars for tickers + benchmark
  - Call feature builders and merge outputs
  - Save to `data/features/<ticker>.parquet`
- [ ] Add tests in `tests/test_features.py`:
  - Use synthetic bars to verify feature correctness (e.g., SMA, returns, vol)

---

## Phase 2 — Signal & Regime Layer

**Goal:** Turn features into rule-based alpha signals and regime labels.

### 2.1 Rule-Based Signals

- [ ] Implement `src/signals/trend_alpha.py`:
  - Positive when price above key MAs, negative when below
- [ ] Implement `src/signals/mean_reversion_alpha.py`:
  - Trigger on ±2σ moves in non-strong-trend regimes
- [ ] Implement `src/signals/volatility_alpha.py`:
  - Score based on whether vol is low/high vs history
- [ ] Implement `src/signals/relative_strength_alpha.py`:
  - Score based on relative performance vs benchmark

- [ ] Implement `src/pipeline/build_signals.py`:
  - Load `data/features/<ticker>.parquet`
  - Compute each alpha
  - Save `data/signals/<ticker>.parquet` as per `docs/data_model.md`

- [ ] Add tests in `tests/test_signals.py`:
  - Verify signals direction under simple synthetic scenarios

### 2.2 Regime Engine

- [ ] Implement `models/regime/rule_based_regime.py`:
  - Use benchmark trend + realized vol thresholds to assign:
    - `bull`, `bear`, `choppy`, `crash`
- [ ] Implement `models/regime/hmm_regime_model.py` (optional after rule-based):
  - Train HMM on benchmark returns + vol, infer regimes
- [ ] Implement `src/pipeline/run_regime_engine.py`:
  - Load processed benchmark bars
  - Run regime engine
  - Save `data/regimes/<benchmark>.parquet`

- [ ] Add tests in `tests/test_regime.py`:
  - Simple scenarios where trends/vol clearly map to expected regimes

---

## Phase 3 — ML Prediction Layer

**Goal:** Train a LightGBM classifier to predict next state probabilities.

### 3.1 Labels & Target States

- [ ] Implement a helper in `src/features/label_targets.py`:
  - Derive `target_state_h1`, `target_state_h3`, `target_state_h5` based on rules:
    - E.g., map future returns into discrete state buckets {-2…+3}
- [ ] Optionally integrate labels into `build_features.py` or a separate pipeline step
- [ ] Update `docs/data_model.md` if label storage is separate

- [ ] Add tests in `tests/test_labels.py`:
  - Verify correct label mapping from returns → states

### 3.2 LightGBM Models

- [ ] Implement `models/ml/model_registry.py`:
  - Functions for saving/loading model artifacts by `(model_name, ticker, horizon, version)`
- [ ] Implement `models/ml/lightgbm_next_state.py`:
  - `prepare_training_data(features: pd.DataFrame, horizon: int) -> (X, y)`
  - `train_model(X, y, config) -> model`
  - `predict_proba(model, X_new) -> prob_matrix`
- [ ] Implement `src/pipeline/train_ml_models.py`:
  - For each ticker and each horizon:
    - Build training data
    - Train model
    - Save artifacts

- [ ] Implement `src/pipeline/run_predictions.py`:
  - Load features in backtest window
  - Load models
  - Generate `data/predictions/<ticker>.parquet`

- [ ] Add tests in `tests/test_models.py`:
  - Smoke tests for training and predicting on small synthetic data

---

## Phase 4 — Meta-Model & Risk/Position Sizing

**Goal:** Combine all signals into a final alpha score and turn it into positions.

### 4.1 Meta-Model (Rule-Based)

- [ ] Implement `src/meta/meta_utils.py`:
  - Helpers for weighting and clipping
- [ ] Implement `src/meta/rule_based_meta.py`:
  - Load regime-dependent weights from config
  - Combine:
    - `trend_alpha`
    - `mean_reversion_alpha`
    - `vol_alpha`
    - `rel_strength_alpha`
    - ML signals (e.g., expected state or probability of positive state)
  - Output `alpha_score` in [-1, 1] and contribution columns

- [ ] Implement `src/pipeline/run_meta_model.py`:
  - Join `signals`, `predictions`, and `regimes`
  - Save `data/meta/alpha_scores/<ticker>.parquet`

- [ ] Add tests in `tests/test_meta.py`:
  - Confirm regime weights are applied correctly
  - Confirm alpha_score signs match expectations

### 4.2 Risk & Position Sizing

- [ ] Implement `src/risk/risk_metrics.py`:
  - Realized vol computation
  - Drawdown calculation (for future extensions)
- [ ] Implement `src/risk/position_sizing.py`:
  - Map `alpha_score` + realized vol → `target_weight` with:
    - `target_vol`
    - `max_weight`
  - Ensure clipping and NaN handling

- [ ] Implement `src/pipeline/run_position_sizing.py`:
  - Load alpha scores and vol
  - Compute positions
  - Save `data/positions/<strategy_name>/<ticker>.parquet`

- [ ] Add tests in `tests/test_risk.py`:
  - Check position scaling and clipping

---

## Phase 5 — Backtester & Reporting

**Goal:** Simulate historical performance and generate metrics.

### 5.1 Backtest Engine

- [ ] Implement `src/backtest/engine.py`:
  - Daily step:
    - Read target weights
    - Adjust positions using next open/close (configurable)
    - Compute trade list and portfolio value
- [ ] Implement `src/backtest/metrics.py`:
  - Sharpe, Sortino, max drawdown, win rate, etc.
- [ ] Implement `src/backtest/reports.py`:
  - Write `pnl_timeseries.parquet` and `summary.json` to:
    - `data/backtests/<strategy_name>/`

- [ ] Implement `src/pipeline/run_backtest.py`:
  - Load positions + processed bars
  - Call engine, metrics, reports

- [ ] Add tests in `tests/test_backtest.py`:
  - Use tiny synthetic dataset and a trivial strategy
  - Validate PnL and metrics against expected values

---

## Phase 6 — Scripts & Glue

**Goal:** Make it easy to run full backtests and daily updates.

### 6.1 Backtest Script

- [ ] Implement `scripts/run_full_backtest.py`:
  - Load config
  - Run pipeline steps in order:
    - preprocess → build_features → build_signals → run_regime_engine →
      train_ml_models (optional) → run_predictions → run_meta_model →
      run_position_sizing → run_backtest

### 6.2 Daily Update Script

- [ ] Implement `scripts/run_daily_update.py`:
  - Assume new raw data is already saved to `data/raw/`
  - Run incremental:
    - preprocess → build_features → build_signals → run_regime_engine →
      run_predictions → run_meta_model → run_position_sizing

### 6.3 Inspection / Debug Script

- [ ] Implement `scripts/inspect_signals.py`:
  - CLI that prints or plots:
    - features, signals, alpha scores for a given ticker/date range

---

## Phase 7 — Polish, Docs, and Extensions

**Goal:** Bring the codebase closer to a production-grade research tool.

- [ ] Add README with:
  - High-level description
  - How to run a backtest
  - How to add a new ticker
- [ ] Add example config with 1–2 tickers (e.g., SPY, NVDA)
- [ ] Add small synthetic sample data in `data/sample/` for tests
- [ ] Improve logging and error messages across pipelines
- [ ] Add simple plots (optional, for human debugging, not required for agent)

---

## Phase Status Tracking

Use this section to track progress:

- [ ] Phase 0 — Repo & Config
- [ ] Phase 1 — Data & Features
- [ ] Phase 2 — Signals & Regimes
- [ ] Phase 3 — ML Predictions
- [ ] Phase 4 — Meta & Risk
- [ ] Phase 5 — Backtester & Reporting
- [ ] Phase 6 — Scripts & Glue
- [ ] Phase 7 — Polish & Extensions

---

This backlog should be treated as a **living document**:
- When new modules or features are added, update this file.
- When tasks are completed, check them off.
- If a spec in `docs/` changes, ensure the corresponding tasks and code are updated.
