# Prophet → Markowitz: Forecast-Driven Portfolio Optimisation

An end-to-end machine-learning project that

1. **ingests** 2 years of daily prices for 10 assets (free data sources),
2. **forecasts** each series 90 days forward with **Meta Prophet** (one model per asset, with holdout validation),
3. turns the forecasts into expected returns **μ** and estimates risk **Σ** with Ledoit–Wolf shrinkage,
4. solves the **Markowitz** mean-variance problem (efficient frontier, max-Sharpe, min-volatility),
5. **rebalances** a $10k portfolio into whole-share orders, and
6. exports everything to `outputs/results.json` for the dashboard.

## Quick start

```bash
poetry install                    # core deps
poetry install -E pypfopt         # optional: PyPortfolioOpt backend
poetry run forecast-portfolio run # full pipeline (uses cached CSVs)
poetry run forecast-portfolio run --refresh   # re-download data via yfinance
```

Without Poetry: `pip install -e .` works too (PEP 621 metadata in `pyproject.toml`).

## Project layout

```
config/settings.yaml      # tickers, horizon, constraints, book size
src/forecast_portfolio/
  config.py               # YAML → pydantic Settings
  data.py                 # CSV cache + yfinance loader
  forecast.py             # Prophet per asset + 60-day holdout metrics
  optimize.py             # Markowitz QP (scipy SLSQP), frontier, allocation
  pipeline.py             # orchestration, exports JSON
  cli.py                  # `forecast-portfolio run`
data/raw/*.csv            # cached price history
outputs/                  # results.json, prices.csv, allocation.csv
```

## How the optimisation works

- **μ** — terminal value of each Prophet path vs last close, annualised: `(1+r_h)^(365/h) − 1`.
- **Σ** — daily log-close returns, Ledoit–Wolf shrunk, ×252.
- **Problem** — `min w'Σw` s.t. `Σwᵢ = 1`, `0 ≤ wᵢ ≤ 0.35`; max-Sharpe via SLSQP on `−(μ'w − rf)/√(w'Σw)`.
- **Rebalance** — greedy whole-share allocation at last close, leftover stays in cash.

## Recommended free toolchain

| Stage | Tool (used here) | Free alternatives |
|---|---|---|
| Env & deps | **Poetry** | uv, pip-tools |
| Market data | **yfinance** (Yahoo Finance) | Stooq, Nasdaq Data Link free tier, Alpha Vantage free tier |
| Forecasting | **Prophet** | NeuralProphet, statsmodels SARIMAX, Darts |
| Validation | holdout + MAPE/RMSE | `prophet.diagnostics.cross_validation`, sktime |
| Optimisation | **scipy SLSQP** (self-contained) | PyPortfolioOpt (optional extra), cvxpy, Riskfolio-Lib |
| Tracking | JSON artifacts | MLflow OSS, DVC |
| Automation | GitHub Actions free cron | cron + make, Prefect OSS |
| Dashboard | React + Vite + Recharts | Plotly Dash, Streamlit |

## Honest caveats

- Prophet extrapolates trend/seasonality; it cannot see earnings, news, or regime breaks. On trending stocks it produces aggressive μ (e.g. triple-digit annualised), which inflates the max-Sharpe Sharpe — classic "garbage in, gospel out" for mean-variance. Shrink μ toward 0 or the cross-sectional mean before trusting it.
- 2 years of daily data is thin for yearly seasonality (disabled in config) and for covariance stability — hence Ledoit–Wolf.
- Educational project, not investment advice.
