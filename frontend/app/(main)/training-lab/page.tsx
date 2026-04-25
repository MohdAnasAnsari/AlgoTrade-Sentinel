"use client";
import React from "react";
import dynamic from "next/dynamic";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading";
import { useTrainingLab } from "@/hooks/use-training-lab";
import { RunTrainingPanel } from "@/components/training/run-training-panel";
import { ExperimentsTable } from "@/components/training/experiments-table";
import { RunDetailPanel } from "@/components/training/run-detail-panel";
import { BestModelCard } from "@/components/training/best-model-card";

const ModelComparisonChart = dynamic(
  () => import("@/components/training/model-comparison-chart").then((mod) => mod.ModelComparisonChart),
  {
    ssr: false,
    loading: () => (
      <LoadingState message="Loading model comparison chart..." className="min-h-[220px]" />
    ),
  }
);

const FeatureImportanceChart = dynamic(
  () => import("@/components/training/feature-importance-chart").then((mod) => mod.FeatureImportanceChart),
  {
    ssr: false,
    loading: () => (
      <LoadingState message="Loading feature importance chart..." className="min-h-[220px]" />
    ),
  }
);

export default function TrainingLabPage() {
  const lab = useTrainingLab();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Page header */}
      <div className="border-b border-slate-800 bg-slate-900/60 px-6 py-4">
        <div className="max-w-screen-2xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">Training Lab</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Train &amp; evaluate ML models — experiments tracked via MLflow
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

        {/* Top row: config + best model */}
        <div className="grid grid-cols-1 xl:grid-cols-[360px_1fr] gap-6">
          <RunTrainingPanel
            datasetVersions={lab.datasetVersions}
            selectedVersion={lab.selectedVersion}
            onVersionChange={lab.setSelectedVersion}
            allModels={lab.allModels}
            selectedModels={lab.selectedModels}
            onToggleModel={lab.toggleModel}
            runName={lab.runName}
            onRunNameChange={lab.setRunName}
            nTrials={lab.nTrials}
            onTrialsChange={lab.setNTrials}
            onStart={lab.startTraining}
            isRunning={lab.isRunning}
            starting={lab.starting}
            jobStatus={lab.jobStatus}
          />

          <div className="space-y-6">
            <BestModelCard
              bestRun={lab.bestRun}
              registeredModels={lab.registeredModels}
              onSelect={lab.selectRun}
            />
            <ModelComparisonChart
              runs={lab.runs}
              selectedRunId={lab.selectedRun?.run_id ?? null}
            />
          </div>
        </div>

        {/* Experiments table */}
        <div>
          <h2 className="text-sm font-semibold text-slate-300 mb-3">
            Experiment Runs
            <span className="ml-2 text-xs font-normal text-slate-500">
              ({lab.runs.length} run{lab.runs.length !== 1 ? "s" : ""})
            </span>
          </h2>
          <ExperimentsTable
            runs={lab.runs}
            selectedRunId={lab.selectedRun?.run_id ?? null}
            onSelect={lab.selectRun}
          />
        </div>

        {/* Selected run detail */}
        {(lab.selectedRun || lab.loadingDetails) && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <RunDetailPanel
              details={lab.runDetails}
              loading={lab.loadingDetails}
            />
            <FeatureImportanceChart data={lab.featureImportances} />
          </div>
        )}
      </div>
    </div>
  );
}
