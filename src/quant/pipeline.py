"""Usage: python -m quant.pipeline daily|backfill|backtest"""
import datetime as dt
import json
import sys
import numpy as np
import pandas as pd
from . import db, features, ingest, portfolio as pf
from .config import load_cfg
from .evaluate import metrics, residual_std_by_ticker, walk_forward
from src.models.gbdt import LGBMForecaster
from src.models.garch import garch_vol_forecast
from src.optmize.black_litterman import black_litterman, optimize
from src.optmize.covariance import shrunk_cov


def get_prices(cfg):
    ingest.run_ingest(cfg["universe"], cfg["history_start"])
    return db.load_prices(cfg["universe"])


def forecast_step(prices_long, cfg):
    """Walk-forward evaluation + refit on all data + live prediction."""
    h = cfg["horizon_days"]
    df = features.build_model_frame(prices_long, h)

    preds = walk_forward(lambda: LGBMForecaster(cfg.get("lgbm_params")), df,
                         initial_train=cfg.get("initial_train", 756), step=h)
    m = metrics(preds)
    resid = residual_std_by_ticker(preds)
    print("[forecast]", json.dumps(m, indent=2, default=str))

    model = LGBMForecaster(cfg.get("lgbm_params")).fit(df[df["y"].notna()],
                                                       df.loc[df["y"].notna(), "y"])
    last_date = df["date"].max()
    live = df[df["date"] == last_date]
    p = model.predict(live)
    sd = live["ticker"].map(resid).fillna(resid.mean()).values

    fc = live[["ticker", "date", "target_date"]].copy()
    fc["horizon_days"] = h
    fc["expected_return"] = p
    fc["interval_low"] = p - 1.96 * sd
    fc["interval_high"] = p + 1.96 * sd
    return fc.rename(columns={"date": "forecast_date"}), model, m, resid


def optimize_step(prices_long, fc, resid, cfg):
    h = cfg["horizon_days"]
    rets = features.simple_returns_wide(prices_long)
    log_rets = features.log_returns_wide(prices_long)

    S = shrunk_cov(rets.tail(cfg.get("cov_window", 756)))
    w_mkt = pd.Series(1.0 / S.shape[0], index=S.index)

    views = fc.set_index("ticker")["expected_return"] * (252 / h)      # annualize
    view_var = (resid.reindex(S.index).fillna(resid.mean()) ** 2) * (252 / h)

    mu_bl, S_bl = black_litterman(S, w_mkt, views, view_var,
                                  tau=cfg.get("tau", 0.05),
                                  risk_aversion=cfg.get("risk_aversion", 2.5))
    bounds = tuple(cfg.get("weight_bounds", [0.0, 0.30]))
    w = optimize(mu_bl, S_bl, objective=cfg.get("objective", "max_sharpe"), bounds=bounds)

    vols = {t: garch_vol_forecast(log_rets[t].tail(1500), h) for t in log_rets.columns}
    return w, rets, vols


def _heartbeat():
    """Emit a CloudWatch metric on success — a missed run trips the alarm.
    Telemetry must never fail the pipeline, hence the blanket try/except."""
    try:
        import boto3
        boto3.client("cloudwatch").put_metric_data(
            Namespace="Quant/Pipeline",
            MetricData=[{"MetricName": "RunCompleted", "Unit": "Count", "Value": 1}],
        )
    except Exception as e:
        print(f"[heartbeat] skipped: {e}")


def daily(cfg=None):
    cfg = cfg or load_cfg()
    prices = get_prices(cfg)

    fc, model, m, resid = forecast_step(prices, cfg)
    model_id = db.register_model("lgbm", "lightgbm", cfg.get("lgbm_params"), metrics=m)
    try:
        db.upload_artifact(model_id, model)
    except Exception as e:
        print(f"[registry] artifact upload skipped: {e}")
    db.save_forecasts(model_id, fc.assign(
        forecast_date=pd.to_datetime(fc["forecast_date"]).dt.date,
        target_date=pd.to_datetime(fc["target_date"]).dt.date))

    w, rets, vols = optimize_step(prices, fc, resid, cfg)
    print("[optimize]", w.round(4).to_dict())

    # ---- rebalance decision: bands + minimum turnover ----
    last_date, last_w = db.latest_rebalance()
    if last_w is None or last_w.empty:
        db.save_rebalance(w, dt.date.today(), "initial allocation",
                          config={"vols_annualized": vols})
        print("[rebalance] initial allocation saved")
    else:
        since = rets.loc[rets.index > pd.Timestamp(last_date)]
        cum = (1 + since).prod() - 1
        current = pf.drifted(last_w, cum.iloc[-1] if len(cum) else pd.Series(0.0, index=last_w.index))
        new_w = pf.apply_bands(current, w, band=cfg.get("band", 0.05))
        turnover = pf.one_way_turnover(current, new_w)

        if turnover < cfg.get("min_turnover", 0.05):
            print(f"[rebalance] skipped — one-way turnover {turnover:.1%} < "
                  f"{cfg.get('min_turnover', 0.05):.0%}")
        else:
            db.save_rebalance(new_w, dt.date.today(),
                              f"drift {turnover:.1%} exceeded band {cfg.get('band', 0.05):.0%}",
                              config={"one_way_turnover": turnover, "vols_annualized": vols})
            print(f"[rebalance] saved, one-way turnover {turnover:.1%}")

    _heartbeat()

def backfill(cfg=None):
    cfg = cfg or load_cfg()
    ingest.run_ingest(cfg["universe"], cfg["history_start"], full=True)


def run_backtest(cfg=None):
    cfg = cfg or load_cfg()
    from .backtest import backtest, report
    prices = db.load_prices(cfg["universe"])
    report(backtest(prices, cfg))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "daily"
    {"daily": daily, "backfill": backfill, "backtest": run_backtest}[cmd]()