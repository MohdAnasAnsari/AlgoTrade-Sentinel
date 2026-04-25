import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import type { TickerStats } from "@/lib/api";

interface StatsBarProps {
  ticker: string;
  stats: TickerStats | null;
  isLoading?: boolean;
}

function fmt(n: number | null | undefined, decimals = 2, prefix = ""): string {
  if (n == null) return "—";
  return `${prefix}${n.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
}

function fmtVol(n: number | null | undefined): string {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

export function StatsBar({ ticker, stats, isLoading }: StatsBarProps) {
  const items = [
    { label: "Current Price", value: fmt(stats?.current_price, 2, "$") },
    {
      label: "YTD Return",
      value: stats?.ytd_return != null ? `${stats.ytd_return >= 0 ? "+" : ""}${stats.ytd_return.toFixed(2)}%` : "—",
      trend: stats?.ytd_return != null ? (stats.ytd_return >= 0 ? "up" : "down") : null,
    },
    { label: "52W High", value: fmt(stats?.week52_high, 2, "$") },
    { label: "52W Low", value: fmt(stats?.week52_low, 2, "$") },
    { label: "Avg Volume", value: fmtVol(stats?.avg_volume) },
    {
      label: "Data Range",
      value:
        stats?.data_from && stats?.data_to
          ? `${stats.data_from} → ${stats.data_to}`
          : "—",
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {items.map((item) => (
        <div
          key={item.label}
          className="flex flex-col gap-0.5 rounded-xl bg-slate-900 border border-slate-800 px-4 py-3"
        >
          <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">
            {item.label}
          </span>
          <div className="flex items-center gap-1">
            {item.trend === "up" && (
              <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            )}
            {item.trend === "down" && (
              <ArrowDownRight className="w-3.5 h-3.5 text-rose-400 shrink-0" />
            )}
            <span
              className={`text-sm font-bold truncate ${
                item.trend === "up"
                  ? "text-emerald-400"
                  : item.trend === "down"
                  ? "text-rose-400"
                  : "text-slate-100"
              }`}
            >
              {isLoading ? (
                <span className="inline-block w-16 h-3.5 rounded bg-slate-800 animate-pulse" />
              ) : (
                item.value
              )}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
