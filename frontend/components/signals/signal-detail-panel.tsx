"use client";
import React from "react";
import { LatestSignal } from "@/lib/api";

interface Props {
  signal: LatestSignal;
}

function ProbBar({ label, value, color }: { label: string; value: number | null; color: string }) {
  const pct = Math.round((value ?? 0) * 100);
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-slate-400">{label}</span>
        <span className="font-mono text-slate-200">{pct}%</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function SignalDetailPanel({ signal: s }: Props) {
  const explanation = s.explanation ?? "";
  const topFeatures = explanation
    .split(";")
    .map((p) => p.trim())
    .filter(Boolean)
    .slice(0, 3);

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 space-y-5">
      {/* Header */}
      <div>
        <h3 className="text-sm font-semibold text-slate-200">{s.ticker} — Signal Detail</h3>
        <p className="text-xs text-slate-500 mt-0.5">{s.signal_date ?? "—"}</p>
      </div>

      {/* Probability bars */}
      <div className="space-y-3">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wide">Class Probabilities</p>
        <ProbBar label="BUY"  value={s.prob_buy}  color="bg-emerald-500" />
        <ProbBar label="HOLD" value={s.prob_hold} color="bg-amber-500"   />
        <ProbBar label="SELL" value={s.prob_sell} color="bg-rose-500"    />
      </div>

      {/* Top features */}
      {topFeatures.length > 0 && (
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">
            Key Drivers
          </p>
          <div className="space-y-1.5">
            {topFeatures.map((f, i) => (
              <div key={i} className="flex items-center gap-2 bg-slate-800/50 rounded-lg px-3 py-1.5">
                <span className="text-slate-500 text-xs w-4">{i + 1}.</span>
                <span className="font-mono text-xs text-slate-300">{f}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Model info */}
      {s.model_version && (
        <p className="text-xs text-slate-600">
          Model v{s.model_version}
        </p>
      )}
    </div>
  );
}
