import { results } from "@/data/results";
import { num, pct, usd } from "@/lib/format";

export function RebalanceBoard() {
  const rb = results.rebalance;
  const tickers = results.tickers;
  const invested = rb.allocation.reduce((s, a) => s + a.value, 0);

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {/* weight shifts */}
      <div className="rounded-lg border border-[#1e2632] bg-[#10151c] p-4">
        <h3 className="mb-1 font-mono text-sm uppercase tracking-widest text-[#7d8794]">
          Rebalance — equal weight → forecast-optimised
        </h3>
        <p className="mb-4 text-xs text-[#5d6774]">
          Max-Sharpe target weights vs the naive 1/N baseline. Long-only, capped at{" "}
          {pct(results.config.weight_bounds[1], 0)} per asset.
        </p>
        <div className="space-y-2.5">
          {tickers
            .slice()
            .sort((a, b) => rb.target_weights[b] - rb.target_weights[a])
            .map((t) => {
              const base = rb.baseline_weights[t];
              const tgt = rb.target_weights[t];
              const delta = tgt - base;
              return (
                <div key={t} className="grid grid-cols-[3.2rem_1fr_4.6rem] items-center gap-3">
                  <span className="font-mono text-sm text-[#c6ced9]">{t}</span>
                  <div className="relative h-5 overflow-hidden rounded bg-[#0b0f14]">
                    <div
                      className="absolute inset-y-0 left-0 bg-[#3b82f6]/35"
                      style={{ width: `${base * 100 * 2.5}%` }}
                    />
                    <div
                      className="absolute inset-y-0 left-0 rounded-r bg-emerald-400/80"
                      style={{ width: `${tgt * 100 * 2.5}%` }}
                    />
                  </div>
                  <span
                    className={`text-right font-mono text-xs ${
                      delta > 0.001 ? "text-emerald-300" : delta < -0.001 ? "text-rose-300" : "text-[#7d8794]"
                    }`}
                  >
                    {pct(tgt, 1)} ({delta > 0 ? "+" : ""}
                    {pct(delta, 1)})
                  </span>
                </div>
              );
            })}
        </div>
        <div className="mt-4 flex gap-6 font-mono text-[11px] text-[#7d8794]">
          <span><span className="mr-1.5 inline-block h-2 w-2 bg-emerald-400/80" />target</span>
          <span><span className="mr-1.5 inline-block h-2 w-2 bg-[#3b82f6]/50" />equal-weight 1/N</span>
        </div>
      </div>

      {/* discrete allocation */}
      <div className="rounded-lg border border-[#1e2632] bg-[#10151c] p-4">
        <h3 className="mb-1 font-mono text-sm uppercase tracking-widest text-[#7d8794]">
          Discrete allocation — {usd(results.config.portfolio_value, 0)} portfolio
        </h3>
        <p className="mb-3 text-xs text-[#5d6774]">
          Whole-share orders at last close; {usd(rb.leftover_cash)} left in cash.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full font-mono text-sm">
            <thead>
              <tr className="border-b border-[#1e2632] text-left text-[11px] uppercase tracking-widest text-[#7d8794]">
                <th className="py-2 pr-3 font-normal">Ticker</th>
                <th className="py-2 pr-3 text-right font-normal">Weight</th>
                <th className="py-2 pr-3 text-right font-normal">Price</th>
                <th className="py-2 pr-3 text-right font-normal">Shares</th>
                <th className="py-2 text-right font-normal">Value</th>
              </tr>
            </thead>
            <tbody>
              {rb.allocation.map((a) => (
                <tr key={a.ticker} className="border-b border-[#151b24] last:border-0">
                  <td className="py-2 pr-3 text-[#e5e7eb]">{a.ticker}</td>
                  <td className="py-2 pr-3 text-right text-[#9aa4b2]">{pct(a.weight, 1)}</td>
                  <td className="py-2 pr-3 text-right text-[#9aa4b2]">{usd(a.price)}</td>
                  <td className={`py-2 pr-3 text-right ${a.shares === 0 ? "text-[#5d6774]" : "text-emerald-300"}`}>
                    {a.shares}
                  </td>
                  <td className="py-2 text-right text-[#c6ced9]">{usd(a.value)}</td>
                </tr>
              ))}
              <tr className="border-t border-[#1e2632] text-[#9aa4b2]">
                <td className="py-2 pr-3" colSpan={4}>Invested / cash</td>
                <td className="py-2 text-right">{usd(invested)} <span className="text-[#5d6774]">+ {usd(rb.leftover_cash)}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="mt-3 font-mono text-[11px] leading-relaxed text-[#5d6774]">
          Expected: return {pct(rb.expected_return, 1, true)} · vol {pct(rb.expected_volatility)} · Sharpe{" "}
          {num(rb.sharpe)} — annualised, before costs & taxes.
        </p>
      </div>
    </div>
  );
}
