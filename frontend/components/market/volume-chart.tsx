"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { OHLCVRow } from "@/lib/api";

interface VolumeChartProps {
  data: OHLCVRow[];
}

function fmtVol(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

export function VolumeChart({ data }: VolumeChartProps) {
  if (data.length === 0) return null;

  // Sample dates for X-axis labels (avoid crowding)
  const step = Math.max(1, Math.floor(data.length / 8));

  return (
    <div>
      <p className="text-xs text-slate-500 font-medium mb-2 px-1">Volume</p>
      <ResponsiveContainer width="100%" height={100}>
        <BarChart
          data={data}
          margin={{ top: 0, right: 0, left: -10, bottom: 0 }}
          barCategoryGap="10%"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: "#64748b", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            interval={step - 1}
            tickFormatter={(v: string) => v.slice(5)} // MM-DD
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={fmtVol}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "8px",
              color: "#e2e8f0",
              fontSize: "12px",
            }}
            formatter={(val: number) => [fmtVol(val), "Volume"]}
            labelFormatter={(label: string) => label}
          />
          <Bar dataKey="volume" maxBarSize={8} radius={[2, 2, 0, 0]}>
            {data.map((d, i) => (
              <Cell
                key={i}
                fill={
                  (d.close ?? 0) >= (d.open ?? 0) ? "#10b98166" : "#f43f5e66"
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
