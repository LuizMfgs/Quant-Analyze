import sys
sys.path.insert(0, "src")

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from quant import db, features

st.set_page_config(page_title="Quant Portfolio", layout="wide")


@st.cache_data(ttl=600)
def load_prices():
    return db.load_prices()


@st.cache_data(ttl=600)
def load_forecasts():
    return db.latest_forecasts(days=60)


prices = load_prices()
adj = features.adj_close_wide(prices)
rets = adj.pct_change()

tab1, tab2, tab3 = st.tabs(["Portfolio", "Forecasts", "Performance"])

with tab1:
    _, w = db.latest_rebalance()
    if w is None:
        st.info("No rebalance yet — run `python -m quant.pipeline daily`.")
    else:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("Current target weights")
            st.plotly_chart(px.pie(names=w.index, values=w.values, hole=0.4))
        with c2:
            fc = load_forecasts()
            if not fc.empty:
                latest = fc[fc["forecast_date"] == fc["forecast_date"].max()]
                st.subheader("Latest 1-month expected returns")
                st.plotly_chart(px.bar(latest, x="ticker", y="expected_return"))

with tab2:
    fc = load_forecasts()
    if fc.empty:
        st.info("No forecasts stored yet.")
    else:
        # join forecasts with realized outcomes computed from stored prices
        f = fc.copy()
        f["realized"] = [
            adj.loc[fd, t] / adj.loc[min(td, adj.index.max()), t] - 1
            if fd in adj.index and t in adj.columns else np.nan
            for t, fd, td in zip(f["ticker"], pd.to_datetime(f["forecast_date"]),
                                 pd.to_datetime(f["target_date"]))
        ]
        f = f.dropna(subset=["realized"])
        st.subheader("Forecast vs realized (horizon returns)")
        st.plotly_chart(px.scatter(f, x="expected_return", y="realized",
                                   color="ticker", trendline="ols"))
        ic = f.groupby("forecast_date").apply(
            lambda g: g["expected_return"].corr(g["realized"], method="spearman")
            if len(g) > 2 else np.nan).mean()
        st.metric("Mean daily cross-sectional IC", f"{ic:.3f}")
        st.dataframe(f.sort_values("forecast_date", ascending=False).head(50))

with tab3:
    pr = db.portfolio_returns()
    if pr.empty:
        st.info("No portfolio returns recorded yet.")
    else:
        pr["date"] = pd.to_datetime(pr["date"])
        s = pr.set_index("date")["net_return"]
        bench = rets.loc[rets.index >= s.index.min()].mean(axis=1)
        eq = (1 + s).cumprod()
        beq = (1 + bench).cumprod()
        st.subheader("Strategy vs equal-weight benchmark")
        st.plotly_chart(px.line(pd.DataFrame({"strategy": eq, "equal-weight": beq})))
        c1, c2, c3 = st.columns(3)
        sharpe = s.mean() / s.std() * np.sqrt(252) if s.std() > 0 else 0
        c1.metric("Ann. return", f"{eq.iloc[-1] ** (252 / len(s)) - 1:.1%}")
        c2.metric("Ann. volatility", f"{s.std() * np.sqrt(252):.1%}")
        c3.metric("Sharpe (net)", f"{sharpe:.2f}")