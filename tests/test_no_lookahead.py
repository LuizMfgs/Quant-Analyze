import numpy as np
import pandas as pd

from quant.features import build_features, build_model_frame

def synthetic_prices(n=400, tickers=("A", "B"), seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2020-01-01", periods=n)
    rows = []
    for t in tickers:
        px = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
        rows += [(t, d, p, p, 1e6) for d, p in zip(dates, px)]
    return pd.DataFrame(rows, columns=["ticker", "date", "adj_close", "close", "volume"])


def test_features_are_trailing_only():
    """Features at date t must be identical whether computed on full or truncated data."""
    full = synthetic_prices(n=600)
    f_full = build_features(full)
    cutoff = sorted(full["date"].unique())[400]
    f_cut = build_features(full[full["date"] <= cutoff])

    m = f_full.merge(f_cut, on=["ticker", "date"], suffixes=("_f", "_c"))
    assert len(m) == len(f_cut)
    for col in ["ret_1d", "vol_21d", "rsi_14", "dist_252d_high"]:
        assert np.allclose(m[f"{col}_f"], m[f"{col}_c"], equal_nan=True)


def test_forward_target_is_correct():
    df = build_model_frame(synthetic_prices(n=300), horizon=5)
    row = df.iloc[100]
    px = synthetic_prices(n=300)
    p = px[(px["ticker"] == row["ticker"]) &
       (px["date"].between(row["date"], row["target_date"]))]
    p = p.sort_values("date")["adj_close"].values
    assert np.isclose(row["y"], np.log(p[-1] / p[0]))