"use client";
import React from "react";
import { ModelVersionInfo } from "@/lib/api";

interface Props {
  challengers:   ModelVersionInfo[];
  championF1:    number | null;
  onPromote:     (v: ModelVersionInfo) => void;
}

export function ChallengerTable({ challengers, championF1, onPromote }: Props) {
  if (!challengers.length) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 text-center text-slate-500 text-sm">
        No challengers in Staging — run a training job to add models
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-slate-200">Challengers (Staging)</h3>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-slate-800/50">
          <tr>
            <th className="px-5 py-2 text-left text-xs font-medium text-slate-400">Version</th>
            <th className="px-5 py-2 text-left text-xs font-medium text-slate-400">Model</th>
            <th className="px-5 py-2 text-right text-xs font-medium text-slate-400">F1 Macro</th>
            <th className="px-5 py-2 text-right text-xs font-medium text-slate-400">Accuracy</th>
            <th className="px-5 py-2 text-right text-xs font-medium text-slate-400">ROC-AUC</th>
            <th className="px-5 py-2 text-center text-xs font-medium text-slate-400">Edge</th>
            <th className="px-5 py-2 text-center text-xs font-medium text-slate-400">Action</th>
          </tr>
        </thead>
        <tbody>
          {challengers.map((c) => {
            const f1   = c.f1_macro ?? 0;
            const edge = championF1 != null ? f1 - championF1 : null;
            return (
              <tr key={c.version} className="border-t border-slate-800/60">
                <td className="px-5 py-2.5 text-slate-300 font-mono text-xs">v{c.version}</td>
                <td className="px-5 py-2.5 text-slate-400 text-xs">{c.model_name ?? "—"}</td>
                <td className="px-5 py-2.5 text-right font-mono text-slate-100">
                  {c.f1_macro?.toFixed(4) ?? "—"}
                </td>
                <td className="px-5 py-2.5 text-right font-mono text-slate-400">
                  {c.accuracy != null ? (c.accuracy * 100).toFixed(1) + "%" : "—"}
                </td>
                <td className="px-5 py-2.5 text-right font-mono text-slate-400">
                  {c.roc_auc?.toFixed(4) ?? "—"}
                </td>
                <td className="px-5 py-2.5 text-center">
                  {edge != null ? (
                    <span className={`text-xs font-mono ${edge > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {edge > 0 ? "+" : ""}{edge.toFixed(4)}
                    </span>
                  ) : (
                    <span className="text-slate-600">—</span>
                  )}
                </td>
                <td className="px-5 py-2.5 text-center">
                  <button
                    onClick={() => onPromote(c)}
                    className="text-xs px-2.5 py-1 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/20 transition-colors"
                  >
                    Promote
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
