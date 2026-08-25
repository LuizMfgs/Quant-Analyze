import pandas as pd
import yfinance as yf

from . import db

FIELDS = {"Date": "date", "Open": "open", "High": "high", "Low": "low",
          "Close": "close", "Adj Close": "adj_close", "Volume": "volume"}


def fetch_history(tickers, start, end=None) -> pd.DataFrame:
    raw = yf.download(tickers, start=start, end=end, auto_adjust=False,
                      group_by="ticker", threads=True, progress=False)
    if isinstance(raw.columns, pd.MultiIndex):
        data = {t: raw[t] for t in raw.columns.get_level_values(0).unique()}
    else:                                   # single-ticker download has flat columns
        data = {tickers[0]: raw}

    frames = []
    for t in tickers:
        d = data.get(t)
        if d is None or d.empty:
            print(f"[ingest] WARNING: no data for {t}")
            continue
        d = d.dropna(subset=["Close"]).reset_index().rename(columns=FIELDS)
        d["ticker"] = t
        frames.append(d[["ticker", "date", "open", "high", "low",
                         "close", "adj_close", "volume"]])
    out = pd.concat(frames, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"]).dt.date
    return out


def data_quality(prices: pd.DataFrame, max_stale_days=7) -> list[str]:
    """Flag stale assets and suspicious internal gaps (holidays will pass)."""
    issues = []
    global_max = prices["date"].max()
    for t, g in prices.groupby("ticker"):
        stale = (global_max - g["date"].max()).days
        if stale > max_stale_days:
            issues.append(f"{t}: last bar {g['date'].max()} lags global max by {stale}d")
        d = pd.to_datetime(g["date"]).sort_values()
        for _, gap in d.diff().dt.days.items():
            if gap > 10:
                issues.append(f"{t}: calendar gap of {gap}d (check splits/delistings)")
    return issues


def run_ingest(tickers, history_start, full=False):
    """Incremental sync (or full backfill). Returns (df, issues)."""
    if full:
        start = history_start
    else:
        last = db.last_price_dates(tickers)
        # refetch from 10 calendar days before newest bar; upsert makes overlap safe
        newest = max((v for v in last.values() if v is not None), default=None)
        start = ((pd.Timestamp(newest) - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
                 if newest else history_start)

    df = fetch_history(tickers, start)
    if df.empty:
        raise RuntimeError("ingest returned no data â€” check tickers / network")
    db.upsert_prices(df)
    issues = data_quality(df)
    for i in issues:
        print(f"[ingest] {i}")
    print(f"[ingest] upserted {len(df)} rows, {df['date'].min()} â†’ {df['date'].max()}")
    return df, issues
import pandas as pd
import yfinance as yf

from . import db

FIELDS = {"Date": "date", "Open": "open", "High": "high", "Low": "low",
          "Close": "close", "Adj Close": "adj_close", "Volume": "volume"}


def fetch_history(tickers, start, end=None) -> pd.DataFrame:
    """Download OHLCV from yfinance. Tries batch first; falls back to
    per-ticker downloads if the batch fails or misses some tickers."""
    frames = []

    # Batch download â€” threads=False is more reliable on Windows
    try:
        raw = yf.download(tickers, start=start, end=end, auto_adjust=False,
                          group_by="ticker", threads=False, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            data = {t: raw[t] for t in raw.columns.get_level_values(0).unique()}
        else:
            data = {tickers[0]: raw}
    except Exception:
        data = {}

    for t in tickers:
        d = data.get(t)
        if d is None or d.empty:
            # Fallback: download this ticker alone
            print(f"[ingest] batch miss for {t}, trying individual download")
            try:
                d = yf.download(t, start=start, end=end, auto_adjust=False,
                                progress=False, threads=False)
            except Exception as e:
                print(f"[ingest] WARNING: no data for {t}: {e}")
                continue
            if d.empty:
                print(f"[ingest] WARNING: no data for {t}")
                continue

        d = d.dropna(subset=["Close"]).reset_index().rename(columns=FIELDS)
        d["ticker"] = t
        frames.append(d[["ticker", "date", "open", "high", "low",
                         "close", "adj_close", "volume"]])

    if not frames:
        raise RuntimeError(
            "ingest returned no data for any ticker - check network/yfinance")
    out = pd.concat(frames, ignore_index=True)
    out["date"] = pd.to_datetime(out["date"]).dt.date
    return out


def data_quality(prices: pd.DataFrame, max_stale_days=7) -> list[str]:
    """Flag stale assets and suspicious internal gaps (holidays will pass)."""
    issues = []
    global_max = prices["date"].max()
    for t, g in prices.groupby("ticker"):
        stale = (global_max - g["date"].max()).days
        if stale > max_stale_days:
            issues.append(f"{t}: last bar {g['date'].max()} lags global max by {stale}d")
        d = pd.to_datetime(g["date"]).sort_values()
        for _, gap in d.diff().dt.days.items():
            if gap > 10:
                issues.append(f"{t}: calendar gap of {gap}d (check splits/delistings)")
    return issues


def run_ingest(tickers, history_start, full=False):
    """Incremental sync (or full backfill). Falls back to existing DB data
    if the download fails entirely - the pipeline continues on cached data."""
    if full:
        start = history_start
    else:
        last = db.last_price_dates(tickers)
        newest = max((v for v in last.values() if v is not None), default=None)
        start = ((pd.Timestamp(newest) - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
                 if newest else history_start)

    try:
        df = fetch_history(tickers, start)
    except Exception as e:
        print(f"[ingest] download failed ({e}); will use existing DB data")
        return pd.DataFrame(), []

    if df.empty:
        print("[ingest] no new data downloaded; using existing DB data")
        return df, []

    db.upsert_prices(df)
    issues = data_quality(df)
    for i in issues:
        print(f"[ingest] {i}")
    print(f"[ingest] upserted {len(df)} rows, {df['date'].min()} -> {df['date'].max()}")
    return df, issues
