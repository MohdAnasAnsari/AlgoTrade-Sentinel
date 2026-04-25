"use client";
import React from "react";
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
import { FeatureImportances } from "@/lib/api";

interface Props {
  data: FeatureImportances | null;
}

const BAR_COLOR = "#06b6d4";
const TOP_N = 20;

export function FeatureImportanceChart({ data }: Props) {
  if (!data || data.importances.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 text-center text-slate-500 text-sm h-48 flex items-center justify-center">
        No feature importance data for this run
      </div>
    );
  }

  const items = data.importances.slice(0, TOP_N).reverse();
  const chartData = items.map((it) => ({
    feature: it.feature.replace(/_/g, " "),
    score:   it.score,
    raw:     it.feature,
  }));

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-slate-200 mb-4">
        Feature Importance — {data.model_name}
        <span className="ml-2 text-xs font-normal text-slate-500">(top {Math.min(TOP_N, data.importances.length)})</span>
      </h3>
      <ResponsiveContainer width="100%" height={Math.max(280, chartData.length * 20)}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 0, right: 16, left: 100, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, "auto"]}
            tick={{ fill: "#94a3b8", fontSize: 10 }}
            tickFormatter={(v) => v.toFixed(3)}
          />
          <YAxis
            type="category"
            dataKey="feature"
            tick={{ fill: "#cbd5e1", fontSize: 11 }}
            width={96}
          />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #475569", borderRadius: 8 }}
            formatter={(value: number) => [value.toFixed(6), "Importance"]}
            labelStyle={{ color: "#e2e8f0", fontSize: 12 }}
          />
          <Bar dataKey="score" radius={[0, 3, 3, 0]}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={BAR_COLOR} fillOpacity={0.7 + (i / chartData.length) * 0.3} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
