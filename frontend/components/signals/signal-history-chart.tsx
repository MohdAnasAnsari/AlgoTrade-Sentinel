"use client";
import React, { useMemo } from "react";
import {
  ComposedChart,
  Line,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { SignalHistoryPoint } from "@/lib/api";

interface Props {
  ticker: string;
  data:   SignalHistoryPoint[];
}

const SIG_COLOR: Record<string, string> = {
  BUY:  "#10b981",
  SELL: "#f43f5e",
  HOLD: "#f59e0b",
};

interface ChartRow {
  date:   string;
  close:  number | null;
  BUY?:   number;
  SELL?:  number;
  HOLD?:  number;
}

export function SignalHistoryChart({ ticker, data }: Props) {
  const chartData = useMemo((): ChartRow[] => {
    return [...data]
      .sort((a, b) => a.signal_date.localeCompare(b.signal_date))
      .map((d) => {
        const row: ChartRow = { date: d.signal_date, close: d.close };
        if (d.close != null) row[d.signal as keyof ChartRow] = d.close as never;
        return row;
      });
  }, [data]);

  if (data.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 flex items-center justify-center h-52 text-slate-500 text-sm">
        No signal history for {ticker}
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-slate-200 mb-4">
        {ticker} — Signal History
      </h3>
      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} />
          <YAxis tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#94a3b8" }}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#64748b"
            strokeWidth={1.5}
            dot={false}
            connectNulls
          />
          {(["BUY", "SELL", "HOLD"] as const).map((sig) => (
            <Scatter
              key={sig}
              dataKey={sig}
              fill={SIG_COLOR[sig]}
              name={sig}
              shape={(props: React.SVGProps<SVGPolygonElement> & { cx?: number; cy?: number }) => {
                const { cx = 0, cy = 0 } = props;
                const size = 6;
                if (sig === "BUY") {
                  return <polygon points={`${cx},${cy - size} ${cx - size},${cy + size} ${cx + size},${cy + size}`} fill={SIG_COLOR.BUY} />;
                }
                if (sig === "SELL") {
                  return <polygon points={`${cx},${cy + size} ${cx - size},${cy - size} ${cx + size},${cy - size}`} fill={SIG_COLOR.SELL} />;
                }
                return <circle cx={cx} cy={cy} r={3} fill={SIG_COLOR.HOLD} />;
              }}
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
      <div className="flex items-center gap-4 mt-2 text-xs text-slate-500 justify-end">
        <span className="flex items-center gap-1"><span className="text-emerald-400">▲</span> BUY</span>
        <span className="flex items-center gap-1"><span className="text-rose-400">▼</span> SELL</span>
        <span className="flex items-center gap-1"><span className="text-amber-400">●</span> HOLD</span>
      </div>
    </div>
  );
}
