const STACK = [
  {
    stage: "Environment & deps",
    tool: "Poetry",
    why: "Deterministic lockfiles, isolated venvs, one pyproject.toml. Free & open source.",
    alt: "uv (faster, also free) · pip-tools",
  },
  {
    stage: "Market data",
    tool: "yfinance / Yahoo Finance",
    why: "Free daily OHLCV for global tickers, no key. Cached to CSV for reproducibility.",
    alt: "Stooq · Nasdaq Data Link (free tier) · Alpha Vantage free tier",
  },
  {
    stage: "Forecasting model",
    tool: "Meta Prophet",
    why: "Additive trend + seasonality model, robust to gaps, uncertainty intervals out of the box.",
    alt: "NeuralProphet · statsmodels SARIMAX · Darts",
  },
  {
    stage: "Validation",
    tool: "Time-based holdout + MAPE/RMSE",
    why: "Last 60 days held out per asset; no leakage, metrics comparable across tickers.",
    alt: "prophet.diagnostics cross_validation · sktime",
  },
  {
    stage: "Portfolio optimisation",
    tool: "Markowitz via scipy SLSQP",
    why: "min w'Σw s.t. Σw=1, long-only, 35% cap. Σ = Ledoit-Wolf shrunk, μ from Prophet.",
    alt: "PyPortfolioOpt (optional extra) · cvxpy · Riskfolio-Lib",
  },
  {
    stage: "Experiment tracking",
    tool: "MLflow (OSS) or plain JSON artifacts",
    why: "Every run exports results.json + CSVs — diffable, versionable, free.",
    alt: "DVC · Weights & Biases free tier",
  },
  {
    stage: "Automation",
    tool: "GitHub Actions (free tier)",
    why: "Weekly cron: refresh data → refit → reoptimise → commit new artifacts.",
    alt: "cron + make · Prefect OSS",
  },
  {
    stage: "Front-end",
    tool: "React + Vite + Tailwind + Recharts",
    why: "This dashboard. All MIT-licensed.",
    alt: "Plotly Dash · Streamlit (fastest Python-native option)",
  },
];

const STEPS = [
  { n: "01", t: "Ingest", d: "2y daily closes for 10 assets, cached CSVs" },
  { n: "02", t: "Forecast", d: "One Prophet model per asset, 90-day horizon + 95% interval" },
  { n: "03", t: "Validate", d: "60-day holdout per asset → MAPE / RMSE / MAE" },
  { n: "04", t: "Estimate", d: "μ from forecasts · Σ from Ledoit-Wolf shrinkage" },
  { n: "05", t: "Optimise", d: "Markowitz QP → efficient frontier, max-Sharpe, min-vol" },
  { n: "06", t: "Rebalance", d: "Weights → whole-share orders on a $10k book" },
];

export function Methodology() {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {STEPS.map((s, i) => (
          <div key={s.n} className="relative rounded-lg border border-[#1e2632] bg-[#10151c] p-4">
            <div className="font-mono text-[11px] text-emerald-400/80">{s.n}</div>
            <div className="mt-1 font-medium text-[#e5e7eb]">{s.t}</div>
            <div className="mt-1 text-sm leading-relaxed text-[#7d8794]">{s.d}</div>
            {i < STEPS.length - 1 && (
              <div className="absolute -right-2.5 top-1/2 hidden -translate-y-1/2 text-[#334052] lg:block">→</div>
            )}
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-[#1e2632] bg-[#10151c] p-4">
        <h3 className="mb-3 font-mono text-sm uppercase tracking-widest text-[#7d8794]">
          Recommended stack — free tools only
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-[#1e2632] text-left font-mono text-[11px] uppercase tracking-widest text-[#7d8794]">
                <th className="py-2 pr-4 font-normal">Stage</th>
                <th className="py-2 pr-4 font-normal">Tool</th>
                <th className="py-2 pr-4 font-normal">Why</th>
                <th className="py-2 font-normal">Free alternatives</th>
              </tr>
            </thead>
            <tbody>
              {STACK.map((r) => (
                <tr key={r.stage} className="border-b border-[#151b24] align-top last:border-0">
                  <td className="whitespace-nowrap py-2.5 pr-4 font-mono text-[#9aa4b2]">{r.stage}</td>
                  <td className="whitespace-nowrap py-2.5 pr-4 font-medium text-emerald-300">{r.tool}</td>
                  <td className="py-2.5 pr-4 text-[#9aa4b2]">{r.why}</td>
                  <td className="py-2.5 text-[#7d8794]">{r.alt}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
