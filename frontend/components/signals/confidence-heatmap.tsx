"use client";
import React, { useMemo } from "react";
import { LatestSignal } from "@/lib/api";

interface Props {
  signals: LatestSignal[];
}

const SIG_BG: Record<string, (conf: number) => string> = {
  BUY:  (c) => `rgba(16,185,129,${0.15 + c * 0.7})`,
  SELL: (c) => `rgba(244,63,94,${0.15 + c * 0.7})`,
  HOLD: (c) => `rgba(245,158,11,${0.10 + c * 0.5})`,
};

export function ConfidenceHeatmap({ signals }: Props) {
  const sorted = useMemo(
    () => [...signals].sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0)),
    [signals]
  );

  if (!sorted.length) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 text-center text-slate-500 text-sm">
        No signals to display
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-slate-200 mb-4">Confidence Heatmap</h3>
      <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 xl:grid-cols-10 gap-1.5">
        {sorted.map((s) => {
          const sig  = s.signal ?? "HOLD";
          const conf = s.confidence ?? 0;
          const bg   = (SIG_BG[sig] ?? SIG_BG.HOLD)(conf);
          const pct  = Math.round(conf * 100);
          return (
            <div
              key={s.ticker}
              className="rounded-lg p-1.5 text-center"
              style={{ background: bg }}
              title={`${s.ticker}: ${sig} ${pct}% (${s.signal_date})`}
            >
              <div className="text-xs font-bold text-white/90 truncate">{s.ticker}</div>
              <div className="text-[10px] text-white/70 font-mono">{pct}%</div>
            </div>
          );
        })}
      </div>
      <div className="flex items-center gap-4 mt-3 text-xs text-slate-500 justify-end">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm" style={{ background: "rgba(16,185,129,0.6)" }} />BUY
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm" style={{ background: "rgba(244,63,94,0.6)" }} />SELL
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm" style={{ background: "rgba(245,158,11,0.5)" }} />HOLD
        </span>
      </div>
    </div>
  );
}
