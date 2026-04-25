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
import { ExperimentRun } from "@/lib/api";

interface Props {
  runs: ExperimentRun[];
  selectedRunId: string | null;
}

const METRIC_KEYS = ["f1_macro", "accuracy", "roc_auc"] as const;
const METRIC_COLORS: Record<string, string> = {
  f1_macro: "#06b6d4",
  accuracy: "#8b5cf6",
  roc_auc:  "#f59e0b",
};
const METRIC_LABELS: Record<string, string> = {
  f1_macro: "F1",
  accuracy: "Acc",
  roc_auc:  "AUC",
};

export function ModelComparisonChart({ runs, selectedRunId }: Props) {
  const finished = runs
    .filter((r) => r.f1_macro != null && r.status === "FINISHED")
    .slice(0, 12);

  if (finished.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 text-center text-slate-500 text-sm h-48 flex items-center justify-center">
        No finished runs to compare
      </div>
    );
  }

  const data = finished.map((r) => ({
    name:     r.model_name.replace("Classifier", "").replace("Regression", " Reg"),
    run_id:   r.run_id,
    f1_macro: r.f1_macro ?? 0,
    accuracy: r.accuracy ?? 0,
    roc_auc:  r.roc_auc ?? 0,
  }));

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-slate-200 mb-4">Model Comparison</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
          <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
          <YAxis domain={[0, 1]} tick={{ fill: "#94a3b8", fontSize: 11 }} tickFormatter={(v) => v.toFixed(2)} />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #475569", borderRadius: 8 }}
            labelStyle={{ color: "#e2e8f0", fontSize: 12 }}
            formatter={(value: number, name: string) => [value.toFixed(4), METRIC_LABELS[name] ?? name]}
          />
          {METRIC_KEYS.map((key) => (
            <Bar key={key} dataKey={key} fill={METRIC_COLORS[key]} radius={[3, 3, 0, 0]}>
              {data.map((entry) => (
                <Cell
                  key={entry.run_id}
                  fill={METRIC_COLORS[key]}
                  opacity={!selectedRunId || entry.run_id === selectedRunId ? 1 : 0.35}
                />
              ))}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
      <div className="flex gap-4 justify-center mt-2">
        {METRIC_KEYS.map((k) => (
          <span key={k} className="flex items-center gap-1.5 text-xs text-slate-400">
            <span className="inline-block w-3 h-3 rounded-sm" style={{ background: METRIC_COLORS[k] }} />
            {METRIC_LABELS[k]}
          </span>
        ))}
      </div>
    </div>
  );
}
