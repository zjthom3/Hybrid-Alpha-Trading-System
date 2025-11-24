📌 PRD — Hybrid Alpha Trading System
1. Overview

Build a modular, data-driven trading system that predicts future market states, aggregates multiple alpha signals, dynamically weights them using a regime-aware meta-model, and outputs position sizing instructions with full backtesting support. System must be modular, testable, and support historical and live inference.

2. Core Objectives

Predict the next state of a financial asset over multiple horizons (1–5 units).

Combine multiple alpha sources (feature-based + ML + regime).

Apply regime-aware signal weighting to improve reliability across market phases.

Output position sizes, not just predictions.

Run on both historical data (backtests) and live mode.

Expose outputs for future UI (state strip visualization).

3. Scope (Initial MVP)

Included:

Data ingestion from CSV/Parquet files (manual import at first)

Feature generation (price, trend, vol, relative strength)

Base alpha signals (rule-based)

Gradient-boosting model for next-state prediction

Regime engine (HMM or trend-based)

Meta-model combining signals

Vol-adjusted position sizing

Local backtester (not production execution)

Not Included (future phases):

Real-time exchange execution

Options pricing integration

True microstructure-level execution algos

Multi-asset optimization / portfolio rebalancing

4. Data Inputs
Source	Format	Required?	Notes
OHLCV Daily	Parquet or CSV	Yes	min 5 years history
Benchmark Index (e.g., SPY)	Same format	Yes	for regime tagging
Features table	Generated internally	Yes	stored persistently
Signals table	Generated internally	Yes	continuous scores
Predictions table	Generated	Yes	model output
Trades & PnL tables	Generated	Yes	from backtester

Data storage format:

/data/raw/

/data/processed/

/data/features/

/data/signals/

/data/predictions/

/data/backtests/

File format standard: Parquet preferred

5. Feature Engine Requirements

Generate reusable numerical features for each (ticker, date):

Trend Features

SMA 10/20/50/200

Distance from MA normalized

Rolling returns (1–60 days)

Momentum score (return / vol)

Volatility Features

Realized vol (10/20/60 day)

ATR

Intraday range percent

Volume Features

Volume z-score

Volume/float

Money flow style features

Relative Strength

return_vs_SPY (rolling)

beta_vs_index (rolling regression)

All features stored as columns, not dictionaries.

6. Alpha Signal Layer

Each signal outputs a continuous score [-1, 1].

Initial signals:

Name	Type	Logic Summary
trend_alpha	rule	trend MA stack + distance
mean_reversion	rule	±2σ reaction under non-trend
vol_alpha	rule	low vol = trend favorable
rel_strength	rule	cross-asset comparison

Signals stored in /data/signals/.

7. ML Prediction Layer (Next-State Forecast)

Target: probability distribution across discrete future states:
{-2, -1, 0, +1, +2, +3} (configurable)

Horizon: multiple (1, 3, 5 days ahead)

Model Type for MVP:
LightGBM Classifier

Training Requirements

walk-forward splits

features must be normalized per window

store model artifacts versioned

Output Fields

pred_state

prob_pred_state

prob_dist

Stored in /data/predictions/.

8. Market Regime Engine

Purpose: adjust weights based on macro context.

Initial Implementation Options:

Hidden Markov Model on returns + volatility

OR simple trend + vol threshold rules

Regime States:

bull

bear

choppy

crash

Each assigned numeric flag + probability score.

Stored in /data/regimes/.

9. Meta-Model (Signal Aggregation)

Output: unified alpha score: [-1, 1]

MVP Approach: rule-based weighting table

Example roadmap:

Regime	trend_w	meanrev_w	ml_w	vol_w
bull	0.5	0.1	0.4	0.2
bear	0.2	0.4	0.4	0.3
choppy	0.1	0.6	0.3	0.2
crash	0	0	0.2	0.6

Future Version: learned stacking model.

Output stored to /data/meta/alpha_scores/.

10. Position Sizing Layer

Input: alpha_score, realized vol, regime

Sizing formula:

target_vol = 0.15 (configurable)
position = alpha_score * (target_vol / asset_vol)
position = clamp(min=-max_pos, max=max_pos)


Constraints:

max position per asset (e.g., 10%)

global net exposure limits

reduce exposure during drawdown

Output: daily position vector.

11. Backtesting Engine

Mode: event-driven backtester (daily resolution)

Requirements:

simulate PnL based on executed positions

track:

Sharpe

max drawdown

win rate

PnL by regime

PnL by signal

Store results in /backtests/<strategy_name>/.

12. Deployment Modes

Backtest Mode

run full pipeline historically

Live Inference Mode

read latest data

refresh features → signals → predictions → alpha → position

save outputs to local storage

13. Success Metrics
Metric	Target
Directional accuracy	>54% for liquid large caps
Sharpe (unlevered)	>1.0 baseline
Max drawdown	<25%
Data freshness	<24h lag
Fully reproducible backtests	Yes
14. Future Extensions (planned but not in MVP)

Multi-asset optimization (risk parity, HRP)

Options surface signals + volatility trading

Live brokerage execution (Interactive Brokers / Alpaca)

Transformer-based sequence models

Causal inference engine (Do-Why)
