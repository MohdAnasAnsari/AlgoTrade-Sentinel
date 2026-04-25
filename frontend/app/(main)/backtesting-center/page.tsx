"use client";
import React from "react";
import dynamic from "next/dynamic";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading";
import { useBacktesting } from "@/hooks/use-backtesting";
import { useMarketData } from "@/hooks/use-market-data";
import { BacktestConfigPanel } from "@/components/backtest/backtest-config-panel";
import { BacktestRunsTable } from "@/components/backtest/backtest-runs-table";
import { MetricsGrid } from "@/components/backtest/metrics-grid";
import { TradesLogTable } from "@/components/backtest/trades-log-table";

const EquityCurveChart = dynamic(
  () => import("@/components/backtest/equity-curve-chart").then((mod) => mod.EquityCurveChart),
  {
    ssr: false,
    loading: () => <LoadingState message="Loading equity curve..." className="min-h-[220px]" />,
  }
);

const DrawdownChart = dynamic(
  () => import("@/components/backtest/drawdown-chart").then((mod) => mod.DrawdownChart),
  {
    ssr: false,
    loading: () => <LoadingState message="Loading drawdown chart..." className="min-h-[220px]" />,
  }
);

const MonthlyReturnsHeatmap = dynamic(
  () => import("@/components/backtest/monthly-returns-heatmap").then((mod) => mod.MonthlyReturnsHeatmap),
  {
    ssr: false,
    loading: () => (
      <LoadingState message="Loading monthly returns heatmap..." className="min-h-[220px]" />
    ),
  }
);

const BenchmarkComparison = dynamic(
  () => import("@/components/backtest/benchmark-comparison").then((mod) => mod.BenchmarkComparison),
  {
    ssr: false,
    loading: () => (
      <LoadingState message="Loading benchmark comparison..." className="min-h-[220px]" />
    ),
  }
);

export default function BacktestingCenterPage() {
  const { tickers } = useMarketData();
  const tickerSymbols = tickers.map((t) => t.ticker);

  const lab = useBacktesting(tickerSymbols);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Page header */}
      <div className="border-b border-slate-800 bg-slate-900/60 px-6 py-4">
        <div className="max-w-screen-2xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">Backtesting Center</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Simulate trading strategies on historical data with full performance analytics
            </p>
          </div>
          <button
            onClick={lab.loadRuns}
            disabled={lab.loadingRuns}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 transition-colors"
          >
            {lab.loadingRuns ? (
              <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
              </svg>
            ) : (
              <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            Refresh
          </button>
        </div>
      </div>

      <div className="max-w-screen-2xl mx-auto px-6 py-6 space-y-6">
        {lab.error && <ErrorState message={lab.error} />}

        {/* Top row: config panel */}
        <div className="grid grid-cols-1 xl:grid-cols-[380px_1fr] gap-6">
          <BacktestConfigPanel
            experimentRuns={lab.experimentRuns}
            modelRunId={lab.modelRunId}
            onModelChange={lab.setModelRunId}
            availableTickers={tickerSymbols}
            selectedTickers={lab.selectedTickers}
            onToggleTicker={lab.toggleTicker}
            startDate={lab.startDate}
            onStartDate={lab.setStartDate}
            endDate={lab.endDate}
            onEndDate={lab.setEndDate}
            initialCapital={lab.initialCapital}
            onCapital={lab.setInitialCapital}
            transactionCost={lab.transactionCost}
            onTCost={lab.setTransactionCost}
            onStart={lab.startBacktest}
            isRunning={lab.isRunning}
            starting={lab.starting}
            jobStatus={lab.jobStatus}
          />

          {/* Runs table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-300">
                Backtest Runs
                <span className="ml-2 text-xs font-normal text-slate-500">
                  ({lab.runs.length} result{lab.runs.length !== 1 ? "s" : ""})
                </span>
              </h2>
              {lab.selectedRun && (
                <button
                  onClick={() => lab.selectRun(null)}
                  className="text-xs text-slate-500 hover:text-slate-300"
                >
                  Clear selection ✕
                </button>
              )}
            </div>
            <BacktestRunsTable
              runs={lab.runs}
              selectedRunId={lab.selectedRun?.run_id ?? null}
              onSelect={lab.selectRun}
            />
          </div>
        </div>

        {/* Selected run report */}
        {lab.selectedRun && (
          <>
            {/* Section header */}
            <div className="flex items-center gap-3 border-t border-slate-800 pt-4">
              <h2 className="text-base font-semibold text-slate-200">
                {lab.selectedRun.ticker} — {lab.selectedRun.strategy_name}
              </h2>
              <span className="text-xs text-slate-500">
                {lab.selectedRun.start_date} → {lab.selectedRun.end_date}
              </span>
            </div>

            {/* Metrics grid */}
            <MetricsGrid summary={lab.selectedRun} />

            {/* Charts row 1: equity + drawdown */}
            {lab.loadingDetail ? (
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {[0, 1].map((i) => (
                  <div key={i} className="bg-slate-900 border border-slate-700 rounded-xl h-48 flex items-center justify-center">
                    <svg className="animate-spin h-6 w-6 text-cyan-400" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                    </svg>
                  </div>
                ))}
              </div>
            ) : lab.runDetail ? (
              <>
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                  <EquityCurveChart
                    data={lab.runDetail.equity_curve}
                    ticker={lab.selectedRun.ticker}
                  />
                  <DrawdownChart
                    data={lab.runDetail.drawdown}
                    ticker={lab.selectedRun.ticker}
                  />
                </div>

                {/* Monthly heatmap */}
                <MonthlyReturnsHeatmap data={lab.runDetail.monthly_returns} />

                {/* Bottom row: trades + benchmark */}
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                  <TradesLogTable trades={lab.runDetail.trades} />
                  <BenchmarkComparison summary={lab.selectedRun} />
                </div>
              </>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
