"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { LabelDistribution } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface LabelDistributionChartProps {
  distributions: LabelDistribution[];
  isLoading:     boolean;
}

const LABEL_COLORS = {
  BUY:  "#10b981",
  SELL: "#f43f5e",
  HOLD: "#64748b",
};

export function LabelDistributionChart({
  distributions,
  isLoading,
}: LabelDistributionChartProps) {
  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-slate-100">
          Label Distribution
          <span className="ml-2 text-xs font-normal text-slate-500">
            BUY / SELL / HOLD per ticker
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {isLoading ? (
          <Skeleton className="h-48 w-full bg-slate-800 rounded-lg" />
        ) : distributions.length === 0 ? (
          <div className="flex items-center justify-center h-48 text-slate-500 text-sm">
            No label data — run the pipeline first
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={distributions}
              margin={{ top: 4, right: 8, left: -10, bottom: 0 }}
              barGap={2}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis
                dataKey="ticker"
                tick={{ fill: "#64748b", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "#64748b", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v: number) => (v >= 1000 ? `${(v / 1000).toFixed(0)}K` : String(v))}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  border: "1px solid #1e293b",
                  borderRadius: "8px",
                  color: "#e2e8f0",
                  fontSize: "12px",
                }}
                cursor={{ fill: "rgba(255,255,255,0.04)" }}
              />
              <Legend
                wrapperStyle={{ fontSize: "11px", color: "#64748b", paddingTop: "8px" }}
              />
              <Bar dataKey="BUY"  fill={LABEL_COLORS.BUY}  radius={[2, 2, 0, 0]} maxBarSize={28} />
              <Bar dataKey="SELL" fill={LABEL_COLORS.SELL} radius={[2, 2, 0, 0]} maxBarSize={28} />
              <Bar dataKey="HOLD" fill={LABEL_COLORS.HOLD} radius={[2, 2, 0, 0]} maxBarSize={28} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
