export interface Backtest {
  dates: string[];
  actual: number[];
  predicted: number[];
}

export interface AssetForecast {
  dates: string[];
  yhat: number[];
  lower: number[];
  upper: number[];
  last_price: number;
  expected_return: number;
  metrics: { mape: number; rmse: number; mae: number };
  backtest: Backtest;
}

export interface FrontierPoint {
  return: number;
  volatility: number;
  sharpe: number;
  weights: Record<string, number>;
}

export interface PortfolioPoint {
  weights: Record<string, number>;
  return: number;
  volatility: number;
  sharpe: number;
}

export interface AllocationRow {
  ticker: string;
  weight: number;
  price: number;
  shares: number;
  value: number;
}

export interface Results {
  as_of: string;
  tickers: string[];
  config: {
    horizon_days: number;
    test_days: number;
    risk_free_rate: number;
    weight_bounds: number[];
    portfolio_value: number;
  };
  prices: { dates: string[]; series: Record<string, number[]> };
  forecasts: Record<string, AssetForecast>;
  optimization: {
    tickers: string[];
    max_sharpe: PortfolioPoint;
    min_volatility: PortfolioPoint;
    frontier: FrontierPoint[];
    risk_free_rate: number;
  };
  rebalance: {
    baseline_weights: Record<string, number>;
    target_weights: Record<string, number>;
    allocation: AllocationRow[];
    leftover_cash: number;
    expected_return: number;
    expected_volatility: number;
    sharpe: number;
  };
}
