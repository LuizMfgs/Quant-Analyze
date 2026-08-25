import numpy as np
import pandas as pd
from pypfopt import BlackLittermanModel, EfficientFrontier, HRPOpt, objective_functions


def implied_returns(S: pd.DataFrame, w_mkt: pd.Series, risk_aversion=2.5) -> pd.Series:
    return risk_aversion * S.dot(w_mkt)


def black_litterman(S, w_mkt, views: pd.Series, view_var: pd.Series,
                    tau=0.05, risk_aversion=2.5):
    """
    views:     annualized expected return per ticker (model forecast).
    view_var:  per-view variance (annualized residual variance of the forecaster).
    """
    pi = implied_returns(S, w_mkt, risk_aversion)
    idx = views.dropna().index.intersection(S.index)
    omega = np.diag(view_var.reindex(idx).fillna(view_var.mean()).values)
    bl = BlackLittermanModel(cov_matrix=S, pi=pi,
                             absolute_views=views.reindex(idx).to_dict(),
                             omega=omega, tau=tau)
    return bl.bl_returns(), bl.bl_cov()


def optimize(mu: pd.Series, S: pd.DataFrame, objective="max_sharpe",
             bounds=(0.0, 0.30), l2_gamma=None, target_vol=0.15) -> pd.Series:
    ef = EfficientFrontier(mu, S, weight_bounds=bounds)
    try:
        if objective == "max_sharpe":
            ef.max_sharpe(risk_free_rate=0.0)
        elif objective == "efficient_risk":
            if l2_gamma:
                ef.add_objective(objective_functions.L2_regularization, gamma=l2_gamma)
            ef.efficient_risk(target_volatility=target_vol)
        elif objective == "min_volatility":
            ef.min_volatility()
        else:
            raise ValueError(objective)
    except Exception:
        # e.g. max_sharpe with all-negative mu — degrade gracefully
        ef = EfficientFrontier(mu, S, weight_bounds=bounds)
        ef.min_volatility()
    w = pd.Series(ef.clean_weights()).reindex(S.index).fillna(0.0)
    return w / w.sum()          # numerical hygiene


def hrp_weights(returns: pd.DataFrame) -> pd.Series:
    w = HRPOpt(returns=returns.dropna()).optimize()
    return pd.Series(w)