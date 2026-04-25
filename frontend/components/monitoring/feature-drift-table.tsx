"use client";

import { useMemo, useState } from "react";
import { ArrowDownUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { FeatureDriftDetail } from "@/lib/api";

type SortKey = "feature" | "drift_detected" | "drift_score" | "p_value";

interface Props {
  rows: FeatureDriftDetail[];
}

export function FeatureDriftTable({ rows }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("drift_score");
  const [sortDesc, setSortDesc] = useState(true);

  const sortedRows = useMemo(() => {
    const next = [...rows];
    next.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const direction = sortDesc ? -1 : 1;

      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "string" && typeof bv === "string") {
        return av.localeCompare(bv) * direction;
      }
      if (typeof av === "boolean" && typeof bv === "boolean") {
        return (Number(av) - Number(bv)) * direction;
      }
      return (Number(av) - Number(bv)) * direction;
    });
    return next;
  }, [rows, sortDesc, sortKey]);

  if (rows.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-8 text-center text-sm text-slate-500">
        No feature drift scores available yet.
      </div>
    );
  }

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortDesc((prev) => !prev);
    else {
      setSortKey(key);
      setSortDesc(key !== "feature");
    }
  }

  const headerClass =
    "px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500";

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] text-sm">
        <thead className="bg-slate-900/90 border-b border-slate-800 sticky top-0">
          <tr>
            {[
              ["feature", "Feature"],
              ["drift_detected", "Status"],
              ["drift_score", "Drift Score"],
              ["p_value", "P-Value"],
            ].map(([key, label]) => (
              <th key={key} className={headerClass}>
                <button
                  type="button"
                  onClick={() => handleSort(key as SortKey)}
                  className="inline-flex items-center gap-2 hover:text-slate-200 transition-colors"
                >
                  {label}
                  <ArrowDownUp className="w-3.5 h-3.5" />
                </button>
              </th>
            ))}
            <th className={headerClass}>Reference Mean</th>
            <th className={headerClass}>Current Mean</th>
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row) => {
            const drifted = row.drift_detected;
            const rowTone = drifted
              ? row.drift_score >= 0.3
                ? "bg-rose-500/6 hover:bg-rose-500/10"
                : "bg-amber-500/6 hover:bg-amber-500/10"
              : "hover:bg-slate-800/40";
            return (
              <tr key={row.feature} className={`border-b border-slate-800/70 transition-colors ${rowTone}`}>
                <td className="px-4 py-3 font-medium text-slate-100">{row.feature}</td>
                <td className="px-4 py-3">
                  <Badge
                    className={
                      drifted
                        ? row.drift_score >= 0.3
                          ? "border border-rose-500/30 bg-rose-500/10 text-rose-300"
                          : "border border-amber-500/30 bg-amber-500/10 text-amber-300"
                        : "border border-emerald-500/25 bg-emerald-500/10 text-emerald-300"
                    }
                  >
                    {drifted ? "Drifted" : "Stable"}
                  </Badge>
                </td>
                <td className="px-4 py-3 font-mono text-slate-200">{row.drift_score.toFixed(4)}</td>
                <td className="px-4 py-3 font-mono text-slate-400">
                  {row.p_value == null ? "—" : row.p_value.toFixed(4)}
                </td>
                <td className="px-4 py-3 font-mono text-slate-400">
                  {row.reference_mean == null ? "—" : row.reference_mean.toFixed(3)}
                </td>
                <td className="px-4 py-3 font-mono text-slate-300">
                  {row.current_mean == null ? "—" : row.current_mean.toFixed(3)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
