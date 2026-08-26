import numpy as np

from .base import ReturnForecaster


class RandomWalk(ReturnForecaster):
    """The null hypothesis of markets: expected return = 0."""
    name = "random_walk"

    def fit(self, X, y): pass

    def predict(self, X):
        return np.zeros(len(X))


class HistoricalMean(ReturnForecaster):
    name = "hist_mean"

    def fit(self, X, y):
        self.mu = float(y.mean())

    def predict(self, X):
        return np.full(len(X), self.mu)