# Hybrid Alpha Trading System — Sprint Plan

This sprint plan defines actionable, time-bound development phases to build the Hybrid Alpha system from zero to full backtesting. Each sprint assumes two-week cycles, but can be accelerated.

Sprints map directly to phases in `BACKLOG.md` and specifications in:

- `docs/prd.md`
- `docs/architecture.md`
- `docs/data_model.md`
- `docs/pipeline_spec.md`
- `docs/agent_instructions.md`

---

## 🔷 Sprint 0 — Bootstrap the Repo (Foundation)
**Goal:** Create a functioning repo environment with configs + skeleton folders.

**Deliverables**
- Repository initialized with full folder structure
- `settings.yaml`, `data_sources.yaml`, `regimes.yaml`
- `src/core/` implemented: `utils.py`, `io.py`, `types.py`
- `.gitignore`, `requirements.txt` or `pyproject.toml`

**Definition of Done**
- Project imports successfully
- Can load config & write/read Parquet from `/data/`

---

## 🔷 Sprint 1 — Data Pipeline + Processed Bars

**Goal:** Load raw OHLCV → produce canonical processed data.

**Tasks**
- Implement loaders + preprocessing modules
- Save to `data/processed/<ticker>.parquet`
- Add synthetic tests validating schema & date consistency

**Deliverables**
- `src/data/loaders.py`
- `src/data/preprocessing.py`
- `src/pipeline/preprocess_data.py`
- `tests/test_data_preprocessing.py`

**Definition of Done**
- Running preprocess step generates valid processed files from raw input

---

## 🔷 Sprint 2 — Feature Engine

**Goal:** Compute trend, vol, volume, and relative-strength features.

**Tasks**
- Implement `src/features/*`
- Build unified pipeline to store features
- Add tests using synthetic bars

**Deliverables**
- `src/pipeline/build_features.py`
- Feature Parquet files for each ticker
- `tests/test_features.py`

**Definition of Done**
- Features persist correctly and match schemas in `docs/data_model.md`

---

## 🔷 Sprint 3 — Rule-Based Signals + Regime Engine

**Goal:** Produce base alpha signals + market regime labels.

**Tasks**
- Implement alphas:
  - trend_alpha
  - mean_reversion_alpha
  - volatility_alpha
  - relative_strength_alpha
- Implement rule-based regime engine
- Wire pipeline modules
- Minimal tests confirming scoring logic on synthetic data

**Deliverables**
- `src/pipeline/build_signals.py`
- `models/regime/rule_based_regime.py`
- `src/pipeline/run_regime_engine.py`
- `tests/test_signals.py`
- `tests/test_regime.py`

**Definition of Done**
- Signals & regimes persist and can be joined downstream

---

## 🔷 Sprint 4 — ML Models (Next-State Prediction)

**Goal:** Train LightGBM models to predict future state distribution.

**Tasks**
- Implement label creation (state buckets)
- Implement LightGBM training + model registry
- Implement prediction pipeline
- Tests verifying:
  - proper label assignment
  - training + inference API functionality

**Deliverables**
- `models/ml/lightgbm_next_state.py`
- `models/ml/model_registry.py`
- `src/features/label_targets.py`
- `src/pipeline/train_ml_models.py`
- `src/pipeline/run_predictions.py`
- `tests/test_models.py`

**Definition of Done**
- Model artifacts saved to `models/ml/artifacts/*`
- Probabilities saved to `data/predictions/*`

---

## 🔷 Sprint 5 — Meta-Model + Position Sizing

**Goal:** Combine all signals and predictions into final alpha + trade weights.

**Tasks**
- Implement rule-based meta-model using regime weights
- Map alpha score → position weights via vol targeting
- Write pipeline orchestration
- Add synthetic tests validating sizing + clipping behavior

**Deliverables**
- `src/meta/rule_based_meta.py`
- `src/risk/position_sizing.py`
- `src/risk/risk_metrics.py`
- `src/pipeline/run_meta_model.py`
- `src/pipeline/run_position_sizing.py`
- `tests/test_meta.py`
- `tests/test_risk.py`

**Definition of Done**
- Persistent `data/meta/alpha_scores/*` and `data/positions/<strategy>/*`

---

## 🔷 Sprint 6 — Backtester + Reporting

**Goal:** Simulate historical performance using computed positions.

**Tasks**
- Implement backtest engine
- Implement metrics (Sharpe, drawdown, etc.)
- Write reports to JSON + Parquet
- Add end-to-end synthetic tests

**Deliverables**
- `src/backtest/engine.py`
- `src/backtest/metrics.py`
- `src/backtest/reports.py`
- `src/pipeline/run_backtest.py`
- `tests/test_backtest.py`

**Definition of Done**
- Running `scripts/run_full_backtest.py` outputs:
  - `trades.parquet`
  - `pnl_timeseries.parquet`
  - `summary.json`

---

## 🔷 Sprint 7 — Glue Scripts + Developer UX

**Goal:** Make system usable end-to-end from the command line.

**Tasks**
- Implement:
  - `scripts/run_full_backtest.py`
  - `scripts/run_daily_update.py`
  - `scripts/inspect_signals.py`
- Add example config + sample data
- Add demo README examples

**Definition of Done**
- Full backtest runs via single script
- Daily update runs incrementally

---

## 🔷 Sprint 8 — Enhancements & Validation

**Goal:** Improve robustness and prep for evolution to live system.

**Tasks**
- Add PnL by regime reporting
- Add contribution columns for meta-model explainability
- Optimize pipelines for speed + incremental runs
- Add stress tests + data sanity checks

**Definition of Done**
- All layers observable and debuggable
- Backtests reproducible end-to-end

---

## 🔷 Optional Extended Sprints (Roadmap)

| Sprint | Focus |
|--------|--------|
| 9 | Transformer-based sequence models |
| 10 | Causal inference / DoWhy |
| 11 | Multi-asset allocation (HRP, ERC, RP) |
| 12 | Execution modeling (slippage, IBKR integration) |
| 13 | Real-time live trading |

---

## 🏁 Completion Requirements

To declare MVP complete:

- Full backtest pipeline runs start→finish without manual steps
- All core modules behave according to `docs/*.md`
- Models, signals, positions, PnL persist in Parquet
- Synthetic tests pass
- Performance metrics computed

---

## 📍 Status Tracking

| Sprint | Status | Notes |
|--------|--------|-------|
| Sprint 0 | ☐ |
| Sprint 1 | ☐ |
| Sprint 2 | ☐ |
| Sprint 3 | ☐ |
| Sprint 4 | ☐ |
| Sprint 5 | ☐ |
| Sprint 6 | ☐ |
| Sprint 7 | ☐ |
| Sprint 8 | ☐ |

