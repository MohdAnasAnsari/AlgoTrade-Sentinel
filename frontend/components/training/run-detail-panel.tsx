"use client";
import React from "react";
import { RunDetails } from "@/lib/api";

interface Props {
  details: RunDetails | null;
  loading: boolean;
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-800 rounded-lg p-3 text-center">
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <p className="text-lg font-semibold font-mono text-cyan-300">{value}</p>
    </div>
  );
}

function fmt(v: number | undefined | null) {
  return v == null ? "—" : v.toFixed(4);
}

export function RunDetailPanel({ details, loading }: Props) {
  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 flex items-center justify-center h-48">
        <svg className="animate-spin h-6 w-6 text-cyan-400" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
        </svg>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 text-center text-slate-500 text-sm">
        Select a run from the table to see details
      </div>
    );
  }

  const m = details.metrics;
  const cm = details.confusion_matrix;
  const report = details.classification_report;
  const labels = cm?.labels ?? ["BUY", "HOLD", "SELL"];

  // colour scale for confusion matrix cell
  function cellOpacity(val: number): string {
    if (!cm) return "bg-slate-700";
    const max = Math.max(...cm.matrix.flat(), 1);
    const pct = val / max;
    if (pct > 0.7) return "bg-cyan-700";
    if (pct > 0.4) return "bg-cyan-900";
    if (pct > 0.1) return "bg-slate-700";
    return "bg-slate-800";
  }

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 space-y-5">
      {/* Header */}
      <div>
        <h3 className="text-sm font-semibold text-slate-200">{details.model_name}</h3>
        <p className="text-xs text-slate-500 font-mono truncate">{details.run_id}</p>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-4 gap-3">
        <MetricCard label="F1 Macro"  value={fmt(m.f1_macro)} />
        <MetricCard label="Accuracy"  value={fmt(m.accuracy)} />
        <MetricCard label="Precision" value={fmt(m.precision_macro)} />
        <MetricCard label="AUC"       value={fmt(m.roc_auc)} />
      </div>

      {/* Confusion matrix */}
      {cm && (
        <div>
          <h4 className="text-xs font-medium text-slate-400 mb-2">Confusion Matrix</h4>
          <div className="overflow-x-auto">
            <table className="text-xs border-separate border-spacing-0.5">
              <thead>
                <tr>
                  <th className="w-16 text-right pr-2 text-slate-500 font-normal">True ↓ / Pred →</th>
                  {labels.map((l) => (
                    <th key={l} className="w-16 text-center text-slate-300 font-medium">{l}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {cm.matrix.map((row, i) => (
                  <tr key={labels[i]}>
                    <td className="text-right pr-2 text-slate-300 font-medium">{labels[i]}</td>
                    {row.map((val, j) => (
                      <td key={j} className={`text-center py-2 px-3 rounded font-mono font-semibold text-slate-100 ${cellOpacity(val)}`}>
                        {val}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Classification report */}
      {report && Object.keys(report).length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-slate-400 mb-2">Classification Report</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="pb-1 text-left text-slate-500 font-normal">Class</th>
                  <th className="pb-1 text-right text-slate-500 font-normal">Precision</th>
                  <th className="pb-1 text-right text-slate-500 font-normal">Recall</th>
                  <th className="pb-1 text-right text-slate-500 font-normal">F1</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(report).map(([cls, metrics]) => (
                  <tr key={cls} className="border-b border-slate-800/50">
                    <td className="py-1.5 text-slate-300 font-medium">{cls}</td>
                    <td className="py-1.5 text-right font-mono text-slate-300">
                      {typeof metrics["precision"] === "number" ? metrics["precision"].toFixed(4) : "—"}
                    </td>
                    <td className="py-1.5 text-right font-mono text-slate-300">
                      {typeof metrics["recall"] === "number" ? metrics["recall"].toFixed(4) : "—"}
                    </td>
                    <td className="py-1.5 text-right font-mono text-cyan-300">
                      {typeof metrics["f1-score"] === "number" ? metrics["f1-score"].toFixed(4) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
