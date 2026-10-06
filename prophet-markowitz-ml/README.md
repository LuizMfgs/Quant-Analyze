# Prophet → Markowitz pipeline

Python pipeline behind the dashboard. See the [root README](../README.md) for the overview, the disclaimer and the dashboard setup.

## Quick start

```bash
pip install -e .                      # or: poetry install
forecast-portfolio run                # uses the cached CSVs in data/raw
forecast-portfolio run --refresh      # re-download prices via yfinance
```

Run it from this folder (`cache_dir` in `config/settings.yaml` is relative). Results go to `outputs/`.

## Layout

```
config/settings.yaml      tickers, horizon, constraints, portfolio size
src/forecast_portfolio/
  config.py               YAML → pydantic Settings
  data.py                 CSV cache + yfinance loader
  forecast.py             Prophet per asset + 60-day holdout metrics
  optimize.py             Markowitz QP (scipy SLSQP), frontier, allocation
  pipeline.py             orchestration, exports JSON
  cli.py                  `forecast-portfolio run`
data/raw/*.csv            cached closing prices (Date, Close)
outputs/                  results.json, prices.csv, allocation.csv
```

## How the optimisation works

- **μ**: terminal value of each Prophet path vs last close, annualised: `(1+r_h)^(365/h) − 1`.
- **Σ**: daily returns, Ledoit–Wolf shrunk, ×252.
- **Problem**: `min w'Σw` s.t. `Σwᵢ = 1`, `0 ≤ wᵢ ≤ 0.35`; max-Sharpe via SLSQP on `−(μ'w − rf)/√(w'Σw)`.
- **Rebalance**: greedy whole-share allocation at the last close; leftover stays in cash.
