"""Prophet forecasting: one model per asset, backtest metrics, future paths."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from prophet import Prophet

from .config import ForecastConfig

log = logging.getLogger(__name__)
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)


@dataclass
class AssetForecast:
    ticker: str
    history: pd.DataFrame     # [date, close] used for training
    forecast: pd.DataFrame    # [date, yhat, yhat_lower, yhat_upper] future only
    backtest: pd.DataFrame    # held-out rows [date, actual, predicted]
    metrics: dict             # mape, rmse, mae on the held-out window
    expected_return: float    # annualised return implied by the forecast


def _make_model(cfg: ForecastConfig) -> Prophet:
    return Prophet(
        daily_seasonality=cfg.prophet.daily_seasonality,
        weekly_seasonality=cfg.prophet.weekly_seasonality,
        yearly_seasonality=cfg.prophet.yearly_seasonality,
        changepoint_prior_scale=cfg.prophet.changepoint_prior_scale,
    )


def _to_prophet_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={"date": "ds", "close": "y"})[["ds", "y"]]


def forecast_asset(prices: pd.DataFrame, ticker: str, cfg: ForecastConfig) -> AssetForecast:
    """Train/validate split, fit Prophet, forecast `horizon_days` ahead."""
    prices = prices.sort_values("date").reset_index(drop=True)

    # --- backtest: hold out the last `test_days` rows ----------------------
    train, test = prices.iloc[:-cfg.test_days], prices.iloc[-cfg.test_days:]
    bt_model = _make_model(cfg)
    bt_model.fit(_to_prophet_frame(train))
    bt_pred = bt_model.predict(bt_model.make_future_dataframe(periods=cfg.test_days))
    pred_test = bt_pred[["ds", "yhat"]].merge(test, left_on="ds", right_on="date")
    err = pred_test["close"] - pred_test["yhat"]
    metrics = {
        "mape": float(np.mean(np.abs(err / pred_test["close"])) * 100),
        "rmse": float(np.sqrt(np.mean(err**2))),
        "mae": float(np.mean(np.abs(err))),
    }
    backtest = pred_test[["date", "close", "yhat"]].rename(
        columns={"close": "actual", "yhat": "predicted"})

    # --- final model on ALL data, forecast the future ----------------------
    model = _make_model(cfg)
    model.fit(_to_prophet_frame(prices))
    future = model.make_future_dataframe(periods=cfg.horizon_days)
    fc = model.predict(future)
    fc_future = fc[fc["ds"] > prices["date"].max()][
        ["ds", "yhat", "yhat_lower", "yhat_upper"]
    ].rename(columns={"ds": "date"}).reset_index(drop=True)

    last_price = float(prices["close"].iloc[-1])
    terminal = float(fc_future["yhat"].iloc[-1])
    horizon_ret = terminal / last_price - 1.0
    expected_return = float((1 + horizon_ret) ** (365 / cfg.horizon_days) - 1)

    log.info("%s: expected annual return %+.1f%% (MAPE %.2f%%)",
             ticker, expected_return * 100, metrics["mape"])
    return AssetForecast(ticker, prices, fc_future, backtest, metrics, expected_return)


def forecast_all(price_matrix: pd.DataFrame, cfg: ForecastConfig) -> dict[str, AssetForecast]:
    out = {}
    for ticker in price_matrix.columns:
        df = price_matrix[[ticker]].reset_index().rename(columns={ticker: "close"})
        out[ticker] = forecast_asset(df, ticker, cfg)
    return out
