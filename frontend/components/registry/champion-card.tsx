"use client";
import React from "react";
import { ModelVersionInfo } from "@/lib/api";

interface Props {
  champion: ModelVersionInfo | null;
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <div className="text-lg font-bold text-white font-mono">{value}</div>
      <div className="text-xs text-slate-400 mt-0.5">{label}</div>
    </div>
  );
}

export function ChampionCard({ champion: c }: Props) {
  if (!c) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 text-center text-slate-500 text-sm">
        No Production model — promote a challenger to get started
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-cyan-500/30 bg-gradient-to-br from-slate-900 via-slate-800 to-cyan-950 p-6">
      <div className="flex items-start justify-between mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              CHAMPION
            </span>
            <span className="text-xs text-slate-400">v{c.version}</span>
          </div>
          <h2 className="text-lg font-bold text-slate-100">{c.model_name ?? "signal-predictor"}</h2>
          {c.run_id && (
            <p className="text-xs text-slate-500 mt-0.5 font-mono truncate max-w-xs">{c.run_id}</p>
          )}
        </div>
        <span className="text-xs px-2 py-1 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
          Production
        </span>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <Stat label="F1 Macro"  value={c.f1_macro  != null ? c.f1_macro.toFixed(4)  : "—"} />
        <Stat label="Accuracy"  value={c.accuracy   != null ? (c.accuracy * 100).toFixed(1) + "%" : "—"} />
        <Stat label="ROC-AUC"   value={c.roc_auc    != null ? c.roc_auc.toFixed(4)   : "—"} />
      </div>
    </div>
  );
}
