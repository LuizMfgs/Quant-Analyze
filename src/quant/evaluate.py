import numpy as np
import pandas as pd


def walk_forward(model_factory, df: pd.DataFrame,
                 initial_train=756, step=21, min_train=252) -> pd.DataFrame:
    dates = np.sort(df["date"].unique())
    recs = []
    for d in dates[initial_train::step]:
        train = df[(df["target_date"] <= d) & df["y"].notna()]
        test = df[df["date"] == d]
        if len(train) < min_train or test.empty:
            continue
        m = model_factory()
        m.fit(train, train["y"])
        rec = test[["ticker", "date", "y"]].copy()
        rec["pred"] = m.predict(test)
        recs.append(rec)
    if not recs:
        raise ValueError("no walk-forward folds produced — check initial_train/history")
    return pd.concat(recs, ignore_index=True)


def metrics(preds: pd.DataFrame) -> dict:
    p = preds.dropna(subset=["y"])
    e = p["pred"] - p["y"]
    ic = p.groupby("date").apply(
        lambda g: g["pred"].corr(g["y"], method="spearman")
        if len(g) > 2 and g["y"].std() > 0 else np.nan)
    return {
        "mae": float(e.abs().mean()),
        "rmse": float(np.sqrt((e ** 2).mean())),
        "hit_rate": float((np.sign(p["pred"]) == np.sign(p["y"])).mean()),
        "mean_daily_ic": float(ic.mean()),
        "ic_ir": float(ic.mean() / ic.std()) if ic.std() > 0 else None,
        "n_obs": int(len(p)),
    }


def residual_std_by_ticker(preds: pd.DataFrame) -> pd.Series:
    """Per-asset forecast error std → becomes Black-Litterman view uncertainty."""
    p = preds.dropna(subset=["y"]).copy()
    p["e"] = p["pred"] - p["y"]
    return p.groupby("ticker")["e"].std()