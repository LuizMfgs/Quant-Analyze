"""Data ingestion: CSV cache first, yfinance download on cache miss.

Both sources are free. The cache makes runs reproducible and avoids
rate limits; `refresh=True` forces a fresh download.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .config import DataConfig

log = logging.getLogger(__name__)


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Return a tidy frame: date (tz-naive), close (float)."""
    df = df.copy()
    date_col = "Date" if "Date" in df.columns else "date"
    df["date"] = pd.to_datetime(df[date_col], utc=True).dt.tz_localize(None).dt.normalize()
    close_col = "Close" if "Close" in df.columns else "close"
    out = df[["date", close_col]].rename(columns={close_col: "close"})
    return out.dropna().sort_values("date").reset_index(drop=True)


def load_prices(ticker: str, cfg: DataConfig, refresh: bool = False) -> pd.DataFrame:
    """Load daily close prices for one ticker as [date, close]."""
    cache = Path(cfg.cache_dir) / f"{ticker}.csv"
    if cache.exists() and not refresh:
        df = pd.read_csv(cache)
        log.info("%s: loading %d cached rows", ticker, len(df))
        return _normalise(df)

    import yfinance as yf  # imported lazily so cached runs need no network

    log.info("%s: downloading %s of history from Yahoo Finance", ticker, cfg.period)
    raw = yf.download(ticker, period=cfg.period, interval=cfg.interval,
                      auto_adjust=True, progress=False)
    if raw.empty:
        raise ValueError(f"No data returned for {ticker}")
    raw.reset_index().to_csv(cache, index=False)
    return _normalise(raw.reset_index())


def load_price_matrix(tickers: list[str], cfg: DataConfig,
                      refresh: bool = False) -> pd.DataFrame:
    """Wide DataFrame of close prices, one column per ticker, aligned on dates."""
    frames = {t: load_prices(t, cfg, refresh).set_index("date")["close"] for t in tickers}
    prices = pd.DataFrame(frames).dropna()
    prices.index.name = "date"
    return prices


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna()
