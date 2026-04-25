"use client";

import { useState } from "react";
import type { FeatureStatsResponse } from "@/lib/api";
import { FEATURE_GROUPS, GROUP_COLORS, GROUP_LABELS, featureLabel } from "@/lib/features";
import type { FeatureGroup } from "@/lib/features";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface FeatureStatsPanelProps {
  stats:     FeatureStatsResponse | null;
  isLoading: boolean;
}

function fmt(n: number | null | undefined, dec = 4): string {
  if (n == null) return "—";
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000)     return `${(n / 1_000).toFixed(2)}K`;
  return n.toFixed(dec);
}

function NullBadge({ pct }: { pct: number | null | undefined }) {
  if (pct == null) return null;
  const color =
    pct > 50 ? "text-rose-400" :
    pct > 20 ? "text-amber-400" :
    "text-slate-500";
  return <span className={cn("text-[10px] font-mono", color)}>{pct.toFixed(1)}%</span>;
}

export function FeatureStatsPanel({ stats, isLoading }: FeatureStatsPanelProps) {
  const [activeGroup, setActiveGroup] = useState<FeatureGroup>("trend");

  const groups = Object.keys(FEATURE_GROUPS) as FeatureGroup[];
  const features = FEATURE_GROUPS[activeGroup] as readonly string[];

  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader className="pb-0">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <CardTitle className="text-sm font-semibold text-slate-100">
            Feature Statistics
            {stats && (
              <span className="ml-2 text-xs font-normal text-slate-500">
                {stats.ticker} · {stats.total_rows.toLocaleString()} rows
              </span>
            )}
          </CardTitle>

          {/* Group tabs */}
          <div className="flex gap-1">
            {groups.map((g) => (
              <button
                key={g}
                onClick={() => setActiveGroup(g)}
                className={cn(
                  "px-3 py-1 rounded-md text-xs font-semibold transition-all",
                  activeGroup === g
                    ? "text-slate-950"
                    : "text-slate-400 hover:text-slate-200"
                )}
                style={
                  activeGroup === g
                    ? { backgroundColor: GROUP_COLORS[g] }
                    : undefined
                }
              >
                {GROUP_LABELS[g]}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-3">
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full bg-slate-800 rounded-lg" />
            ))}
          </div>
        ) : !stats || stats.total_rows === 0 ? (
          <div className="flex items-center justify-center h-24 text-slate-500 text-sm">
            No feature data — run the pipeline first
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="px-4 py-2 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Feature
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Mean
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Std Dev
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Min
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Max
                  </th>
                  <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Null %
                  </th>
                </tr>
              </thead>
              <tbody>
                {features.map((feat) => {
                  const s = stats.stats[feat];
                  return (
                    <tr
                      key={feat}
                      className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
                    >
                      <td className="px-4 py-2 font-mono text-xs text-slate-300 whitespace-nowrap">
                        {featureLabel(feat)}
                      </td>
                      <td className="px-4 py-2 text-right text-xs text-slate-300 font-mono">
                        {fmt(s?.mean)}
                      </td>
                      <td className="px-4 py-2 text-right text-xs text-slate-400 font-mono">
                        {fmt(s?.std)}
                      </td>
                      <td className="px-4 py-2 text-right text-xs text-rose-400 font-mono">
                        {fmt(s?.min)}
                      </td>
                      <td className="px-4 py-2 text-right text-xs text-emerald-400 font-mono">
                        {fmt(s?.max)}
                      </td>
                      <td className="px-4 py-2 text-right">
                        <NullBadge pct={s?.null_pct} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
