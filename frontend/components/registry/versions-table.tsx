"use client";
import React from "react";
import { ModelVersionInfo } from "@/lib/api";

interface Props {
  versions:   ModelVersionInfo[];
  onArchive:  (version: string) => void;
}

const STAGE_BADGE: Record<string, string> = {
  Production: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  Staging:    "bg-amber-500/20 text-amber-300 border-amber-500/40",
  Archived:   "bg-slate-700/50 text-slate-500 border-slate-600/40",
  None:       "bg-slate-700/50 text-slate-500 border-slate-600/40",
};

export function VersionsTable({ versions, onArchive }: Props) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-slate-200">
          All Versions
          <span className="ml-2 text-xs font-normal text-slate-500">({versions.length})</span>
        </h3>
      </div>
      {versions.length === 0 ? (
        <div className="p-5 text-center text-slate-500 text-sm">No registered versions</div>
      ) : (
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-800/50 border-b border-slate-700 sticky top-0">
              <tr>
                <th className="px-5 py-2 text-left text-xs font-medium text-slate-400">Version</th>
                <th className="px-5 py-2 text-left text-xs font-medium text-slate-400">Stage</th>
                <th className="px-5 py-2 text-left text-xs font-medium text-slate-400">Model</th>
                <th className="px-5 py-2 text-right text-xs font-medium text-slate-400">F1</th>
                <th className="px-5 py-2 text-right text-xs font-medium text-slate-400">AUC</th>
                <th className="px-5 py-2 text-center text-xs font-medium text-slate-400">Action</th>
              </tr>
            </thead>
            <tbody>
              {versions.map((v) => (
                <tr key={v.version} className="border-t border-slate-800/60 hover:bg-slate-800/30">
                  <td className="px-5 py-2 font-mono text-xs text-slate-300">v{v.version}</td>
                  <td className="px-5 py-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${STAGE_BADGE[v.stage] ?? STAGE_BADGE.None}`}>
                      {v.stage}
                    </span>
                  </td>
                  <td className="px-5 py-2 text-xs text-slate-400">{v.model_name ?? "—"}</td>
                  <td className="px-5 py-2 text-right font-mono text-xs text-slate-300">
                    {v.f1_macro?.toFixed(4) ?? "—"}
                  </td>
                  <td className="px-5 py-2 text-right font-mono text-xs text-slate-400">
                    {v.roc_auc?.toFixed(4) ?? "—"}
                  </td>
                  <td className="px-5 py-2 text-center">
                    {v.stage !== "Archived" && v.stage !== "Production" && (
                      <button
                        onClick={() => onArchive(v.version)}
                        className="text-xs text-slate-500 hover:text-rose-400 transition-colors"
                      >
                        Archive
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
