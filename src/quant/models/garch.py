import numpy as np
from arch import arch_model


def garch_vol_forecast(returns, horizon: int) -> float:
    """Annualized vol over the next `horizon` days, GARCH(1,1)-t per asset.
    Falls back to realized vol on failure. `returns`: daily log-return Series."""
    r = returns.dropna().values * 100.0          # arch prefers scaled data
    if len(r) < 100:
        return float(np.std(r, ddof=1) / 100 * np.sqrt(252))
    try:
        res = arch_model(r, vol="Garch", p=1, q=1, dist="t").fit(disp="off")
        var_h = res.forecast(horizon=horizon, reindex=False).variance.iloc[-1].sum()
        var_h /= 100 ** 2                         # back to decimal-return variance
        return float(np.sqrt(var_h * 252 / horizon))
    except Exception:
        return float(np.std(r[-63:], ddof=1) / 100 * np.sqrt(252))