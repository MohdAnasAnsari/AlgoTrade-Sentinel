"use client";
import React, { useMemo } from "react";
import dynamic from "next/dynamic";
import { useSignalCenter } from "@/hooks/use-signal-center";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading";
import { SignalCard } from "@/components/signals/signal-card";
import { SignalFilterBar } from "@/components/signals/signal-filter-bar";
import { SignalDetailPanel } from "@/components/signals/signal-detail-panel";
import { LatestSignal } from "@/lib/api";

type Filter = "ALL" | "BUY" | "SELL" | "HOLD";

const SignalHistoryChart = dynamic(
  () => import("@/components/signals/signal-history-chart").then((mod) => mod.SignalHistoryChart),
  {
    ssr: false,
    loading: () => (
      <LoadingState message="Loading signal history chart..." className="min-h-[220px]" />
    ),
  }
);

const ConfidenceHeatmap = dynamic(
  () => import("@/components/signals/confidence-heatmap").then((mod) => mod.ConfidenceHeatmap),
  {
    ssr: false,
    loading: () => (
      <LoadingState message="Loading confidence heatmap..." className="min-h-[220px]" />
    ),
  }
);

export default function SignalCenterPage() {
  const sc = useSignalCenter();

  const counts = useMemo(() => {
    const c: Partial<Record<Filter, number>> = { ALL: sc.latestSignals.length };
    for (const s of sc.latestSignals) {
      const sig = (s.signal ?? "HOLD") as Filter;
      c[sig] = (c[sig] ?? 0) + 1;
    }
    return c;
  }, [sc.latestSignals]);

  const selectedSignal = sc.selectedTicker
    ? sc.latestSignals.find((s) => s.ticker === sc.selectedTicker) ?? null
    : null;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/60 px-6 py-4">
        <div className="max-w-screen-2xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">Signal Center</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              ML-generated BUY / HOLD / SELL signals with confidence scores
            </p>
          </div>
          <div className="flex items-center gap-3">
            {sc.jobStatus && (
              <span className={`text-xs px-2.5 py-1 rounded-lg border ${
                sc.jobStatus.status === "complete" ? "border-emerald-500/40 text-emerald-400 bg-emerald-500/10" :
                sc.jobStatus.status === "failed"   ? "border-rose-500/40 text-rose-400 bg-rose-500/10" :
                "border-amber-500/40 text-amber-400 bg-amber-500/10"
              }`}>
                {sc.jobStatus.message}
              </span>
            )}
            <button
              onClick={() => sc.startInference()}
              disabled={sc.starting || sc.isRunning}
              className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white border border-slate-700 rounded-lg px-3 py-1.5 transition-colors disabled:opacity-50"
            >
              {sc.isRunning ? (
                <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                </svg>
              ) : (
                <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
              )}
              {sc.isRunning ? "Running…" : "Run Inference"}
            </button>
            <button
              onClick={sc.loadLatest}
              disabled={sc.loadingLatest}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 transition-colors"
            >
              <svg className={`h-3.5 w-3.5 ${sc.loadingLatest ? "animate-spin" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-screen-2xl mx-auto px-6 py-6 space-y-6">
        {sc.error && <ErrorState message={sc.error} />}

        {/* Filter bar */}
        <SignalFilterBar
          active={sc.signalFilter as Filter}
          onChange={sc.setSignalFilter as (f: Filter) => void}
          counts={counts}
        />

        {/* Main grid */}
        <div className="grid grid-cols-1 xl:grid-cols-[1fr_340px] gap-6">
          {/* Left: signal cards grid */}
          <div>
            {sc.loadingLatest ? (
              <div className="flex items-center justify-center h-48 text-slate-500 text-sm">
                <svg className="animate-spin h-6 w-6 text-cyan-400 mr-2" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                </svg>
                Loading signals…
              </div>
            ) : sc.latestSignals.length === 0 ? (
              <div className="flex items-center justify-center h-48 rounded-xl border border-slate-800 text-slate-500 text-sm">
                No signals yet — run inference to generate signals
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-3 gap-3">
                {sc.latestSignals.map((s: LatestSignal) => (
                  <SignalCard
                    key={s.ticker}
                    signal={s}
                    selected={sc.selectedTicker === s.ticker}
                    onSelect={() =>
                      sc.selectedTicker === s.ticker
                        ? sc.selectTicker(null)
                        : sc.selectTicker(s.ticker)
                    }
                  />
                ))}
              </div>
            )}
          </div>

          {/* Right: detail panel */}
          {selectedSignal ? (
            <SignalDetailPanel signal={selectedSignal} />
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center justify-center text-slate-600 text-sm">
              Select a ticker to view details
            </div>
          )}
        </div>

        {/* History chart (when ticker selected) */}
        {sc.selectedTicker && (
          <SignalHistoryChart
            ticker={sc.selectedTicker}
            data={sc.tickerHistory}
          />
        )}

        {/* Confidence heatmap */}
        {sc.latestSignals.length > 0 && (
          <ConfidenceHeatmap signals={sc.latestSignals} />
        )}
      </div>
    </div>
  );
}
