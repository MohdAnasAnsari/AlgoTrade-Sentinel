"use client";
import React from "react";
import { BacktestSummary } from "@/lib/api";

interface Props {
  summary: BacktestSummary;
}

interface MetricCardProps {
  label:    string;
  value:    string;
  sub?:     string;
  positive?: boolean | null;
}

function MetricCard({ label, value, sub, positive }: MetricCardProps) {
  const valueColor =
    positive === true  ? "text-emerald-400" :
    positive === false ? "text-rose-400"    :
    "text-cyan-300";

  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-4">
      <p className="text-xs text-slate-500 mb-1.5">{label}</p>
      <p className={`text-xl font-bold font-mono ${valueColor}`}>{value}</p>
      {sub && <p className="text-xs text-slate-600 mt-1">{sub}</p>}
    </div>
  );
}

function pct(v: number | null, showSign = true) {
  if (v == null) return "—";
  const sign = showSign && v >= 0 ? "+" : "";
  return `${sign}${v.toFixed(2)}%`;
}
function dec(v: number | null, d = 2) {
  return v == null ? "—" : v.toFixed(d);
}

export function MetricsGrid({ summary: s }: Props) {
  return (
    <div className="grid grid-cols-3 gap-3">
      <MetricCard
        label="Total Return"
        value={pct(s.total_return)}
        sub={`Ann. ${pct(s.annualized_return)}`}
        positive={s.total_return == null ? null : s.total_return >= 0}
      />
      <MetricCard
        label="Alpha vs Benchmark"
        value={pct(s.alpha)}
        sub={`Bench ${pct(s.benchmark_return)}`}
        positive={s.alpha == null ? null : s.alpha >= 0}
      />
      <MetricCard
        label="Sharpe Ratio"
        value={dec(s.sharpe_ratio)}
        sub="annualized, RF=4%"
        positive={s.sharpe_ratio == null ? null : s.sharpe_ratio >= 1}
      />
      <MetricCard
        label="Sortino Ratio"
        value={dec(s.sortino_ratio)}
        positive={s.sortino_ratio == null ? null : s.sortino_ratio >= 1}
      />
      <MetricCard
        label="Max Drawdown"
        value={pct(s.max_drawdown, false)}
        sub={`Calmar ${dec(s.calmar_ratio)}`}
        positive={false}
      />
      <MetricCard
        label="Daily Volatility"
        value={pct(s.daily_volatility, false)}
        sub="annualized"
        positive={null}
      />
      <MetricCard
        label="Win Rate"
        value={`${dec(s.win_rate, 1)}%`}
        sub={`${s.total_trades ?? 0} trades`}
        positive={s.win_rate == null ? null : s.win_rate >= 50}
      />
      <MetricCard
        label="Profit Factor"
        value={dec(s.profit_factor)}
        sub={`Avg hold ${dec(s.avg_holding_days, 1)}d`}
        positive={s.profit_factor == null ? null : s.profit_factor >= 1}
      />
      <MetricCard
        label="Avg Win / Loss"
        value={`${pct(s.avg_win)} / ${pct(s.avg_loss)}`}
        positive={null}
      />
    </div>
  );
}
