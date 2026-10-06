import { EfficientFrontier } from "@/components/EfficientFrontier";
import { ForecastExplorer } from "@/components/ForecastExplorer";
import { Methodology } from "@/components/Methodology";
import { RebalanceBoard } from "@/components/RebalanceBoard";
import { results } from "@/data/results";
import { num, pct, usd } from "@/lib/format";

function SectionHeading({ index, title, sub }: { index: string; title: string; sub: string }) {
  return (
    <div className="mb-5">
      <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-emerald-400/80">{index}</div>
      <h2 className="mt-1 text-xl font-semibold text-[#e5e7eb] sm:text-2xl">{title}</h2>
      <p className="mt-1 max-w-2xl text-sm text-[#7d8794]">{sub}</p>
    </div>
  );
}

function Kpis() {
  const rb = results.rebalance;
  const mapes = results.tickers.map((t) => results.forecasts[t].metrics.mape);
  const avgMape = mapes.reduce((a, b) => a + b, 0) / mapes.length;
  const kpis = [
    { label: "Expected return", value: pct(rb.expected_return, 1, true), sub: "annualised · max-Sharpe", tone: rb.expected_return >= 0 ? "up" : "down" },
    { label: "Expected volatility", value: pct(rb.expected_volatility), sub: "annualised, from Σ", tone: "flat" },
    { label: "Sharpe ratio", value: num(rb.sharpe), sub: `rf = ${pct(results.config.risk_free_rate)}`, tone: "flat" },
    { label: "Avg forecast MAPE", value: `${num(avgMape)}%`, sub: `${results.config.test_days}-day holdout, 10 assets`, tone: "flat" },
    { label: "Book size", value: usd(results.config.portfolio_value, 0), sub: "discrete allocation basis", tone: "flat" },
  ] as const;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {kpis.map((k) => (
        <div key={k.label} className="rounded-lg border border-[#1e2632] bg-[#10151c] p-4">
          <div className="font-mono text-[10px] uppercase tracking-widest text-[#7d8794]">{k.label}</div>
          <div
            className={`mt-1.5 font-mono text-2xl ${
              k.tone === "up" ? "text-emerald-300" : k.tone === "down" ? "text-rose-300" : "text-[#e5e7eb]"
            }`}
          >
            {k.value}
          </div>
          <div className="mt-0.5 text-[11px] text-[#5d6774]">{k.sub}</div>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-[#0b0f14] text-[#c6ced9] antialiased">
      <div className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        {/* hero */}
        <header className="border-b border-[#1e2632] py-10 sm:py-14">
          <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-emerald-400/80">
            End-to-end ML · Python + Poetry
          </div>
          <h1 className="mt-3 text-3xl font-semibold leading-tight text-[#f3f5f7] sm:text-5xl">
            Prophet forecasts,
            <br />
            <span className="text-[#7d8794]">Markowitz allocations.</span>
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-[#9aa4b2] sm:text-base">
            Ten assets, two years of daily prices. Each series is forecast 90 days forward with Meta
            Prophet; the forecast returns become μ in a mean-variance optimisation that rebalances a{" "}
            {usd(results.config.portfolio_value, 0)} portfolio. As of{" "}
            <span className="font-mono text-[#e5e7eb]">{results.as_of}</span>.
          </p>
          <div className="mt-6 flex flex-wrap gap-2 font-mono text-[11px]">
            {["prophet 1.5", "scipy SLSQP", "Ledoit-Wolf Σ", "long-only ≤35%", `${results.config.horizon_days}d horizon`].map(
              (b) => (
                <span key={b} className="rounded border border-[#232c38] bg-[#10151c] px-2.5 py-1.5 text-[#9aa4b2]">
                  {b}
                </span>
              )
            )}
          </div>
        </header>

        <main className="space-y-14 pt-10">
          <section>
            <Kpis />
          </section>

          <section>
            <SectionHeading
              index="01 / Forecast"
              title="Per-asset Prophet models"
              sub="Trend + weekly seasonality, fit on 2 years of closes. The shaded band is the 95% uncertainty interval; the side panel shows holdout accuracy and the implied annual return."
            />
            <ForecastExplorer />
          </section>

          <section>
            <SectionHeading
              index="02 / Optimise"
              title="The efficient frontier"
              sub="Forecast μ against shrunk-covariance risk. Every blue point is an optimal long-only portfolio; green is the tangency (max-Sharpe) portfolio the rebalance uses."
            />
            <EfficientFrontier />
          </section>

          <section>
            <SectionHeading
              index="03 / Rebalance"
              title="From weights to orders"
              sub="Target weights versus the equal-weight baseline, translated into whole-share orders at last close."
            />
            <RebalanceBoard />
          </section>

          <section>
            <SectionHeading
              index="04 / Reproduce"
              title="Pipeline & free toolchain"
              sub="Everything below is open source or free-tier. Clone, poetry install, forecast-portfolio run."
            />
            <Methodology />
          </section>
        </main>

        <footer className="mt-16 border-t border-[#1e2632] pt-6 text-xs leading-relaxed text-[#5d6774]">
          Educational demo, not investment advice. Prophet extrapolates trend/seasonality and cannot see news,
          earnings or regime breaks; forecast-based μ is the weakest link in mean-variance optimisation —
          shrink it, cap weights, and rebalance on a schedule, not on impulse.
        </footer>
      </div>
    </div>
  );
}
