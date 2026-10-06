"""Configuration loading (YAML + pydantic validation)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class DataConfig(BaseModel):
    period: str = "2y"
    interval: str = "1d"
    cache_dir: Path = PROJECT_ROOT / "data" / "raw"


class ProphetConfig(BaseModel):
    daily_seasonality: bool = False
    weekly_seasonality: bool = True
    yearly_seasonality: bool = True
    changepoint_prior_scale: float = 0.05


class ForecastConfig(BaseModel):
    horizon_days: int = 90
    test_days: int = 60
    prophet: ProphetConfig = Field(default_factory=ProphetConfig)


class OptimizationConfig(BaseModel):
    risk_free_rate: float = 0.04
    weight_bounds: tuple[float, float] = (0.0, 0.35)
    frontier_points: int = 40


class RebalanceConfig(BaseModel):
    portfolio_value: float = 10_000.0


class Settings(BaseModel):
    tickers: list[str]
    data: DataConfig = Field(default_factory=DataConfig)
    forecast: ForecastConfig = Field(default_factory=ForecastConfig)
    optimization: OptimizationConfig = Field(default_factory=OptimizationConfig)
    rebalance: RebalanceConfig = Field(default_factory=RebalanceConfig)

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> "Settings":
        path = Path(path or PROJECT_ROOT / "config" / "settings.yaml")
        with open(path) as f:
            return cls(**yaml.safe_load(f))
