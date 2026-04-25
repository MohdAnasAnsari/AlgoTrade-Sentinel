"use client";
import React, { useState } from "react";
import { ErrorState } from "@/components/shared/error-state";
import { useModelRegistry } from "@/hooks/use-model-registry";
import { ChampionCard } from "@/components/registry/champion-card";
import { ChallengerTable } from "@/components/registry/challenger-table";
import { VersionsTable } from "@/components/registry/versions-table";
import { MetricsComparison } from "@/components/registry/metrics-comparison";
import { PromoteModal } from "@/components/registry/promote-modal";

export default function ModelRegistryPage() {
  const reg = useModelRegistry("signal-predictor");
  const [autoResult, setAutoResult] = useState<string | null>(null);

  const handleAutoPromote = async () => {
    const result = await reg.runAutoPromote();
    if (result) {
      setAutoResult(result.promoted ? result.message : "No promotion — challenger did not exceed threshold");
      setTimeout(() => setAutoResult(null), 5000);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/60 px-6 py-4">
        <div className="max-w-screen-2xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">Model Registry</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Manage model lifecycle — champion, challengers, promotion, and audit log
            </p>
          </div>
          <div className="flex items-center gap-3">
            {autoResult && (
              <span className="text-xs px-2.5 py-1 rounded-lg border border-cyan-500/40 text-cyan-400 bg-cyan-500/10">
                {autoResult}
              </span>
            )}
            <button
              onClick={handleAutoPromote}
              className="text-xs text-slate-300 hover:text-white border border-slate-700 rounded-lg px-3 py-1.5 transition-colors"
            >
              Auto-Promote Check
            </button>
            <button
              onClick={reg.load}
              disabled={reg.loading}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 transition-colors"
            >
              <svg className={`h-3.5 w-3.5 ${reg.loading ? "animate-spin" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-screen-2xl mx-auto px-6 py-6 space-y-6">
        {reg.error && <ErrorState message={reg.error} />}

        {/* Champion card */}
        <ChampionCard champion={reg.champion} />

        {/* Challengers + comparison */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <ChallengerTable
            challengers={reg.challengers}
            championF1={reg.champion?.f1_macro ?? null}
            onPromote={reg.setPromoteTarget}
          />
          {reg.comparison && <MetricsComparison comparison={reg.comparison} />}
        </div>

        {/* All versions */}
        <VersionsTable
          versions={reg.allVersions}
          onArchive={reg.archive}
        />

        {/* Audit log */}
        {reg.auditLog.length > 0 && (
          <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-700">
              <h3 className="text-sm font-semibold text-slate-200">Promotion Audit Log</h3>
            </div>
            <div className="overflow-x-auto max-h-52 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-800/50 sticky top-0">
                  <tr>
                    <th className="px-5 py-2 text-left text-xs font-medium text-slate-400">Date</th>
                    <th className="px-5 py-2 text-left text-xs font-medium text-slate-400">Version</th>
                    <th className="px-5 py-2 text-left text-xs font-medium text-slate-400">Stage</th>
                    <th className="px-5 py-2 text-right text-xs font-medium text-slate-400">F1</th>
                    <th className="px-5 py-2 text-left text-xs font-medium text-slate-400">By</th>
                    <th className="px-5 py-2 text-left text-xs font-medium text-slate-400">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {reg.auditLog.map((entry) => (
                    <tr key={entry.id} className="border-t border-slate-800/60">
                      <td className="px-5 py-2 text-xs text-slate-500 font-mono">
                        {entry.promoted_at ? entry.promoted_at.slice(0, 16) : "—"}
                      </td>
                      <td className="px-5 py-2 text-xs text-slate-300 font-mono">v{entry.version}</td>
                      <td className="px-5 py-2 text-xs text-slate-400">{entry.stage}</td>
                      <td className="px-5 py-2 text-right text-xs font-mono text-slate-300">
                        {entry.f1_score?.toFixed(4) ?? "—"}
                      </td>
                      <td className="px-5 py-2 text-xs text-slate-500">{entry.promoted_by ?? "—"}</td>
                      <td className="px-5 py-2 text-xs text-slate-600 max-w-xs truncate">{entry.notes ?? ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Promote modal */}
      {reg.promoteTarget && (
        <PromoteModal
          target={reg.promoteTarget}
          notes={reg.promoteNotes}
          onNotesChange={reg.setPromoteNotes}
          onConfirm={reg.promote}
          onCancel={() => { reg.setPromoteTarget(null); reg.setPromoteResult(null); }}
          promoting={reg.promoting}
          result={reg.promoteResult}
        />
      )}
    </div>
  );
}
