"use client";

import { useState } from "react";
import { AlertCircle, Database, FlaskConical } from "lucide-react";
import { useStrategyLab } from "@/hooks/use-strategy-lab";
import { TickerSelector } from "@/components/market/ticker-selector";
import { PipelineStatusBar } from "@/components/strategy/pipeline-status-bar";
import { DatasetSelector } from "@/components/strategy/dataset-selector";
import { DatasetSummaryCard } from "@/components/strategy/dataset-summary-card";
import { FeatureStatsPanel } from "@/components/strategy/feature-stats-panel";
import { LabelDistributionChart } from "@/components/strategy/label-distribution-chart";
import { SampleDataTable } from "@/components/strategy/sample-data-table";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { FEATURE_GROUPS, GROUP_COLORS, GROUP_LABELS } from "@/lib/features";
import type { FeatureGroup } from "@/lib/features";
import { cn } from "@/lib/utils";
import { useMarketData } from "@/hooks/use-market-data";

export default function StrategyLabPage() {
  const [activeGroup, setActiveGroup] = useState<FeatureGroup>("trend");

  // Reuse ticker list from market hook (already in DB)
  const { tickers, isLoadingTickers } = useMarketData();

  const {
    selectedTicker,   setSelectedTicker,
    selectedVersion,  setSelectedVersion,
    datasetVersions,
    datasetSummary,
    featureStats,
    labelDistributions,
    sampleData,
    pipelineStatus,
    pipelineMessage,
    error,
    isLoadingStats,
    isLoadingLabels,
    isLoadingSample,
    hasFeatureData,
    triggerPipeline,
  } = useStrategyLab(tickers[0]?.ticker ?? "AAPL");

  const groups = Object.keys(FEATURE_GROUPS) as FeatureGroup[];

  return (
    <div className="flex flex-col gap-4">
      {/* ------------------------------------------------------------------ */}
      {/* Header                                                               */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Strategy Lab</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Feature engineering, label distribution, and ML dataset versioning.
          </p>
        </div>
        <PipelineStatusBar
          status={pipelineStatus}
          message={pipelineMessage}
          onRun={triggerPipeline}
        />
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Controls row                                                         */}
      {/* ------------------------------------------------------------------ */}
      <Card className="bg-slate-900 border-slate-800">
        <CardContent className="pt-4 pb-4">
          <div className="flex items-center gap-3 flex-wrap">
            {isLoadingTickers ? (
              <Skeleton className="h-9 w-32 bg-slate-800" />
            ) : (
              <TickerSelector
                tickers={tickers}
                selected={selectedTicker}
                onChange={setSelectedTicker}
              />
            )}

            <div className="w-px h-6 bg-slate-800 hidden sm:block" />

            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-slate-500" />
              <DatasetSelector
                versions={datasetVersions}
                selected={selectedVersion}
                onChange={setSelectedVersion}
              />
            </div>

            {/* Feature group tabs */}
            <div className="ml-auto flex items-center gap-1 flex-wrap">
              {groups.map((g) => (
                <button
                  key={g}
                  onClick={() => setActiveGroup(g)}
                  className={cn(
                    "px-3 py-1.5 rounded-md text-xs font-semibold transition-all",
                    activeGroup === g
                      ? "text-slate-950"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                  )}
                  style={activeGroup === g ? { backgroundColor: GROUP_COLORS[g] } : undefined}
                >
                  {GROUP_LABELS[g]}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ------------------------------------------------------------------ */}
      {/* Empty state                                                          */}
      {/* ------------------------------------------------------------------ */}
      {!hasFeatureData && pipelineStatus !== "running" && (
        <NoDataState onRun={triggerPipeline} isRunning={false} />
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Dataset summary + label distribution (side by side)                 */}
      {/* ------------------------------------------------------------------ */}
      {(hasFeatureData || datasetVersions.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <DatasetSummaryCard
            summary={datasetSummary}
            isLoading={pipelineStatus === "running"}
          />
          <LabelDistributionChart
            distributions={labelDistributions}
            isLoading={isLoadingLabels || pipelineStatus === "running"}
          />
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Feature statistics (synced to active group tab)                      */}
      {/* ------------------------------------------------------------------ */}
      <FeatureStatsPanel
        stats={featureStats}
        isLoading={isLoadingStats || pipelineStatus === "running"}
      />

      {/* ------------------------------------------------------------------ */}
      {/* Sample data table (synced to active group tab)                       */}
      {/* ------------------------------------------------------------------ */}
      <SampleDataTable
        data={sampleData}
        isLoading={isLoadingSample || pipelineStatus === "running"}
        activeGroup={activeGroup}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function NoDataState({ onRun, isRunning }: { onRun: () => void; isRunning: boolean }) {
  return (
    <Card className="bg-slate-900 border-slate-800 border-dashed">
      <CardContent className="pt-12 pb-12">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center">
            <FlaskConical className="w-6 h-6 text-slate-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-300">No feature data yet</p>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              Run the feature pipeline to compute 35 technical indicators and build
              BUY / SELL / HOLD labels from the market data in the database.
            </p>
          </div>
          <button
            onClick={onRun}
            disabled={isRunning}
            className="flex items-center gap-2 h-9 px-5 rounded-lg bg-cyan-500 text-slate-950 text-sm font-bold hover:bg-cyan-400 transition-colors disabled:opacity-50"
          >
            <FlaskConical className="w-4 h-4" />
            {isRunning ? "Running…" : "Run Feature Pipeline"}
          </button>
        </div>
      </CardContent>
    </Card>
  );
}
