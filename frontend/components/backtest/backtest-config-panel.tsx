"use client";
import React from "react";
import { BacktestJobStatus, ExperimentRun } from "@/lib/api";

interface Props {
  experimentRuns:  ExperimentRun[];
  modelRunId:      string;
  onModelChange:   (v: string) => void;
  availableTickers: string[];
  selectedTickers: string[];
  onToggleTicker:  (t: string) => void;
  startDate:       string;
  onStartDate:     (v: string) => void;
  endDate:         string;
  onEndDate:       (v: string) => void;
  initialCapital:  number;
  onCapital:       (v: number) => void;
  transactionCost: number;
  onTCost:         (v: number) => void;
  onStart:         () => void;
  isRunning:       boolean;
  starting:        boolean;
  jobStatus:       BacktestJobStatus | null;
}

const STATUS_COLOR = {
  running:  "text-cyan-400",
  complete: "text-emerald-400",
  failed:   "text-rose-400",
} as const;

export function BacktestConfigPanel({
  experimentRuns, modelRunId, onModelChange,
  availableTickers, selectedTickers, onToggleTicker,
  startDate, onStartDate, endDate, onEndDate,
  initialCapital, onCapital, transactionCost, onTCost,
  onStart, isRunning, starting, jobStatus,
}: Props) {
  const tcPct = (transactionCost * 100).toFixed(2);

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 space-y-5">
      <h2 className="text-base font-semibold text-slate-100">Backtest Configuration</h2>

      {/* Model selector */}
      <div>
        <label className="block text-xs font-medium text-slate-400 mb-1">
          Model Run <span className="text-slate-600">(optional — omit for oracle labels)</span>
        </label>
        <select
          value={modelRunId}
          onChange={(e) => onModelChange(e.target.value)}
          className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
        >
          <option value="">— Oracle Labels (no model) —</option>
          {experimentRuns.map((r) => (
            <option key={r.run_id} value={r.run_id}>
              {r.model_name} · F1={r.f1_macro?.toFixed(4) ?? "?"} · {r.run_id.slice(0, 8)}
            </option>
          ))}
        </select>
      </div>

      {/* Ticker multi-select */}
      <div>
        <label className="block text-xs font-medium text-slate-400 mb-2">
          Tickers <span className="text-slate-600">({selectedTickers.length} selected)</span>
        </label>
        {availableTickers.length === 0 ? (
          <p className="text-xs text-slate-500">No tickers in DB — ingest data first</p>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {availableTickers.map((t) => {
              const sel = selectedTickers.includes(t);
              return (
                <button
                  key={t}
                  onClick={() => onToggleTicker(t)}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                    sel
                      ? "bg-cyan-600 border-cyan-500 text-white"
                      : "bg-slate-800 border-slate-600 text-slate-400 hover:border-slate-500"
                  }`}
                >
                  {t}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Date range */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => onStartDate(e.target.value)}
            className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => onEndDate(e.target.value)}
            className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
        </div>
      </div>

      {/* Initial capital */}
      <div>
        <label className="block text-xs font-medium text-slate-400 mb-1">Initial Capital ($)</label>
        <input
          type="number"
          value={initialCapital}
          min={1000}
          step={10000}
          onChange={(e) => onCapital(Number(e.target.value))}
          className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
        />
      </div>

      {/* Transaction cost */}
      <div>
        <label className="block text-xs font-medium text-slate-400 mb-1">
          Transaction Cost: <span className="text-cyan-400 font-mono">{tcPct}%</span>
        </label>
        <input
          type="range"
          min={0} max={0.005} step={0.0001}
          value={transactionCost}
          onChange={(e) => onTCost(Number(e.target.value))}
          className="w-full accent-cyan-500"
        />
        <div className="flex justify-between text-xs text-slate-500 mt-0.5">
          <span>0%</span><span>0.5%</span>
        </div>
      </div>

      {/* Run button */}
      <button
        onClick={onStart}
        disabled={isRunning || starting || selectedTickers.length === 0}
        className="w-full flex items-center justify-center gap-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 text-sm transition-colors"
      >
        {(isRunning || starting) && (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
        )}
        {isRunning || starting ? "Running Backtest…" : "Run Backtest"}
      </button>

      {jobStatus && (
        <p className={`text-xs text-center ${STATUS_COLOR[jobStatus.status] ?? "text-slate-400"}`}>
          {jobStatus.message}
        </p>
      )}
    </div>
  );
}
