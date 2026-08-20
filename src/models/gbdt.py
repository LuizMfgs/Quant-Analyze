import lightgbm as lgb
import pandas as pd

from ..features import FEATURE_COLS
from .base import ReturnForecaster

DEFAULTS = dict(n_estimators=400, learning_rate=0.03, num_leaves=31,
                min_child_samples=50, subsample=0.8, colsample_bytree=0.8,
                reg_lambda=1.0, random_state=42)


class LGBMForecaster(ReturnForecaster):
    name = "lgbm"

    def __init__(self, params=None):
        self.params = {**DEFAULTS, **(params or {})}

    def _prep(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X[FEATURE_COLS + ["ticker"]].copy()
        # universe is fixed; if you ever predict an unseen ticker it maps to NaN→missing
        X["ticker"] = X["ticker"].astype("category")
        return X

    def fit(self, X, y):
        self.model = lgb.LGBMRegressor(verbose=-1, **self.params)
        self.model.fit(self._prep(X), y, categorical_feature=["ticker"])
        return self

    def predict(self, X):
        return self.model.predict(self._prep(X))