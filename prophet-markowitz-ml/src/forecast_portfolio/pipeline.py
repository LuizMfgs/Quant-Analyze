"""End-to-end pipeline: data → Prophet forecasts → Markowitz → JSON exports."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from .config import PROJECT_ROOT, Settings
from .data import daily_returns, load_price_matrix
from .forecast import forecast_all
from .optimize import discrete_allocation, optimise, shrunk_covariance

log = logging.getLogger(__name__)
OUTPUTS = PROJECT_ROOT / "outputs"


def run(settings: Settings, refresh: bool = False) -> dict:
    OUTPUTS.mkdir(exist_ok=True)

    # 1. data ---------------------------------------------------------------
    prices = load_price_matrix(settings.tickers, settings.data, refresh=refresh)
    returns = daily_returns(prices)
    prices.to_csv(OUTPUTS / "prices.csv")
    log.info("Price matrix: %d rows × %d assets", len(prices), len(prices.columns))

    # 2. Prophet forecasts ---------------------------------------------------
    forecasts = forecast_all(prices, settings.forecast)
    mu = pd.Series({t: f.expected_return for t, f in forecasts.items()})

    # 3. Markowitz optimisation ----------------------------------------------
    cov = shrunk_covariance(returns)
    result = optimise(mu, cov, settings.optimization)

    # 4. rebalance: forecast-driven weights vs equal-weight baseline ---------
    latest = prices.iloc[-1]
    n = len(settings.tickers)
    baseline = {t: 1 / n for t in settings.tickers}
    alloc = discrete_allocation(result["max_sharpe"]["weights"], latest,
                                settings.rebalance.portfolio_value)
    alloc.to_csv(OUTPUTS / "allocation.csv", index=False)

    # 5. export everything the dashboard needs -------------------------------
    payload = {
        "as_of": str(prices.index[-1].date()),
        "tickers": settings.tickers,
        "config": {
            "horizon_days": settings.forecast.horizon_days,
            "test_days": settings.forecast.test_days,
            "risk_free_rate": settings.optimization.risk_free_rate,
            "weight_bounds": list(settings.optimization.weight_bounds),
            "portfolio_value": settings.rebalance.portfolio_value,
        },
        "prices": {
            "dates": [str(d.date()) for d in prices.index],
            "series": {t: [round(float(v), 4) for v in prices[t]] for t in prices},
        },
        "forecasts": {
            t: {
                "dates": [str(d.date()) for d in f.forecast["date"]],
                "yhat": [round(float(v), 4) for v in f.forecast["yhat"]],
                "lower": [round(float(v), 4) for v in f.forecast["yhat_lower"]],
                "upper": [round(float(v), 4) for v in f.forecast["yhat_upper"]],
                "last_price": round(float(f.history["close"].iloc[-1]), 4),
                "expected_return": round(f.expected_return, 6),
                "metrics": {k: round(v, 4) for k, v in f.metrics.items()},
                "backtest": {
                    "dates": [str(d.date()) for d in f.backtest["date"]],
                    "actual": [round(float(v), 4) for v in f.backtest["actual"]],
                    "predicted": [round(float(v), 4) for v in f.backtest["predicted"]],
                },
            }
            for t, f in forecasts.items()
        },
        "optimization": result,
        "rebalance": {
            "baseline_weights": baseline,
            "target_weights": result["max_sharpe"]["weights"],
            "allocation": alloc.to_dict("records"),
            "leftover_cash": round(alloc.attrs["leftover_cash"], 2),
            "expected_return": result["max_sharpe"]["return"],
            "expected_volatility": result["max_sharpe"]["volatility"],
            "sharpe": result["max_sharpe"]["sharpe"],
        },
    }
    out = OUTPUTS / "results.json"
    out.write_text(json.dumps(payload, indent=1))
    log.info("Wrote %s (%.1f KB)", out, out.stat().st_size / 1024)
    return payload
