"use client";
import React, { useState } from "react";
import { BacktestTrade } from "@/lib/api";

type SortKey = "entry_date" | "exit_date" | "pnl" | "return_pct" | "holding_days";

interface Props {
  trades: BacktestTrade[];
}

export function TradesLogTable({ trades }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("entry_date");
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = [...trades].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
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

  if (trades.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 text-center text-slate-500 text-sm">
        No trades executed in this backtest
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-700 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">Trades Log</h3>
        <span className="text-xs text-slate-500">{trades.length} trade{trades.length !== 1 ? "s" : ""}</span>
      </div>
      <div className="overflow-x-auto max-h-72 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-800/60 border-b border-slate-700 sticky top-0">
            <tr>
              <Th col="entry_date"  label="Entry Date" />
              <Th col="exit_date"   label="Exit Date" />
              <th className="px-3 py-2 text-left text-xs font-medium text-slate-400">Entry $</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-slate-400">Exit $</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-slate-400">Shares</th>
              <Th col="pnl"         label="P&L $" />
              <Th col="return_pct"  label="Return %" />
              <Th col="holding_days" label="Days" />
            </tr>
          </thead>
          <tbody>
            {sorted.map((t, i) => {
              const isWin = t.pnl > 0;
              return (
                <tr key={i} className="border-b border-slate-800/70 hover:bg-slate-800/30">
                  <td className="px-3 py-2 text-slate-400">{t.entry_date}</td>
                  <td className="px-3 py-2 text-slate-400">{t.exit_date}</td>
                  <td className="px-3 py-2 font-mono text-slate-300">${t.entry_price.toFixed(2)}</td>
                  <td className="px-3 py-2 font-mono text-slate-300">${t.exit_price.toFixed(2)}</td>
                  <td className="px-3 py-2 font-mono text-slate-400">{t.shares.toFixed(2)}</td>
                  <td className={`px-3 py-2 font-mono font-medium ${isWin ? "text-emerald-400" : "text-rose-400"}`}>
                    {isWin ? "+" : ""}${t.pnl.toFixed(2)}
                  </td>
                  <td className={`px-3 py-2 font-mono ${isWin ? "text-emerald-400" : "text-rose-400"}`}>
                    {isWin ? "+" : ""}{t.return_pct.toFixed(2)}%
                  </td>
                  <td className="px-3 py-2 text-slate-400">{t.holding_days}d</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
