import { useMemo, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { results } from "@/data/results";
import { num, pct, shortDate, usd } from "@/lib/format";
import type { AssetForecast } from "@/types/results";

const COLORS = {
  history: "#8b94a3",
  forecast: "#34d399",
  band: "#34d399",
  actual: "#e5e7eb",
  predicted: "#f59e0b",
  grid: "#1c232e",
  text: "#7d8794",
};

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-[#232c38] bg-[#0d1117]/95 px-3 py-2 font-mono text-xs shadow-xl">
      <div className="mb-1 text-[#9aa4b2]">{shortDate(label)}</div>
      {payload.map((p: any) =>
        p.value != null ? (
          <div key={p.dataKey} className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full" style={{ background: p.color || p.stroke }} />
            <span className="text-[#7d8794]">{p.name}:</span>
            <span className="text-[#e5e7eb]">{usd(p.value)}</span>
          </div>
        ) : null
      )}
    </div>
  );
}

function ForecastChart({ ticker, fc }: { ticker: string; fc: AssetForecast }) {
  const data = useMemo(() => {
    const hist = results.prices;
    const histDates = hist.dates;
    const histVals = hist.series[ticker];
    // show last ~9 months of history for readability
    const cut = Math.max(0, histDates.length - 190);
    const rows: any[] = [];
    for (let i = cut; i < histDates.length; i++) {
      rows.push({ date: histDates[i], history: histVals[i], band: [histVals[i], histVals[i]] });
    }
    const lastHist = histVals[histVals.length - 1];
    rows.push({
      date: fc.dates[0],
      history: lastHist,
      forecast: fc.yhat[0],
      band: [fc.lower[0], fc.upper[0]],
    });
    for (let i = 1; i < fc.dates.length; i++) {
      rows.push({ date: fc.dates[i], forecast: fc.yhat[i], band: [fc.lower[i], fc.upper[i]] });
    }
    return rows;
  }, [ticker, fc]);

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="2 6" vertical={false} />
        <XAxis
          dataKey="date"
          tickFormatter={shortDate}
          tick={{ fill: COLORS.text, fontSize: 11, fontFamily: "monospace" }}
          tickLine={false}
          axisLine={{ stroke: COLORS.grid }}
          minTickGap={48}
        />
        <YAxis
          domain={["auto", "auto"]}
          tick={{ fill: COLORS.text, fontSize: 11, fontFamily: "monospace" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `$${Math.round(v)}`}
          width={56}
        />
        <Tooltip content={<ChartTooltip />} />
        <Area
          dataKey="band"
          name="95% interval"
          stroke="none"
          fill={COLORS.band}
          fillOpacity={0.12}
          isAnimationActive={false}
        />
        <Line
          dataKey="history"
          name="History"
          stroke={COLORS.history}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
        <Line
          dataKey="forecast"
          name="Prophet forecast"
          stroke={COLORS.forecast}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

function BacktestChart({ fc }: { fc: AssetForecast }) {
  const data = fc.backtest.dates.map((d, i) => ({
    date: d,
    actual: fc.backtest.actual[i],
    predicted: fc.backtest.predicted[i],
  }));
  return (
    <ResponsiveContainer width="100%" height={200}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={COLORS.grid} strokeDasharray="2 6" vertical={false} />
        <XAxis
          dataKey="date"
          tickFormatter={shortDate}
          tick={{ fill: COLORS.text, fontSize: 10, fontFamily: "monospace" }}
          tickLine={false}
          axisLine={{ stroke: COLORS.grid }}
          minTickGap={40}
        />
        <YAxis
          domain={["auto", "auto"]}
          tick={{ fill: COLORS.text, fontSize: 10, fontFamily: "monospace" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `$${Math.round(v)}`}
          width={52}
        />
        <Tooltip content={<ChartTooltip />} />
        <Line dataKey="actual" name="Actual" stroke={COLORS.actual} strokeWidth={1.8} dot={false} isAnimationActive={false} />
        <Line dataKey="predicted" name="Predicted" stroke={COLORS.predicted} strokeWidth={1.8} strokeDasharray="5 3" dot={false} isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function ForecastExplorer() {
  const tickers = results.tickers;
  const [ticker, setTicker] = useState(tickers[0]);
  const fc = results.forecasts[ticker];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">
        {tickers.map((t) => {
          const er = results.forecasts[t].expected_return;
          const active = t === ticker;
          return (
            <button
              key={t}
              onClick={() => setTicker(t)}
              className={`min-h-[44px] rounded-md border px-3.5 py-2 font-mono text-sm transition-colors ${
                active
                  ? "border-emerald-400/60 bg-emerald-400/10 text-emerald-300"
                  : "border-[#232c38] bg-[#10151c] text-[#9aa4b2] hover:border-[#334052] hover:text-[#cbd3dd]"
              }`}
            >
              {t}
              <span className={`ml-2 text-xs ${er >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {pct(er, 0, true)}
              </span>
            </button>
          );
        })}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-[#1e2632] bg-[#10151c] p-4 lg:col-span-2">
          <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="font-mono text-sm uppercase tracking-widest text-[#7d8794]">
              {ticker} — {results.config.horizon_days}-day Prophet forecast
            </h3>
            <span className="font-mono text-xs text-[#7d8794]">
              last <span className="text-[#e5e7eb]">{usd(fc.last_price)}</span>
            </span>
          </div>
          <ForecastChart ticker={ticker} fc={fc} />
        </div>

        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-3 gap-3 lg:grid-cols-1">
            {[
              { label: "MAPE", value: `${num(fc.metrics.mape)}%`, hint: "mean abs. % error" },
              { label: "RMSE", value: `$${num(fc.metrics.rmse)}`, hint: "root mean sq. error" },
              { label: "Exp. return", value: pct(fc.expected_return, 1, true), hint: "annualised, from forecast" },
            ].map((m) => (
              <div key={m.label} className="rounded-lg border border-[#1e2632] bg-[#10151c] p-4">
                <div className="font-mono text-[11px] uppercase tracking-widest text-[#7d8794]">{m.label}</div>
                <div className={`mt-1 font-mono text-xl ${m.label === "Exp. return" ? (fc.expected_return >= 0 ? "text-emerald-300" : "text-rose-300") : "text-[#e5e7eb]"}`}>
                  {m.value}
                </div>
                <div className="mt-0.5 text-[11px] text-[#5d6774]">{m.hint} · {results.config.test_days}d holdout</div>
              </div>
            ))}
          </div>
          <div className="flex-1 rounded-lg border border-[#1e2632] bg-[#10151c] p-4">
            <h4 className="mb-2 font-mono text-[11px] uppercase tracking-widest text-[#7d8794]">
              Backtest — actual vs predicted
            </h4>
            <BacktestChart fc={fc} />
          </div>
        </div>
      </div>
    </div>
  );
}
