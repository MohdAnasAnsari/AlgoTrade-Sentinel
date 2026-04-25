"use client";
import React, { useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { EquityPoint } from "@/lib/api";

interface Props {
  data:   EquityPoint[];
  ticker: string;
}

function fmtK(v: number) {
  return v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v.toFixed(0)}`;
}

const SAMPLE_MAX = 500;

export function EquityCurveChart({ data, ticker }: Props) {
  // Downsample for render performance
  const chartData = useMemo(() => {
    if (data.length <= SAMPLE_MAX) return data;
    const step = Math.ceil(data.length / SAMPLE_MAX);
    return data.filter((_, i) => i % step === 0 || i === data.length - 1);
  }, [data]);

  if (data.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 flex items-center justify-center h-48 text-slate-500 text-sm">
        No equity curve data
      </div>
    );
  }

  const minY = Math.min(...chartData.map((d) => Math.min(d.value, d.benchmark ?? Infinity))) * 0.97;
  const maxY = Math.max(...chartData.map((d) => Math.max(d.value, d.benchmark ?? 0)))         * 1.03;

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-slate-200 mb-4">Equity Curve — {ticker}</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData} margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#94a3b8", fontSize: 10 }}
            tickFormatter={(d) => d.slice(0, 7)}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[minY, maxY]}
            tick={{ fill: "#94a3b8", fontSize: 10 }}
            tickFormatter={fmtK}
            width={52}
          />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #475569", borderRadius: 8 }}
            labelStyle={{ color: "#e2e8f0", fontSize: 11 }}
            formatter={(value: number, name: string) => [
              `$${value.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`,
              name,
            ]}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
          <Line
            type="monotone"
            dataKey="value"
            name={`${ticker} Strategy`}
            stroke="#06b6d4"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="benchmark"
            name="SPY Benchmark"
            stroke="#f59e0b"
            strokeWidth={1.5}
            strokeDasharray="5 3"
            dot={false}
            activeDot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
