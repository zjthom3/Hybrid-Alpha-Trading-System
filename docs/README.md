# Hybrid Alpha Trading System

A modular, research-focused trading framework modeled after institutional quant pipelines.  
The system forecasts market states, combines multiple alpha signals, applies regime-aware weighting, and outputs position sizes for backtesting or live inference.

This project is designed for:
- Multi-signal alpha modeling
- Regime-based prediction (bull, bear, choppy, crash)
- Machine learning forecasting (LightGBM, sequence models later)
- Volatility-aware position sizing
- End-to-end reproducible backtests

> Think of this as a mini quant fund tech stack—not a one-model prediction tool.

---

## 🔧 Core Philosophy

Traditional retail models try to “predict the price.”  
Institutional models blend **many small edges**:

features → signals → ML → regime → meta-model → sizing → execution


Each component is independent and testable.

---

## 📂 Repository Structure


├── docs/ # PRD, architecture, pipeline specs
├── config/ # settings, data paths, regime rules
├── data/ # raw/processed/features/predictions/etc.
├── models/ # ML + regime models + artifacts
├── src/
│ ├── core/ # types, IO helpers, config loader
│ ├── data/ # preprocessing, loaders
│ ├── features/ # trend/vol/volume/RS factor builders
│ ├── signals/ # rule-based alpha signals
│ ├── meta/ # signal weighting + aggregation
│ ├── risk/ # sizing based on vol + caps
│ ├── backtest/ # engine, metrics, reports
│ └── pipeline/ # orchestration entrypoints
├── scripts/ # run_full_backtest.py, daily_update.py
├── tests/ # synthetic test suites
└── BACKLOG.md # implementation roadmap


---

## 🚀 Features

| Component | Purpose |
|----------|---------|
| **Feature Engine** | trend, momentum, vol, beta, volume stats |
| **Alpha Signals** | interpretable rule-based signals in [-1,1] |
| **ML Predictions** | LightGBM state forecasts (1,3,5 day horizons) |
| **Regime Engine** | HMM or rule-based bull/bear/choppy/crash |
| **Meta-Model** | combines signals + ML + regime weights |
| **Risk Layer** | volatility targeting + position caps |
| **Backtester** | daily event-driven sim w/ metrics + PnL files |

Everything writes persistent artifacts so you can inspect every layer.

---

## 🔌 Data Model Summary

All data is stored locally in Parquet:

| Layer | Path Example |
|-------|-------------|
| Processed Bars | `data/processed/NVDA.parquet` |
| Features | `data/features/NVDA.parquet` |
| Signals | `data/signals/NVDA.parquet` |
| Predictions | `data/predictions/NVDA.parquet` |
| Regimes | `data/regimes/SPY.parquet` |
| Alpha Scores | `data/meta/alpha_scores/NVDA.parquet` |
| Positions | `data/positions/hybrid_alpha_mvp/NVDA.parquet` |
| Backtests | `data/backtests/hybrid_alpha_mvp/` |

Full schema definitions are in:



docs/data_model.md


---

## 🧪 Running a Full Backtest

Once modules are implemented:

python scripts/run_full_backtest.py --config config/settings.yaml


This will:

preprocess data

build features

generate signals

infer regime

train ML models (optional)

run predictions

compute alpha scores

compute positions

simulate a backtest

Output will be written to:

data/backtests/<strategy_name>/

🔄 Daily Update (Live Mode)

Assumes new bars are already saved to data/raw/.

python scripts/run_daily_update.py


Outputs new positions for the next session.

🧱 Development Workflow
For Human Developers

Make changes in src/

Keep logic modular

Update tests + docs when changing contracts

Run tests with pytest

For AI Agent Developers

Read specs in this order:

docs/prd.md

docs/architecture.md

docs/data_model.md

docs/pipeline_spec.md

docs/agent_instructions.md

Follow tasks in BACKLOG.md

Write code in small, testable modules

Do not change schemas silently

📌 Status
Component	Status
Repo skeleton	☐
Data preprocessing	☐
Feature engine	☐
Signals	☐
Regime engine	☐
ML prediction	☐
Meta-model	☐
Risk sizing	☐
Backtester	☐

Track progress in BACKLOG.md.

🌱 Future Enhancements

Transformer-based sequence models

Causal inference (DoWhy)

Options & implied volatility surface features

Multi-asset allocation (HRP, ERC, risk parity)

Execution modeling (slippage, live order routing)

⚠ Disclaimer

This repository is for research purposes only.
No execution or brokerage hooks are included by default.

It does not constitute trading advice.
