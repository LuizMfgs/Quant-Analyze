import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ReferenceDot,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { results } from "@/data/results";
import { pct } from "@/lib/format";

const GRID = "#1c232e";
const TEXT = "#7d8794";

function FrontierTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-md border border-[#232c38] bg-[#0d1117]/95 px-3 py-2 font-mono text-xs shadow-xl">
      <div className="text-[#9aa4b2]">return <span className="text-emerald-300">{pct(p.return)}</span></div>
      <div className="text-[#9aa4b2]">volatility <span className="text-[#e5e7eb]">{pct(p.volatility)}</span></div>
      <div className="text-[#9aa4b2]">Sharpe <span className="text-amber-300">{p.sharpe.toFixed(2)}</span></div>
    </div>
  );
}

export function EfficientFrontier() {
  const opt = results.optimization;
  const frontier = opt.frontier.map((p) => ({ ...p, z: 1 }));
  const ms = opt.max_sharpe;
  const mv = opt.min_volatility;

  return (
    <div className="grid gap-4 lg:grid-cols-5">
      <div className="rounded-lg border border-[#1e2632] bg-[#10151c] p-4 lg:col-span-3">
        <h3 className="mb-1 font-mono text-sm uppercase tracking-widest text-[#7d8794]">
          Efficient frontier — {opt.frontier.length} optimal portfolios
        </h3>
        <p className="mb-2 text-xs text-[#5d6774]">
          Each point minimises variance for a target return, given Prophet's μ and the shrunk covariance Σ.
        </p>
        <ResponsiveContainer width="100%" height={360}>
          <ScatterChart margin={{ top: 12, right: 16, bottom: 4, left: 0 }}>
            <CartesianGrid stroke={GRID} strokeDasharray="2 6" />
            <XAxis
              type="number"
              dataKey="volatility"
              domain={["auto", "auto"]}
              tickFormatter={(v) => pct(v, 0)}
              tick={{ fill: TEXT, fontSize: 11, fontFamily: "monospace" }}
              tickLine={false}
              axisLine={{ stroke: GRID }}
              name="volatility"
              label={{ value: "annualised volatility →", position: "insideBottomRight", fill: TEXT, fontSize: 11, fontFamily: "monospace" }}
            />
            <YAxis
              type="number"
              dataKey="return"
              domain={["auto", "auto"]}
              tickFormatter={(v) => pct(v, 0)}
              tick={{ fill: TEXT, fontSize: 11, fontFamily: "monospace" }}
              tickLine={false}
              axisLine={false}
              width={48}
              name="return"
            />
            <ZAxis type="number" dataKey="z" range={[28, 28]} />
            <Tooltip content={<FrontierTooltip />} cursor={{ strokeDasharray: "3 3", stroke: "#334052" }} />
            <Scatter data={frontier} fill="#3b82f6" fillOpacity={0.55} isAnimationActive={false} />
            <ReferenceDot x={ms.volatility} y={ms.return} r={8} fill="#34d399" stroke="#0d1117" strokeWidth={2} />
            <ReferenceDot x={mv.volatility} y={mv.return} r={8} fill="#f59e0b" stroke="#0d1117" strokeWidth={2} />
          </ScatterChart>
        </ResponsiveContainer>
        <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 font-mono text-xs text-[#9aa4b2]">
          <span><span className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full bg-[#34d399]" />Max Sharpe {ms.sharpe.toFixed(2)} — {pct(ms.return)} / {pct(ms.volatility)}</span>
          <span><span className="mr-1.5 inline-block h-2.5 w-2.5 rounded-full bg-[#f59e0b]" />Min volatility — {pct(mv.return)} / {pct(mv.volatility)}</span>
          <span className="text-[#5d6774]">rf = {pct(opt.risk_free_rate)}</span>
        </div>
      </div>

      <ExpectedReturnsBars />
    </div>
  );
}

function ExpectedReturnsBars() {
  const data = useMemo(
    () =>
      results.tickers
        .map((t) => ({ ticker: t, er: results.forecasts[t].expected_return }))
        .sort((a, b) => b.er - a.er),
    []
  );
  return (
    <div className="rounded-lg border border-[#1e2632] bg-[#10151c] p-4 lg:col-span-2">
      <h3 className="mb-1 font-mono text-sm uppercase tracking-widest text-[#7d8794]">
        μ — forecast expected returns
      </h3>
      <p className="mb-2 text-xs text-[#5d6774]">
        Annualised from each {results.config.horizon_days}-day Prophet path; these feed Markowitz.
      </p>
      <ResponsiveContainer width="100%" height={360}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 44, bottom: 4, left: 8 }}>
          <CartesianGrid stroke={GRID} strokeDasharray="2 6" horizontal={false} />
          <XAxis
            type="number"
            tickFormatter={(v) => pct(v, 0)}
            tick={{ fill: TEXT, fontSize: 11, fontFamily: "monospace" }}
            tickLine={false}
            axisLine={{ stroke: GRID }}
          />
          <YAxis
            type="category"
            dataKey="ticker"
            tick={{ fill: "#c6ced9", fontSize: 12, fontFamily: "monospace" }}
            tickLine={false}
            axisLine={false}
            width={52}
          />
          <Tooltip
            cursor={{ fill: "#ffffff08" }}
            content={({ active, payload }: any) =>
              active && payload?.length ? (
                <div className="rounded-md border border-[#232c38] bg-[#0d1117]/95 px-3 py-2 font-mono text-xs text-[#e5e7eb] shadow-xl">
                  {payload[0].payload.ticker}: {pct(payload[0].value, 1, true)}
                </div>
              ) : null
            }
          />
          <Bar dataKey="er" radius={[0, 3, 3, 0]} isAnimationActive={false}>
            {data.map((d) => (
              <Cell key={d.ticker} fill={d.er >= 0 ? "#34d399" : "#f43f5e"} fillOpacity={0.85} />
            ))}
            <LabelList
              dataKey="er"
              position="right"
              formatter={(v: number) => pct(v, 0, true)}
              style={{ fill: TEXT, fontSize: 11, fontFamily: "monospace" }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
