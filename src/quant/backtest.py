import os

import numpy as np
import pandas as pd
import quantstats as qs

from . import features, portfolio as pf
from src.models.gbdt import LGBMForecaster
from src.optmize.black_litterman import black_litterman, optimize
from src.optmize.covariance import shrunk_cov


def _validation_residuals(train: pd.DataFrame, cfg):
    """Fit on first 80% of train, measure error on last 20% → per-asset view variance."""
    cut = int(len(train) * 0.8)
    m = LGBMForecaster(cfg.get("lgbm_params")).fit(
        train.iloc[:cut], train["y"].iloc[:cut])
    val = train.iloc[cut:]
    e = m.predict(val) - val["y"].values
    per = pd.Series(e, index=val["ticker"].values).groupby(level=0).std()
    return per, float(np.std(e, ddof=1))


def _target_weights(strat, df, rets, d, cfg):
    cols = rets.columns
    if strat == "equal":
        return pd.Series(1.0 / len(cols), index=cols)
    if strat in ("bl", "minvol"):
        train = df[(df["target_date"] <= d) & df["y"].notna()]
        if len(train) < cfg.get("min_train", 252):
            return None
        S = shrunk_cov(rets.loc[rets.index <= d].tail(cfg.get("cov_window", 756)))
        bounds = tuple(cfg.get("weight_bounds", [0.0, 0.30]))
        if strat == "minvol":
            return optimize(pd.Series(0.0, index=S.index), S,
                            "min_volatility", bounds=bounds)

        h = cfg["horizon_days"]
        per_resid, pooled = _validation_residuals(train, cfg)
        model = LGBMForecaster(cfg.get("lgbm_params")).fit(train, train["y"])
        live = df[df["date"] == d]
        if live.empty:
            return None
        p = pd.Series(model.predict(live), index=live["ticker"].values)

        views = p * (252 / h)
        view_var = (per_resid.reindex(views.index).fillna(pooled) ** 2) * (252 / h)
        w_mkt = pd.Series(1.0 / S.shape[0], index=S.index)
        mu_bl, S_bl = black_litterman(S, w_mkt, views, view_var,
                                      tau=cfg.get("tau", 0.05))
        return optimize(mu_bl, S_bl, cfg.get("objective", "max_sharpe"), bounds=bounds)
    raise ValueError(strat)


def backtest(prices_long, cfg, strategies=("bl", "equal", "minvol")):
    rets = features.simple_returns_wide(prices_long)
    df = features.build_model_frame(prices_long, cfg["horizon_days"])
    dates = rets.index
    start = cfg.get("initial_train", 756)
    if len(dates) <= start:
        raise ValueError("not enough history for the configured warmup")

    rebal_dates = set(dates[start::cfg.get("rebalance_every", 21)])
    cost = cfg.get("cost_bps", 10) / 1e4          # per side, on traded notional
    band = cfg.get("band", 0.05)

    results, curves = {}, {}
    for strat in strategies:
        w, equity, daily = None, 1.0, {}
        for d in dates[start:]:
            r = rets.loc[d].fillna(0.0)
            port = 0.0
            if w is not None:                      # drift through today
                growth = w * (1 + r)
                port = growth.sum() - 1
                w = growth / growth.sum()

            if d in rebal_dates:
                target = _target_weights(strat, df, rets, d, cfg)
                if target is not None:
                    if w is None:
                        new = target
                    else:
                        new = pf.apply_bands(w, target, band) if strat == "bl" else target
                    traded = pf.one_way_turnover(
                        w if w is not None else pd.Series(0.0, index=target.index), new)
                    port -= traded * 2 * cost      # pay bps on both legs
                    w = new

            daily[d] = port
            equity *= 1 + port
            curves[d] = equity
        results[strat] = pd.Series(daily).sort_index()
        print(f"[backtest:{strat}] terminal equity {equity:.2f}")
    return pd.DataFrame(results)


def report(rets_df: pd.DataFrame, out="reports/backtest.html"):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for c in rets_df:
        print(f"\n===== {c} =====")
        print(qs.reports.metrics(rets_df[c], display=False).to_string())
    qs.reports.html(rets_df["bl"], benchmark=rets_df["equal"],
                    output=out, title="BL strategy vs equal-weight")
    print(f"\n[report] tearsheet written to {out}")