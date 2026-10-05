# Market Analyzer

A machine learning project that combines time-series forecasting with portfolio optimization:

1. Loads 2 years of daily prices for 10 assets (AAPL, MSFT, GOOGL, AMZN, NVDA, JPM, XOM, JNJ, GLD, TLT).
2. Forecasts each asset 90 days ahead with **Prophet**, validated on a 60-day holdout.
3. Turns the forecasts into expected returns and estimates risk with a **Ledoit-Wolf** covariance matrix.
4. Solves the **Markowitz** problem (efficient frontier, max-Sharpe, minimum volatility).
5. Computes a whole-share allocation for a $10k portfolio.
6. Exports everything to `outputs/results.json`, which feeds the React dashboard.

> **Disclaimer:** This is an educational project built for learning purposes only. It is **not** investment advice, a recommendation to buy or sell any security, or a product or tool to support investment decisions. See [Disclaimer](#disclaimer).

## Structure

```
prophet-markowitz-ml/   Python pipeline (Prophet + Markowitz)
  config/settings.yaml  tickers, horizon, constraints, portfolio size
  data/raw/             cached prices (CSV)
  outputs/              results.json, allocation.csv, prices.csv
  src/forecast_portfolio/
app/                    dashboard (React + Vite + Tailwind + Recharts)
```

## Requirements

- Python 3.10, 3.11 or 3.12 (this project does not support 3.13+)
- Node.js 20 or higher (dashboard only)

## Installation and usage

### Pipeline (Python)

```powershell
cd prophet-markowitz-ml
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Linux/macOS: source .venv/bin/activate
pip install -e .
forecast-portfolio run
```

To download fresh data from Yahoo Finance instead of using the cache:

```powershell
forecast-portfolio run --refresh
```

Results are written to `prophet-markowitz-ml/outputs/`.

### Dashboard (React)

```powershell
cd app
npm install
npm run dev
```

Open `http://localhost:3000`. To create a production build: `npm run build`.

The dashboard reads `app/src/data/results.ts`, a static copy of `results.json`. After running the pipeline with new data, regenerate that file:

```powershell
$json = [System.IO.File]::ReadAllText((Resolve-Path prophet-markowitz-ml\outputs\results.json).Path)
$ts = "import type { Results } from `"@/types/results`";`n`nexport const results: Results = $json;`n"
[System.IO.File]::WriteAllText((Join-Path (Resolve-Path app).Path "src\data\results.ts"), $ts, (New-Object System.Text.UTF8Encoding($false)))
```

## Configuration

Edit `prophet-markowitz-ml/config/settings.yaml`:

| Key | What it controls |
|---|---|
| `tickers` | assets analyzed |
| `forecast.horizon_days` / `test_days` | forecast horizon and holdout window |
| `optimization.weight_bounds` | per-asset limit (default: 0% to 35%) |
| `optimization.risk_free_rate` | risk-free rate (default: 4%) |
| `rebalance.portfolio_value` | portfolio size in dollars |

## Limitations

- Prophet extrapolates trend and seasonality: it cannot see earnings, news or regime changes. On trending stocks it produces overly aggressive expected returns, which inflates the Sharpe ratio of the max-Sharpe portfolio.
- Two years of daily data is thin for estimating yearly seasonality and a stable covariance matrix.

## Disclaimer

This project is for **educational purposes only**. It demonstrates how time-series forecasting and mean-variance optimization can be combined, and it is not meant to be used for real investing.

- It is **not** investment advice, financial advice, or a recommendation to buy, sell or hold any asset.
- It is **not** a product or service to assist investment decisions, and it should not be used as one.
- Forecasts and allocations produced here are unreliable by design (see Limitations) and past data does not predict future results.
- The author is not a financial advisor and accepts no responsibility for any losses resulting from the use of this code or its outputs. Do your own research and consult a qualified professional before making any investment decision.
