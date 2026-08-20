import pandas as pd


def drifted(current: pd.Series, cum_asset_returns: pd.Series) -> pd.Series:
    """Weights after buy-and-hold drift given cumulative simple returns per asset."""
    w = current * (1 + cum_asset_returns.fillna(0.0))
    return w / w.sum()


def apply_bands(current: pd.Series, target: pd.Series, band=0.05) -> pd.Series:
    """Only trade assets whose drift from current exceeds `band`; renormalize."""
    delta = (target - current).abs()
    new = current.reindex(target.index).fillna(0.0).copy()
    new[delta > band] = target[delta > band]
    s = new.sum()
    return new / s if s > 0 else target


def one_way_turnover(old: pd.Series, new: pd.Series) -> float:
    old = old.reindex(new.index).fillna(0.0)
    return float((new - old).abs().sum() / 2)