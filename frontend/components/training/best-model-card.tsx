"use client";
import React from "react";
import { ExperimentRun, RegisteredModel } from "@/lib/api";

interface Props {
  bestRun: ExperimentRun | null;
  registeredModels: RegisteredModel[];
  onSelect: (run: ExperimentRun) => void;
}

function fmt(v: number | null) {
  return v == null ? "—" : v.toFixed(4);
}

function fmtDate(s: string | null) {
  if (!s) return "—";
  return new Date(s).toLocaleDateString("en-GB", { dateStyle: "medium" });
}

export function BestModelCard({ bestRun, registeredModels, onSelect }: Props) {
  const registered = registeredModels[0] ?? null;

  if (!bestRun && !registered) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 text-center text-slate-500 text-sm">
        No trained models yet
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-cyan-950 to-slate-900 border border-cyan-700/40 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-amber-400 text-lg">★</span>
        <h3 className="text-sm font-semibold text-slate-100">Best Model</h3>
        {registered && (
          <span className="ml-auto text-xs bg-emerald-900/60 text-emerald-300 border border-emerald-700 rounded-full px-2 py-0.5">
            Registered · {registered.stage}
          </span>
        )}
      </div>

      {bestRun && (
        <div className="space-y-3">
          <div>
            <p className="text-xl font-bold text-cyan-300">{bestRun.model_name}</p>
            <p className="text-xs text-slate-500 font-mono truncate">{bestRun.run_id}</p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "F1 Macro",  val: fmt(bestRun.f1_macro) },
              { label: "Accuracy",  val: fmt(bestRun.accuracy) },
              { label: "AUC",       val: fmt(bestRun.roc_auc) },
            ].map(({ label, val }) => (
              <div key={label} className="bg-slate-800/50 rounded-lg p-2.5 text-center">
                <p className="text-xs text-slate-400">{label}</p>
                <p className="text-base font-semibold font-mono text-cyan-200 mt-0.5">{val}</p>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>v{bestRun.dataset_version ?? "?"} dataset · {fmtDate(bestRun.start_time)}</span>
            <button
              onClick={() => onSelect(bestRun)}
              className="text-cyan-400 hover:text-cyan-200 underline underline-offset-2"
            >
              View details →
            </button>
          </div>
        </div>
      )}

      {!bestRun && registered && (
        <div className="space-y-1">
          <p className="text-lg font-bold text-cyan-300">{registered.best_model_name ?? registered.name}</p>
          <p className="text-xs text-slate-500">
            Version {registered.latest_version} · Updated {fmtDate(registered.last_updated_time)}
          </p>
        </div>
      )}
    </div>
  );
}
