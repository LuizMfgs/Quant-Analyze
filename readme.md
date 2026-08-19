
## Key features

- **Return forecasting** — pooled LightGBM on lagged returns + technicals,
  GARCH(1,1) volatility, with random-walk and historical-mean baselines
- **Robust optimization** — Black-Litterman blends model forecasts with an
  equilibrium prior; per-asset view uncertainty derived from walk-forward
  residuals; Ledoit-Wolf shrinkage; HRP and min-variance benchmarks
- **Cost-aware rebalancing** — drift bands and minimum-turnover thresholds,
  so you only trade when it pays
- **Leakage-proof evaluation** — walk-forward harness with realized-label
  training rule, plus unit tests that prove features are trailing-only
- **Supabase backend** — Postgres for prices/forecasts/weights, Storage for
  model artifacts, model registry with auto-deactivation of stale models
- **Streamlit dashboard** — current weights, forecast-vs-realized scatter,
  rolling IC, and net-of-cost performance vs. equal-weight benchmark
- **Scheduled via GitHub Actions** — zero-infrastructure daily runs after
  market close

## Tech stack

Python · LightGBM · arch (GARCH) · PyPortfolioOpt · scikit-learn ·
pandas · Supabase (Postgres + Storage) · Streamlit · Plotly ·
QuantStats · yfinance · GitHub Actions · Docker

## Quickstart

```bash
# 1. Create a Supabase project and run sql/001_schema.sql in the SQL editor
# 2. Configure secrets
cp .env.example .env        # fill in DATABASE_URL, SUPABASE_URL, SUPABASE_SERVICE_KEY

# 3. Install
pip install -r requirements.txt

# 4. Load history (~10y of daily bars)
python -m quant.pipeline backfill

# 5. Verify no lookahead bugs
pytest tests/ -q

# 6. Run the full pipeline (ingest → forecast → optimize → rebalance decision)
python -m quant.pipeline daily

# 7. Backtest the whole strategy net of costs
python -m quant.pipeline backtest     # writes reports/backtest.html

# 8. Launch the dashboard
streamlit run app/dashboard.py

Usage Command
What it does
python -m quant.pipeline backfill	Full historical data load into Supabase
python -m quant.pipeline daily	Incremental sync, forecasts, optimization, rebalance signal
python -m quant.pipeline backtest	Walk-forward backtest of BL vs. equal-weight vs. min-vol
streamlit run app/dashboard.py	Interactive dashboard
pytest tests/ -q	Lookahead / target-correctness tests

Configuration
All strategy parameters live in config.yaml: universe, forecast horizon,
covariance window, weight bounds, rebalance band, transaction costs, and
LightGBM hyperparameters.

Project structure
text

src/quant/
├── ingest.py       # data ingestion + quality checks
├── db.py           # Supabase access layer
├── features.py     # trailing-only feature engineering
├── models/         # baselines, LightGBM, GARCH
├── evaluate.py     # walk-forward harness + metrics
├── optimize/       # covariance, Black-Litterman, turnover control
├── backtest.py     # full-loop net-of-cost backtest
└── pipeline.py     # orchestration entrypoint
Disclaimer
This project is for research and education. Nothing here is financial advice.
Past performance in a backtest does not predict future results.