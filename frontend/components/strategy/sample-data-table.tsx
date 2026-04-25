"use client";

import { useState } from "react";
import type { FeatureListResponse } from "@/lib/api";
import { FEATURE_GROUPS, featureLabel } from "@/lib/features";
import type { FeatureGroup } from "@/lib/features";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface SampleDataTableProps {
  data:       FeatureListResponse | null;
  isLoading:  boolean;
  activeGroup: FeatureGroup;
}

function fmtCell(val: unknown): string {
  if (val == null) return "—";
  const n = Number(val);
  if (isNaN(n)) return String(val);
  const abs = Math.abs(n);
  if (abs >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000)     return `${(n / 1_000_000).toFixed(2)}M`;
  if (abs >= 10_000)        return n.toFixed(0);
  return n.toFixed(3);
}

export function SampleDataTable({ data, isLoading, activeGroup }: SampleDataTableProps) {
  const features   = FEATURE_GROUPS[activeGroup] as readonly string[];
  const visibleCols = ["date", "close", ...features];

  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold text-slate-100">
            Sample Data
            <span className="ml-2 text-xs font-normal text-slate-500">
              last {data?.count ?? 0} rows · showing{" "}
              {activeGroup.replace("_", " ")} features
            </span>
          </CardTitle>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full bg-slate-800 rounded-lg" />
            ))}
          </div>
        ) : !data || data.rows.length === 0 ? (
          <div className="flex items-center justify-center h-24 text-slate-500 text-sm">
            No feature data — run the pipeline first
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-800">
                  {visibleCols.map((col) => (
                    <th
                      key={col}
                      className="px-3 py-2.5 text-left font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap"
                    >
                      {col === "date" ? "Date"
                       : col === "close" ? "Close"
                       : featureLabel(col)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[...data.rows].reverse().map((row, i) => (
                  <tr
                    key={i}
                    className="border-b border-slate-800/40 hover:bg-slate-800/30 transition-colors"
                  >
                    {visibleCols.map((col) => {
                      const val = (row as unknown as Record<string, unknown>)[col];
                      const isDate  = col === "date";
                      const isClose = col === "close";
                      return (
                        <td
                          key={col}
                          className={cn(
                            "px-3 py-2 whitespace-nowrap font-mono",
                            isDate  ? "text-slate-400"   : "",
                            isClose ? "text-slate-200 font-semibold" : "text-slate-400",
                          )}
                        >
                          {isClose && val != null ? `$${fmtCell(val)}` : fmtCell(val)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
