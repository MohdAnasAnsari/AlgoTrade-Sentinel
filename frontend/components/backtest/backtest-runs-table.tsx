"use client";
import React, { useState } from "react";
import { BacktestSummary } from "@/lib/api";

type SortKey = "created_at" | "ticker" | "total_return" | "sharpe_ratio" | "max_drawdown" | "win_rate";

interface Props {
  runs:          BacktestSummary[];
  selectedRunId: string | null;
  onSelect:      (run: BacktestSummary) => void;
}

function pct(v: number | null) {
  return v == null ? "—" : `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
}
function dec(v: number | null, d = 4) {
  return v == null ? "—" : v.toFixed(d);
}
function fmtDate(s: string | null) {
  if (!s) return "—";
  return new Date(s).toLocaleDateString("en-GB", { dateStyle: "short" });
}

export function BacktestRunsTable({ runs, selectedRunId, onSelect }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("created_at");
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = [...runs].sort((a, b) => {
    const av = a[sortKey] ?? null;
    const bv = b[sortKey] ?? null;
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    const dir = sortAsc ? 1 : -1;
    return av < bv ? -dir : av > bv ? dir : 0;
  });

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortAsc((p) => !p);
    else { setSortKey(key); setSortAsc(false); }
  }

  const Th = ({ col, label }: { col: SortKey; label: string }) => (
    <th
      onClick={() => handleSort(col)}
      className="px-3 py-2 text-left text-xs font-medium text-slate-400 cursor-pointer hover:text-slate-200 select-none whitespace-nowrap"
    >
      {label}{sortKey === col ? (sortAsc ? " ↑" : " ↓") : ""}
    </th>
  );

  if (runs.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 text-center text-slate-500 text-sm">
        No backtest runs yet. Configure and run a backtest above.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-800/60 border-b border-slate-700">
            <tr>
              <Th col="ticker"       label="Ticker" />
              <th className="px-3 py-2 text-left text-xs font-medium text-slate-400">Strategy</th>
              <Th col="total_return"  label="Total Ret" />
              <th className="px-3 py-2 text-left text-xs font-medium text-slate-400">Alpha</th>
              <Th col="sharpe_ratio"  label="Sharpe" />
              <Th col="max_drawdown"  label="Max DD" />
              <Th col="win_rate"      label="Win Rate" />
              <th className="px-3 py-2 text-left text-xs font-medium text-slate-400">Trades</th>
              <Th col="created_at"    label="Date" />
            </tr>
          </thead>
          <tbody>
            {sorted.map((run) => {
              const selected = run.run_id === selectedRunId;
              const retColor = (run.total_return ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400";
              const ddColor  = "text-rose-400";
              return (
                <tr
                  key={run.run_id}
                  onClick={() => onSelect(run)}
                  className={`border-b border-slate-800 cursor-pointer transition-colors ${
                    selected ? "bg-cyan-900/25 border-l-2 border-l-cyan-500" : "hover:bg-slate-800/40"
                  }`}
                >
                  <td className="px-3 py-2 font-semibold text-slate-100">{run.ticker}</td>
                  <td className="px-3 py-2 text-slate-400 text-xs truncate max-w-[120px]">{run.strategy_name ?? "—"}</td>
                  <td className={`px-3 py-2 font-mono font-medium ${retColor}`}>{pct(run.total_return)}</td>
                  <td className={`px-3 py-2 font-mono ${(run.alpha ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{pct(run.alpha)}</td>
                  <td className="px-3 py-2 font-mono text-cyan-300">{dec(run.sharpe_ratio, 2)}</td>
                  <td className={`px-3 py-2 font-mono ${ddColor}`}>{pct(run.max_drawdown)}</td>
                  <td className="px-3 py-2 font-mono text-slate-300">{dec(run.win_rate, 1)}%</td>
                  <td className="px-3 py-2 text-slate-400">{run.total_trades ?? "—"}</td>
                  <td className="px-3 py-2 text-slate-500 whitespace-nowrap">{fmtDate(run.created_at)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
