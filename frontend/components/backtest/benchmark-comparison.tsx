"use client";
import React from "react";
import { BacktestSummary } from "@/lib/api";

interface Props {
  summary: BacktestSummary;
}

function pct(v: number | null) {
  if (v == null) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
}
function dec(v: number | null, d = 2) {
  return v == null ? "—" : v.toFixed(d);
}

export function BenchmarkComparison({ summary: s }: Props) {
  const rows = [
    {
      label:    "Total Return",
      strategy: pct(s.total_return),
      bench:    pct(s.benchmark_return),
      better:   (s.total_return ?? 0) > (s.benchmark_return ?? 0),
    },
    {
      label:    "Annualized Return",
      strategy: pct(s.annualized_return),
      bench:    "N/A (B&H ~same)",
      better:   null,
    },
    {
      label:    "Alpha",
      strategy: pct(s.alpha),
      bench:    "0.00%",
      better:   (s.alpha ?? 0) > 0,
    },
    {
      label:    "Sharpe Ratio",
      strategy: dec(s.sharpe_ratio),
      bench:    "—",
      better:   null,
    },
    {
      label:    "Max Drawdown",
      strategy: pct(s.max_drawdown),
      bench:    "—",
      better:   (s.max_drawdown ?? 0) > -20 ? true : false,
    },
    {
      label:    "Win Rate",
      strategy: `${dec(s.win_rate, 1)}%`,
      bench:    "N/A",
      better:   null,
    },
    {
      label:    "Profit Factor",
      strategy: dec(s.profit_factor),
      bench:    "N/A",
      better:   (s.profit_factor ?? 0) > 1 ? true : false,
    },
  ];

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-slate-200">Strategy vs Benchmark (Buy &amp; Hold)</h3>
        <p className="text-xs text-slate-500 mt-0.5">{s.ticker} — {s.start_date} to {s.end_date}</p>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-slate-800/50">
          <tr>
            <th className="px-5 py-2 text-left text-xs font-medium text-slate-400">Metric</th>
            <th className="px-5 py-2 text-right text-xs font-medium text-cyan-400">Strategy</th>
            <th className="px-5 py-2 text-right text-xs font-medium text-amber-400">Benchmark</th>
            <th className="px-5 py-2 text-center text-xs font-medium text-slate-400">Edge</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-slate-800/60">
              <td className="px-5 py-2.5 text-slate-400">{row.label}</td>
              <td className="px-5 py-2.5 text-right font-mono font-medium text-slate-100">{row.strategy}</td>
              <td className="px-5 py-2.5 text-right font-mono text-slate-400">{row.bench}</td>
              <td className="px-5 py-2.5 text-center">
                {row.better === true  && <span className="text-emerald-400 text-sm">✓</span>}
                {row.better === false && <span className="text-rose-400 text-sm">✗</span>}
                {row.better === null  && <span className="text-slate-600 text-sm">—</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
