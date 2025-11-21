# Hybrid Alpha Trading System — Data Model

This document defines the **data schemas** used across the pipeline. All modules and scripts should adhere to these structures for compatibility and reproducibility.

## 1. Conventions

- **Storage format:** Parquet preferred. CSV can be used for debugging or export.
- **Indexing:**
  - Primary index: `(date, ticker)` where applicable.
  - `date` is trading date (timezone-agnostic, `YYYY-MM-DD`).
- **Naming:**
  - All column names are `snake_case`.
  - Files are grouped under `/data/<layer>/<ticker>.parquet` where relevant.
- **Types (logical):**
  - `DATE` → trading date
  - `STRING` → text labels, IDs
  - `FLOAT` → numeric with decimals
  - `INT` → integers
  - `BOOL` → boolean

---

## 2. Raw & Processed Market Data

### 2.1 Raw OHLCV (`data/raw/`)

Raw input from external providers. Schema may vary, but internal code should map it into the **processed** schema below.

**Location:**
- `data/raw/<ticker>_raw.parquet`

**Canonical internal schema (after mapping):**

| Column   | Type   | Description                              |
|----------|--------|------------------------------------------|
| date     | DATE   | Trading date                             |
| open     | FLOAT  | Open price                               |
| high     | FLOAT  | High price                               |
| low      | FLOAT  | Low price                                |
| close    | FLOAT  | Close price                              |
| adj_close| FLOAT  | Adjusted close (if available)            |
| volume   | FLOAT  | Traded volume                            |
| ticker   | STRING | Asset symbol (e.g., NVDA, BTC-USD, SPY)  |

---

### 2.2 Processed Bars (`data/processed/`)

Cleaned and standardized OHLCV.

**Location:**
- `data/processed/<ticker>.parquet`

**Schema:**

| Column   | Type   | Description                                      |
|----------|--------|--------------------------------------------------|
| date     | DATE   | Trading date (unique per ticker)                 |
| open     | FLOAT  | Cleaned open price                               |
| high     | FLOAT  | Cleaned high price                               |
| low      | FLOAT  | Cleaned low price                                |
| close    | FLOAT  | Cleaned close price                              |
| adj_close| FLOAT  | Adjusted close (forward/back adjusted if needed) |
| volume   | FLOAT  | Cleaned volume                                   |
| ticker   | STRING | Asset symbol                                     |

**Constraints:**
- One row per `(ticker, date)`.
- No duplicate dates for same ticker.
- Missing days should be either filled or explicitly absent depending on config.

---

## 3. Features Layer (`data/features/`)

Per-ticker, per-date engineered features (trend, vol, volume, relative strength, etc.).

**Location:**
- `data/features/<ticker>.parquet`

**Base schema (extensible):**

| Column                    | Type   | Description                                              |
|---------------------------|--------|----------------------------------------------------------|
| date                      | DATE   | Trading date                                             |
| ticker                    | STRING | Asset symbol                                             |
| ret_1d                    | FLOAT  | 1-day return (close/prev_close - 1)                      |
| ret_5d                    | FLOAT  | 5-day return                                             |
| ret_20d                   | FLOAT  | 20-day return                                            |
| sma_10                    | FLOAT  | 10-day simple moving average                            |
| sma_20                    | FLOAT  | 20-day simple moving average                            |
| sma_50                    | FLOAT  | 50-day simple moving average                            |
| sma_200                   | FLOAT  | 200-day simple moving average                           |
| dist_to_sma_20            | FLOAT  | (close - sma_20) / sma_20                               |
| dist_to_sma_50            | FLOAT  | (close - sma_50) / sma_50                               |
| dist_to_sma_200           | FLOAT  | (close - sma_200) / sma_200                             |
| momentum_20               | FLOAT  | 20-day return / 20-day vol                              |
| realized_vol_10           | FLOAT  | Annualized realized vol over 10 days                    |
| realized_vol_20           | FLOAT  | Annualized realized vol over 20 days                    |
| realized_vol_60           | FLOAT  | Annualized realized vol over 60 days                    |
| atr_14                    | FLOAT  | 14-day Average True Range (normalized if desired)       |
| intraday_range_pct        | FLOAT  | (high - low) / close                                    |
| volume_z_20               | FLOAT  | Volume z-score vs 20-day mean                           |
| volume_to_20d_avg         | FLOAT  | volume / mean(volume_20d)                               |
| rel_ret_vs_benchmark_20   | FLOAT  | Asset 20d return - benchmark 20d return                 |
| rel_ret_vs_benchmark_60   | FLOAT  | Asset 60d return - benchmark 60d return                 |
| beta_vs_benchmark_60      | FLOAT  | Rolling 60d beta vs benchmark (e.g., SPY)               |

**Notes:**
- This table is **append-only** as history grows.
- New feature columns can be added without breaking existing logic, as long as code handles missing columns gracefully.

---

## 4. Signals Layer (`data/signals/`)

Rule-based alpha signals from features. Each signal is a continuous score in `[-1, 1]` unless otherwise specified.

**Location:**
- `data/signals/<ticker>.parquet`

**Schema:**

| Column              | Type   | Description                                     |
|---------------------|--------|-------------------------------------------------|
| date                | DATE   | Trading date                                    |
| ticker              | STRING | Asset symbol                                    |
| trend_alpha         | FLOAT  | Trend signal score in [-1, 1]                  |
| mean_reversion_alpha| FLOAT  | Mean reversion signal score in [-1, 1]         |
| vol_alpha           | FLOAT  | Volatility-context signal score in [-1, 1]     |
| rel_strength_alpha  | FLOAT  | Relative strength signal score in [-1, 1]      |

**Extensions:**
- Additional signals should be added as new columns with `_alpha` suffix or clear naming like `signal_<name>`.

---

## 5. Regime Layer (`data/regimes/`)

Market regime states, typically computed at the benchmark/index level (e.g., SPY, QQQ, BTC index).

**Location:**
- `data/regimes/<benchmark>.parquet`  
  Example: `data/regimes/SPY.parquet`

**Schema:**

| Column            | Type   | Description                                      |
|-------------------|--------|--------------------------------------------------|
| date              | DATE   | Trading date                                     |
| benchmark         | STRING | Benchmark symbol (e.g., SPY, QQQ)                |
| regime_label      | STRING | One of {bull, bear, choppy, crash}              |
| regime_id         | INT    | Encoded regime: e.g., 0=bull,1=bear,2=choppy,3=crash |
| regime_prob_bull  | FLOAT  | Probability of bull regime                      |
| regime_prob_bear  | FLOAT  | Probability of bear regime                      |
| regime_prob_choppy| FLOAT  | Probability of choppy regime                    |
| regime_prob_crash | FLOAT  | Probability of crash regime                     |

**Notes:**
- Probabilities may originate from HMM or soft assignment rules.
- `regime_label` should be consistent with config (`config/regimes.yaml`).

---

## 6. ML Labels & Predictions (`data/predictions/`)

### 6.1 Labels (for training)

If labels are stored, they can be kept as a separate table or merged into features. Recommended:

**Location:**
- `data/features/<ticker>.parquet` (as extra columns) or
- `data/labels/<ticker>.parquet` (optional separate file)

**Label columns:**

| Column               | Type   | Description                                      |
|----------------------|--------|--------------------------------------------------|
| target_state_h1      | INT    | Next-state label for horizon 1 (e.g., -2…+3)    |
| target_state_h3      | INT    | Next-state label for horizon 3                  |
| target_state_h5      | INT    | Next-state label for horizon 5                  |

---

### 6.2 Predictions

Per ticker, per date, model-generated state probabilities and chosen prediction.

**Location:**
- `data/predictions/<ticker>.parquet`

**Schema:**

| Column                    | Type   | Description                                           |
|---------------------------|--------|-------------------------------------------------------|
| date                      | DATE   | Prediction timestamp (aligned to feature date)        |
| ticker                    | STRING | Asset symbol                                          |
| horizon                   | INT    | Prediction horizon in days (e.g., 1, 3, 5)           |
| model_name                | STRING | Identifier for model (e.g., lightgbm_v1)             |
| pred_state                | INT    | Predicted discrete state (e.g., -2, -1, 0, 1, 2, 3)  |
| prob_pred_state           | FLOAT  | Probability of `pred_state`                          |
| prob_state_m2             | FLOAT  | Probability of state -2                              |
| prob_state_m1             | FLOAT  | Probability of state -1                              |
| prob_state_0              | FLOAT  | Probability of state 0                               |
| prob_state_p1             | FLOAT  | Probability of state +1                              |
| prob_state_p2             | FLOAT  | Probability of state +2                              |
| prob_state_p3             | FLOAT  | Probability of state +3                              |

**Notes:**
- State set is configurable but should remain consistent per model.
- For multiple horizons, either:
  - store multiple rows per `(date, ticker)` with different `horizon`, or
  - store separate files per horizon (config dependent).

---

## 7. Meta-Model Alpha Scores (`data/meta/alpha_scores/`)

Combined alpha output after blending signals, predictions, and regimes.

**Location:**
- `data/meta/alpha_scores/<ticker>.parquet`

**Schema:**

| Column              | Type   | Description                                         |
|---------------------|--------|-----------------------------------------------------|
| date                | DATE   | Trading date                                        |
| ticker              | STRING | Asset symbol                                        |
| alpha_score         | FLOAT  | Final combined alpha in [-1, 1]                     |
| alpha_confidence    | FLOAT  | Optional confidence metric (e.g., |alpha| scaled)   |
| contrib_trend       | FLOAT  | Contribution from trend_alpha                       |
| contrib_mean_rev    | FLOAT  | Contribution from mean_reversion_alpha              |
| contrib_vol         | FLOAT  | Contribution from vol_alpha                         |
| contrib_rel_strength| FLOAT  | Contribution from rel_strength_alpha                |
| contrib_ml          | FLOAT  | Contribution from ML prediction                     |
| regime_label        | STRING | Regime used for weighting (for debugging/explainer) |

**Notes:**
- Contribution columns are optional but very useful for introspection.
- `alpha_score` is what the risk/position layer acts on.

---

## 8. Positions (`data/positions/`)

Desired position sizing output after risk layer.

**Location:**
- `data/positions/<strategy_name>/<ticker>.parquet`

**Schema:**

| Column            | Type   | Description                                           |
|-------------------|--------|-------------------------------------------------------|
| date              | DATE   | Trading date                                         |
| ticker            | STRING | Asset symbol                                         |
| strategy_name     | STRING | Name/ID of strategy                                  |
| target_weight     | FLOAT  | Desired portfolio weight in [-1, 1] (short/long)    |
| target_dollar_pos | FLOAT  | Desired dollar exposure (optional)                  |
| realized_vol_lookback | FLOAT | Vol used in sizing (e.g., 20d realized vol)     |
| max_weight_applied| BOOL   | True if position was clipped by max weight rules    |

**Notes:**
- `target_weight` is typically the main control field for backtesting.
- Additional per-asset risk flags (e.g., `suspended`, `illiquid`) can be added later.

---

## 9. Trades (`data/backtests/<strategy_name>/trades/`)

Trade-level history generated by the backtest engine.

**Location:**
- `data/backtests/<strategy_name>/trades.parquet`  
  or  
- `data/backtests/<strategy_name>/trades/<ticker>.parquet`

**Schema:**

| Column        | Type   | Description                                         |
|---------------|--------|-----------------------------------------------------|
| datetime      | DATE   | Execution date (or datetime if higher freq later)   |
| ticker        | STRING | Asset symbol                                        |
| strategy_name | STRING | Strategy identifier                                 |
| side          | STRING | 'BUY' or 'SELL'                                     |
| quantity      | FLOAT  | Number of units traded                              |
| price         | FLOAT  | Execution price                                     |
| notional      | FLOAT  | `quantity * price`                                  |
| fees          | FLOAT  | Commission / fees (if modeled)                      |
| reason        | STRING | Optional text or categorical reason (e.g., 'rebalance','enter','exit') |

---

## 10. PnL & Backtest Summary (`data/backtests/<strategy_name>/`)

### 10.1 Daily PnL Time Series

**Location:**
- `data/backtests/<strategy_name>/pnl_timeseries.parquet`

**Schema:**

| Column        | Type   | Description                                          |
|---------------|--------|------------------------------------------------------|
| date          | DATE   | Trading date                                        |
| strategy_name | STRING | Strategy identifier                                 |
| portfolio_value | FLOAT| Total portfolio value (normalized or actual)        |
| daily_return  | FLOAT  | Daily portfolio return                              |
| drawdown      | FLOAT  | Drawdown from peak                                  |
| gross_exposure| FLOAT  | Sum of absolute weights or notional                 |
| net_exposure  | FLOAT  | Net sum of weights or notional                      |
| regime_label  | STRING | Regime on that date (from regime table)             |

---

### 10.2 Summary Metrics

**Location:**
- `data/backtests/<strategy_name>/summary.json`

**Example fields:**

{
  "strategy_name": "hybrid_alpha_mvp",
  "start_date": "2015-01-01",
  "end_date": "2025-01-01",
  "sharpe": 1.25,
  "sortino": 1.80,
  "max_drawdown": -0.23,
  "cagr": 0.18,
  "win_rate": 0.56,
  "avg_trade_return": 0.004,
  "num_trades": 1200,
  "pnl_by_regime": {
    "bull": 0.65,
    "bear": 0.20,
    "choppy": 0.10,
    "crash": 0.05
  }
}

11. Relationships Overview

High-level relational view:

processed bars (per ticker)
   → features (per ticker, date)
       → signals (per ticker, date)
       → labels (per ticker, date; for training)
       → predictions (per ticker, date; for inference)
regimes (per benchmark, date)
   + alpha_scores (per ticker, date)
   → positions (per ticker, date, strategy)
   → backtest engine
       → trades (per strategy)
       → pnl_timeseries (per strategy)
       → summary.json


All joins should generally be done on (date, ticker) plus benchmark/strategy_name where relevant.
