"use client";
import React from "react";
import { ModelVersionInfo } from "@/lib/api";

interface Props {
  target:      ModelVersionInfo;
  notes:       string;
  onNotesChange: (v: string) => void;
  onConfirm:   () => void;
  onCancel:    () => void;
  promoting:   boolean;
  result:      string | null;
}

export function PromoteModal({
  target, notes, onNotesChange, onConfirm, onCancel, promoting, result,
}: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
        <h2 className="text-base font-semibold text-slate-100 mb-1">Promote to Production</h2>
        <p className="text-xs text-slate-400 mb-5">
          Promote <span className="font-mono text-slate-200">v{target.version}</span>
          {" "}({target.model_name}) to Production. The current champion will be archived.
        </p>

        {/* Metrics summary */}
        <div className="grid grid-cols-3 gap-3 mb-5">
          {[
            { label: "F1 Macro", value: target.f1_macro?.toFixed(4) ?? "—" },
            { label: "Accuracy", value: target.accuracy != null ? (target.accuracy * 100).toFixed(1) + "%" : "—" },
            { label: "ROC-AUC",  value: target.roc_auc?.toFixed(4) ?? "—" },
          ].map(({ label, value }) => (
            <div key={label} className="bg-slate-800 rounded-lg p-2.5 text-center">
              <div className="text-sm font-mono font-bold text-slate-100">{value}</div>
              <div className="text-xs text-slate-500">{label}</div>
            </div>
          ))}
        </div>

        {/* Notes */}
        <label className="block text-xs text-slate-400 mb-1">Notes (optional)</label>
        <textarea
          value={notes}
          onChange={(e) => onNotesChange(e.target.value)}
          rows={3}
          className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 resize-none mb-4"
          placeholder="Reason for promoting this model…"
        />

        {result && (
          <p className={`text-xs mb-4 ${result.startsWith("Model") ? "text-emerald-400" : "text-rose-400"}`}>
            {result}
          </p>
        )}

        <div className="flex items-center justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 border border-slate-700 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={promoting}
            className="px-4 py-2 text-xs font-semibold text-white bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 rounded-lg transition-colors"
          >
            {promoting ? "Promoting…" : "Confirm Promote"}
          </button>
        </div>
      </div>
    </div>
  );
}
