"use client";
import React, { useState } from "react";
import { ExperimentRun } from "@/lib/api";

type SortKey = "start_time" | "model_name" | "f1_macro" | "accuracy" | "roc_auc";

interface Props {
  runs: ExperimentRun[];
  selectedRunId: string | null;
  onSelect: (run: ExperimentRun) => void;
}

function fmt(v: number | null, decimals = 4) {
  return v == null ? "—" : v.toFixed(decimals);
}

function fmtDate(s: string | null) {
  if (!s) return "—";
  return new Date(s).toLocaleString("en-GB", { dateStyle: "short", timeStyle: "short" });
}

const STATUS_DOT: Record<string, string> = {
  FINISHED: "bg-emerald-500",
  RUNNING:  "bg-cyan-400 animate-pulse",
  FAILED:   "bg-rose-500",
};

export function ExperimentsTable({ runs, selectedRunId, onSelect }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("start_time");
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = [...runs].sort((a, b) => {
    let av: number | string | null = a[sortKey] ?? null;
    let bv: number | string | null = b[sortKey] ?? null;
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    const dir = sortAsc ? 1 : -1;
    return av < bv ? -dir : av > bv ? dir : 0;
  });

  function handleSort(key: SortKey) {
    if (key === sortKey) setSortAsc((p) => !p);
    else { setSortKey(key); setSortAsc(false); }
  }

  const Th = ({ col, label }: { col: SortKey; label: string }) => (
    <th
      onClick={() => handleSort(col)}
      className="px-3 py-2 text-left text-xs font-medium text-slate-400 cursor-pointer hover:text-slate-200 select-none whitespace-nowrap"
    >
      {label} {sortKey === col ? (sortAsc ? "↑" : "↓") : ""}
    </th>
  );

  if (runs.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 text-center text-slate-500 text-sm">
        No experiments yet. Start a training run above.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-800/60 border-b border-slate-700">
            <tr>
              <th className="px-3 py-2 w-4"></th>
              <Th col="model_name"  label="Model" />
              <Th col="f1_macro"    label="F1" />
              <Th col="accuracy"    label="Acc" />
              <Th col="roc_auc"     label="AUC" />
              <Th col="start_time"  label="Started" />
              <th className="px-3 py-2 text-left text-xs font-medium text-slate-400">Status</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((run) => {
              const selected = run.run_id === selectedRunId;
              return (
                <tr
                  key={run.run_id}
                  onClick={() => onSelect(run)}
                  className={`border-b border-slate-800 cursor-pointer transition-colors ${
                    selected
                      ? "bg-cyan-900/30 border-l-2 border-l-cyan-500"
                      : "hover:bg-slate-800/40"
                  }`}
                >
                  <td className="px-3 py-2">
                    <span className={`inline-block w-2 h-2 rounded-full ${STATUS_DOT[run.status] ?? "bg-slate-500"}`} />
                  </td>
                  <td className="px-3 py-2 text-slate-200 font-medium whitespace-nowrap">{run.model_name || "—"}</td>
                  <td className="px-3 py-2 font-mono text-cyan-300">{fmt(run.f1_macro)}</td>
                  <td className="px-3 py-2 font-mono text-slate-300">{fmt(run.accuracy)}</td>
                  <td className="px-3 py-2 font-mono text-slate-300">{fmt(run.roc_auc)}</td>
                  <td className="px-3 py-2 text-slate-400 whitespace-nowrap">{fmtDate(run.start_time)}</td>
                  <td className="px-3 py-2 text-slate-400 text-xs">{run.status}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
