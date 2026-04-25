"use client";
import React, { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DrawdownPoint } from "@/lib/api";

interface Props {
  data:   DrawdownPoint[];
  ticker: string;
}

const SAMPLE_MAX = 500;

export function DrawdownChart({ data, ticker }: Props) {
  const chartData = useMemo(() => {
    if (data.length <= SAMPLE_MAX) return data;
    const step = Math.ceil(data.length / SAMPLE_MAX);
    return data.filter((_, i) => i % step === 0 || i === data.length - 1);
  }, [data]);

  if (data.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 flex items-center justify-center h-48 text-slate-500 text-sm">
        No drawdown data
      </div>
    );
  }

  const minDD = Math.min(...chartData.map((d) => d.drawdown));

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-slate-200 mb-1">
        Drawdown — {ticker}
        <span className="ml-2 text-xs font-normal text-rose-400">
          Max: {minDD.toFixed(2)}%
        </span>
      </h3>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={chartData} margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
          <defs>
            <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#f43f5e" stopOpacity={0.5} />
              <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#94a3b8", fontSize: 10 }}
            tickFormatter={(d) => d.slice(0, 7)}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[minDD * 1.05, 0]}
            tick={{ fill: "#94a3b8", fontSize: 10 }}
            tickFormatter={(v) => `${v.toFixed(1)}%`}
            width={52}
          />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #475569", borderRadius: 8 }}
            labelStyle={{ color: "#e2e8f0", fontSize: 11 }}
            formatter={(value: number) => [`${value.toFixed(2)}%`, "Drawdown"]}
          />
          <ReferenceLine y={0} stroke="#475569" />
          <Area
            type="monotone"
            dataKey="drawdown"
            stroke="#f43f5e"
            strokeWidth={1.5}
            fill="url(#ddGrad)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
