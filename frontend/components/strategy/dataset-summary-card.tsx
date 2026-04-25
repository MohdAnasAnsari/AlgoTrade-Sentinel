"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { DatasetVersion } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface DatasetSummaryCardProps {
  summary:    DatasetVersion | null;
  isLoading?: boolean;
}

const PIE_COLORS = {
  BUY:  "#10b981",
  SELL: "#f43f5e",
  HOLD: "#64748b",
};

function fmt(n: number | null | undefined): string {
  if (n == null) return "—";
  return n.toLocaleString();
}

export function DatasetSummaryCard({ summary, isLoading }: DatasetSummaryCardProps) {
  if (isLoading) {
    return (
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-32 bg-slate-800" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-48 w-full bg-slate-800 rounded-lg" />
        </CardContent>
      </Card>
    );
  }

  if (!summary) {
    return (
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-slate-100">
            Dataset Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 text-slate-500 text-sm">
            No dataset built yet
          </div>
        </CardContent>
      </Card>
    );
  }

  const dist = summary.label_distribution ?? {};
  const total = (dist.BUY ?? 0) + (dist.SELL ?? 0) + (dist.HOLD ?? 0);
  const pieData = [
    { name: "BUY",  value: dist.BUY  ?? 0 },
    { name: "SELL", value: dist.SELL ?? 0 },
    { name: "HOLD", value: dist.HOLD ?? 0 },
  ].filter((d) => d.value > 0);

  const trainPct = summary.n_rows && summary.n_train
    ? Math.round((summary.n_train / summary.n_rows) * 100)
    : null;

  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-slate-100 flex items-center gap-2">
          <span className="font-mono text-cyan-400">v{summary.version}</span>
          <span className="text-slate-500 font-normal">· Dataset Summary</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="grid grid-cols-2 gap-4">
          {/* Pie chart */}
          <div>
            <ResponsiveContainer width="100%" height={140}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={55}
                  innerRadius={30}
                  strokeWidth={0}
                >
                  {pieData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={PIE_COLORS[entry.name as keyof typeof PIE_COLORS]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #1e293b",
                    borderRadius: "8px",
                    color: "#e2e8f0",
                    fontSize: "12px",
                  }}
                  formatter={(val: number) => [
                    `${val.toLocaleString()} (${total ? Math.round((val / total) * 100) : 0}%)`,
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>

            {/* Legend */}
            <div className="flex justify-center gap-3 mt-1">
              {(["BUY", "SELL", "HOLD"] as const).map((lbl) => (
                <div key={lbl} className="flex items-center gap-1">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: PIE_COLORS[lbl] }}
                  />
                  <span className="text-[10px] text-slate-400">{lbl}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Stats */}
          <div className="flex flex-col gap-2 justify-center">
            <Stat label="Total rows"   value={fmt(summary.n_rows)} />
            <Stat label="Train"        value={`${fmt(summary.n_train)}${trainPct != null ? ` (${trainPct}%)` : ""}`} />
            <Stat label="Test"         value={fmt(summary.n_test)} />
            <Stat label="Tickers"      value={summary.tickers?.length?.toString() ?? "—"} />
            <Stat label="Date range"   value={summary.date_range_start && summary.date_range_end
              ? `${summary.date_range_start} → ${summary.date_range_end}` : "—"} />
            <Stat label="Split"        value={summary.split_date ?? "—"} />
            <Stat label="Features"     value={summary.feature_list?.length?.toString() ?? "—"} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-xs font-mono text-slate-300">{value}</span>
    </div>
  );
}
