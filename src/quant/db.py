import json
import os
from contextlib import contextmanager

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


@contextmanager
def get_cursor():
    conn = get_conn()
    try:
        with conn:                      # commits on success, rolls back on error
            with conn.cursor() as cur:
                yield cur
    finally:
        conn.close()


def fetch_df(query, params=None) -> pd.DataFrame:
    conn = get_conn()
    try:
        return pd.read_sql(query, conn, params=params)
    finally:
        conn.close()


# ---------- assets ----------

def ensure_assets(tickers, asset_class="equity") -> dict:
    """Upsert tickers, return {ticker: asset_id}."""
    with get_cursor() as cur:
        execute_values(cur, """
            insert into assets (ticker, asset_class) values %s
            on conflict (ticker) do update set is_active = true
        """, [(t, asset_class) for t in tickers])
        cur.execute("select ticker, id from assets where ticker = any(%s)",
                    (list(tickers),))
        return dict(cur.fetchall())


# ---------- prices ----------

def upsert_prices(df: pd.DataFrame, source="yfinance"):
    """df columns: ticker, date, open, high, low, close, adj_close, volume."""
    if df.empty:
        return
    ids = ensure_assets(df["ticker"].unique().tolist())
    rows = [
        (ids[r.ticker], r.date, r.open, r.high, r.low, r.close, r.adj_close,
         int(r.volume) if pd.notna(r.volume) else None, source)
        for r in df.itertuples(index=False)
    ]
    with get_cursor() as cur:
        execute_values(cur, """
            insert into prices (asset_id, date, open, high, low, close, adj_close, volume, source)
            values %s
            on conflict (asset_id, date) do update set
              open=excluded.open, high=excluded.high, low=excluded.low,
              close=excluded.close, adj_close=excluded.adj_close,
              volume=excluded.volume, source=excluded.source
        """, rows, page_size=1000)


def load_prices(tickers=None, start=None) -> pd.DataFrame:
    q = """select a.ticker, p.date, p.open, p.high, p.low, p.close, p.adj_close, p.volume
           from prices p join assets a on a.id = p.asset_id
           where a.is_active"""
    params = []
    if tickers:
        q += " and a.ticker = any(%s)"
        params.append(list(tickers))
    if start:
        q += " and p.date >= %s"
        params.append(str(start))
    df = fetch_df(q, params or None)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)


def last_price_dates(tickers) -> dict:
    q = """select a.ticker, max(p.date) from assets a
           left join prices p on p.asset_id = a.id
           where a.ticker = any(%s) group by a.ticker"""
    df = fetch_df(q, (list(tickers),))
    return dict(zip(df["ticker"], df["max"]))


# ---------- models & forecasts ----------

def register_model(name, algorithm, hyperparams=None, metrics=None) -> str:
    with get_cursor() as cur:
        cur.execute("update models set is_active = false where algorithm = %s and is_active",
                    (algorithm,))
        cur.execute("""insert into models (name, algorithm, hyperparameters)
                       values (%s, %s, %s) returning id""",
                    (name, algorithm, json.dumps(hyperparams or {})))
        model_id = cur.fetchone()[0]
        if metrics:
            cur.execute("insert into eval_results (model_id, metric) values (%s, %s)",
                        (model_id, json.dumps(metrics, default=float)))
    return model_id


def upload_artifact(model_id, model, bucket="model-artifacts"):
    """Persist fitted model to Supabase Storage. Create the (private) bucket once in the UI."""
    import io
    import joblib
    from supabase import create_client
    buf = io.BytesIO()
    joblib.dump(model, buf)
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    sb.storage.from_(bucket).upload(f"{model_id}.joblib", buf.getvalue())
    with get_cursor() as cur:
        cur.execute("update models set artifact_path = %s where id = %s",
                    (f"{bucket}/{model_id}.joblib", model_id))


def save_forecasts(model_id, df: pd.DataFrame):
    """df columns: ticker, forecast_date, target_date, horizon_days,
    expected_return, interval_low, interval_high."""
    ids = ensure_assets(df["ticker"].unique().tolist())
    rows = [(model_id, ids[r.ticker], r.forecast_date, r.target_date, r.horizon_days,
             float(r.expected_return), float(r.interval_low), float(r.interval_high))
            for r in df.itertuples(index=False)]
    with get_cursor() as cur:
        execute_values(cur, """
            insert into forecasts (model_id, asset_id, forecast_date, target_date,
                                   horizon_days, expected_return, interval_low, interval_high)
            values %s
            on conflict (model_id, asset_id, forecast_date, target_date) do update set
              expected_return = excluded.expected_return,
              interval_low = excluded.interval_low,
              interval_high = excluded.interval_high
        """, rows)


def latest_forecasts(days=30) -> pd.DataFrame:
    return fetch_df(f"""
        select a.ticker, f.forecast_date, f.target_date, f.horizon_days,
               f.expected_return, f.interval_low, f.interval_high, m.algorithm
        from forecasts f
        join assets a on a.id = f.asset_id
        join models m on m.id = f.model_id
        where m.is_active
          and f.forecast_date >= current_date - interval '{days} days'
        order by f.forecast_date desc, a.ticker
    """)


# ---------- rebalances ----------

def save_rebalance(weights: pd.Series, date, rationale="", config=None) -> int:
    ids = ensure_assets(list(weights.index))
    with get_cursor() as cur:
        cur.execute("""insert into rebalances (rebalance_date, optimizer_config, rationale)
                       values (%s, %s, %s) returning id""",
                    (date, json.dumps(config or {}, default=str), rationale))
        rid = cur.fetchone()[0]
        execute_values(cur, """
            insert into target_weights (rebalance_id, asset_id, weight) values %s
        """, [(rid, ids[t], float(w)) for t, w in weights.items() if w > 1e-6])
    return rid


def latest_rebalance():
    """Returns (date, weights Series) of the most recent rebalance, or (None, None)."""
    with get_cursor() as cur:
        cur.execute("""select id, rebalance_date from rebalances
                       order by rebalance_date desc limit 1""")
        row = cur.fetchone()
        if not row:
            return None, None
        rid, d = row
        cur.execute("""select a.ticker, tw.weight from target_weights tw
                       join assets a on a.id = tw.asset_id
                       where tw.rebalance_id = %s""", (rid,))
        w = pd.Series({t: float(v) for t, v in cur.fetchall()})
        return d, w


def save_portfolio_return(date, net_return, portfolio_name="default"):
    with get_cursor() as cur:
        cur.execute("""insert into portfolio_returns (portfolio_id, date, net_return)
                       select id, %s, %s from portfolios where name = %s
                       on conflict (portfolio_id, date) do update
                       set net_return = excluded.net_return""",
                    (date, float(net_return), portfolio_name))


def portfolio_returns(portfolio_name="default") -> pd.DataFrame:
    return fetch_df("""select pr.date, pr.net_return from portfolio_returns pr
                       join portfolios p on p.id = pr.portfolio_id
                       where p.name = %s order by pr.date""", (portfolio_name,))