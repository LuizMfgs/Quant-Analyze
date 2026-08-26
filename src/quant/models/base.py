from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class ReturnForecaster(ABC):
    name: str = "base"

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series): ...

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray: ...