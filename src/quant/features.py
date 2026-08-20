import numpy as np
import pandas as pd

FEATURE_COLS = ["ret_1d", "ret_5d", "ret_21d", "vol_21d", "vol_63d",
                "rsi_14", "dist_252d_high", "volume_z"]


def rsi(close: pd.Series, period=14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def build_features(prices_long: pd.DataFrame) -> pd.DataFrame:
    """prices_long: [ticker, date, adj_close, volume] → per-(ticker,date) features."""
    out = []
    for t, g in prices_long.groupby("ticker"):
        g = g.sort_values("date").set_index("date")
        c = g["adj_close"]
        f = pd.DataFrame(index=g.index)
        f["ticker"] = t
        f["ret_1d"] = np.log(c).diff()
        f["ret_5d"] = np.log(c).diff(5)
        f["ret_21d"] = np.log(c).diff(21)
        f["vol_21d"] = f["ret_1d"].rolling(21).std()
        f["vol_63d"] = f["ret_1d"].rolling(63).std()
        f["rsi_14"] = rsi(c)
        f["dist_252d_high"] = c / c.rolling(252).max() - 1
        vz = (g["volume"] - g["volume"].rolling(63).mean()) / g["volume"].rolling(63).std()
        f["volume_z"] = vz.fillna(0.0)
        out.append(f.reset_index())
    return pd.concat(out, ignore_index=True)


def build_model_frame(prices_long: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """
    Returns [ticker, date, target_date, y, *FEATURE_COLS].
    y = forward log return over `horizon` trading days.
    Rows near the end have y/target_date = NaT (unrealized) — kept for live prediction;
    training code must filter on target_date (realized) or dropna(y).
    """
    feats = build_features(prices_long)

    targets = []
    for t, g in prices_long.sort_values(["ticker", "date"]).groupby("ticker"):
        g = g.reset_index(drop=True)
        c = np.log(g["adj_close"])
        targets.append(pd.DataFrame({
            "ticker": t,
            "date": g["date"],
            "target_date": g["date"].shift(-horizon),
            "y": -c.diff(-horizon),      # log(p[t+h] / p[t])
        }))
    target = pd.concat(targets, ignore_index=True)

    df = feats.merge(target, on=["ticker", "date"], how="inner")
    return df.dropna(subset=FEATURE_COLS).reset_index(drop=True)


# ---------- wide matrices ----------

def adj_close_wide(prices_long) -> pd.DataFrame:
    return prices_long.pivot(index="date", columns="ticker",
                             values="adj_close").sort_index()


def log_returns_wide(prices_long) -> pd.DataFrame:
    return np.log(adj_close_wide(prices_long)).diff().dropna(how="all")


def simple_returns_wide(prices_long) -> pd.DataFrame:
    return adj_close_wide(prices_long).pct_change().dropna(how="all")