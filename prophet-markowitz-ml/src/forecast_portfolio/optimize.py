"""Markowitz mean-variance optimisation.

Uses PyPortfolioOpt when installed (`poetry install -E pypfopt`), otherwise a
self-contained scipy SLSQP implementation of the same maths:

    minimise      w' Σ w            (portfolio variance)
    subject to    Σ wᵢ = 1          (fully invested)
                  boundsᵢ ≤ wᵢ      (long-only + concentration cap)
    and, for frontier points,  μ'w = target_return

Expected returns μ come from the Prophet forecasts; the covariance Σ is
estimated from historical daily returns with Ledoit-Wolf shrinkage and
annualised (×252 trading days).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf

from .config import OptimizationConfig

log = logging.getLogger(__name__)
TRADING_DAYS = 252


def shrunk_covariance(returns: pd.DataFrame) -> pd.DataFrame:
    """Ledoit-Wolf shrunk, annualised covariance of daily returns."""
    lw = LedoitWolf().fit(returns.values)
    cov = pd.DataFrame(lw.covariance_ * TRADING_DAYS,
                       index=returns.columns, columns=returns.columns)
    return cov


def _portfolio_stats(w: np.ndarray, mu: np.ndarray, cov: np.ndarray, rf: float):
    ret = float(w @ mu)
    vol = float(np.sqrt(w @ cov @ w))
    sharpe = (ret - rf) / vol if vol > 0 else 0.0
    return ret, vol, sharpe


def _solve(mu: np.ndarray, cov: np.ndarray, bounds, target: float | None,
           rf: float) -> np.ndarray | None:
    n = len(mu)
    w0 = np.full(n, 1 / n)
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    if target is not None:
        cons.append({"type": "eq", "fun": lambda w: w @ mu - target})
        obj = lambda w: w @ cov @ w                      # noqa: E731
    else:  # max Sharpe  <=>  minimise negative Sharpe
        obj = lambda w: -(w @ mu - rf) / np.sqrt(w @ cov @ w)  # noqa: E731
    res = minimize(obj, w0, method="SLSQP", bounds=bounds, constraints=cons,
                   options={"maxiter": 500, "ftol": 1e-10})
    if not res.success:
        return None
    w = np.clip(res.x, 0, None)
    return w / w.sum()


def optimise(mu: pd.Series, cov: pd.DataFrame, cfg: OptimizationConfig) -> dict:
    """Return max-Sharpe / min-vol portfolios and the full efficient frontier."""
    tickers = list(mu.index)
    mu_v, cov_v = mu.values, cov.loc[tickers, tickers].values
    bounds = [cfg.weight_bounds] * len(tickers)
    rf = cfg.risk_free_rate

    w_ms = _solve(mu_v, cov_v, bounds, target=None, rf=rf)
    if w_ms is None:
        raise RuntimeError("Max-Sharpe optimisation failed to converge")

    ret_min, ret_max = float(mu_v.min()), float(mu_v.max())
    frontier, targets = [], np.linspace(ret_min, ret_max, cfg.frontier_points)
    min_vol_w, min_vol_stats = None, None
    for t in targets:
        w = _solve(mu_v, cov_v, bounds, target=t, rf=rf)
        if w is None:
            continue
        r, v, s = _portfolio_stats(w, mu_v, cov_v, rf)
        frontier.append({"return": r, "volatility": v, "sharpe": s,
                         "weights": dict(zip(tickers, w.round(6)))})
        if min_vol_stats is None or v < min_vol_stats[1]:
            min_vol_w, min_vol_stats = w, (r, v, s)

    ms = _portfolio_stats(w_ms, mu_v, cov_v, rf)
    log.info("Max Sharpe portfolio: ret %.1f%%, vol %.1f%%, Sharpe %.2f",
             ms[0] * 100, ms[1] * 100, ms[2])
    return {
        "tickers": tickers,
        "max_sharpe": {"weights": dict(zip(tickers, w_ms.round(6))),
                       "return": ms[0], "volatility": ms[1], "sharpe": ms[2]},
        "min_volatility": {"weights": dict(zip(tickers, min_vol_w.round(6))),
                           "return": min_vol_stats[0],
                           "volatility": min_vol_stats[1],
                           "sharpe": min_vol_stats[2]},
        "frontier": frontier,
        "risk_free_rate": rf,
    }


def discrete_allocation(weights: dict[str, float], latest_prices: pd.Series,
                        portfolio_value: float) -> pd.DataFrame:
    """Greedy discrete share allocation for a given cash amount."""
    rows, cash = [], portfolio_value
    for t, w in sorted(weights.items(), key=lambda kv: -kv[1]):
        price = float(latest_prices[t])
        shares = int(w * portfolio_value / price) if price > 0 else 0
        value = shares * price
        cash -= value
        rows.append({"ticker": t, "weight": w, "price": price,
                     "shares": shares, "value": value})
    df = pd.DataFrame(rows)
    df.attrs["leftover_cash"] = cash
    return df
