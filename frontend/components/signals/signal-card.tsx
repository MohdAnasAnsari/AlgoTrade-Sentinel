"use client";
import React from "react";
import { LatestSignal } from "@/lib/api";

interface Props {
  signal:     LatestSignal;
  selected:   boolean;
  onSelect:   () => void;
}

const BADGE: Record<string, string> = {
  BUY:  "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  SELL: "bg-rose-500/20 text-rose-300 border-rose-500/40",
  HOLD: "bg-amber-500/20 text-amber-300 border-amber-500/40",
};

export function SignalCard({ signal: s, selected, onSelect }: Props) {
  const pct = Math.round((s.confidence ?? 0) * 100);
  const sig  = s.signal ?? "HOLD";

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left rounded-xl border p-4 transition-all ${
        selected
          ? "border-cyan-500/60 bg-slate-800/80 ring-1 ring-cyan-500/30"
          : "border-slate-700 bg-slate-900 hover:border-slate-600"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-bold text-slate-100">{s.ticker}</span>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${BADGE[sig] ?? BADGE.HOLD}`}>
          {sig}
        </span>
      </div>

      {/* Confidence bar */}
      <div className="mb-2">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
          <span>Confidence</span>
          <span className="font-mono text-slate-300">{pct}%</span>
        </div>
        <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              sig === "BUY" ? "bg-emerald-500" : sig === "SELL" ? "bg-rose-500" : "bg-amber-500"
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Date */}
      <p className="text-xs text-slate-600 mt-2">
        {s.signal_date ?? "—"}
      </p>
    </button>
  );
}
