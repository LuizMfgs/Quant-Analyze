import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf, OAS

TRADING_DAYS = 252


def shrunk_cov(returns: pd.DataFrame, method="ledoit_wolf") -> pd.DataFrame:
    """returns: date × ticker daily returns → annualized shrunk covariance."""
    X = returns.dropna().values
    est = LedoitWolf() if method == "ledoit_wolf" else OAS()
    S = est.fit(X).covariance_ if method != "sample" else np.cov(X, rowvar=False)
    return pd.DataFrame(S * TRADING_DAYS, index=returns.columns, columns=returns.columns)