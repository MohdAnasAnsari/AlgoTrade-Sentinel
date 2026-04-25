"use client";
import React from "react";
import { DatasetVersion } from "@/lib/api";
import { TrainingJobStatus } from "@/lib/api";

interface Props {
  datasetVersions: DatasetVersion[];
  selectedVersion: number;
  onVersionChange: (v: number) => void;
  allModels: string[];
  selectedModels: string[];
  onToggleModel: (m: string) => void;
  runName: string;
  onRunNameChange: (v: string) => void;
  nTrials: number;
  onTrialsChange: (v: number) => void;
  onStart: () => void;
  isRunning: boolean;
  starting: boolean;
  jobStatus: TrainingJobStatus | null;
}

const MODEL_LABELS: Record<string, string> = {
  LogisticRegression:         "Logistic Regression",
  DecisionTreeClassifier:     "Decision Tree",
  RandomForestClassifier:     "Random Forest",
  GradientBoostingClassifier: "Gradient Boosting",
  XGBClassifier:              "XGBoost",
  LGBMClassifier:             "LightGBM",
  CatBoostClassifier:         "CatBoost",
};

export function RunTrainingPanel({
  datasetVersions, selectedVersion, onVersionChange,
  allModels, selectedModels, onToggleModel,
  runName, onRunNameChange,
  nTrials, onTrialsChange,
  onStart, isRunning, starting, jobStatus,
}: Props) {
  const statusColor =
    jobStatus?.status === "complete" ? "text-emerald-400"
    : jobStatus?.status === "failed" ? "text-rose-400"
    : "text-cyan-400";

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 space-y-5">
      <h2 className="text-base font-semibold text-slate-100">Training Configuration</h2>

      {/* Dataset */}
      <div>
        <label className="block text-xs font-medium text-slate-400 mb-1">Dataset Version</label>
        <select
          value={selectedVersion}
          onChange={(e) => onVersionChange(Number(e.target.value))}
          className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
        >
          {datasetVersions.length === 0 && (
            <option value={1}>v1 (default)</option>
          )}
          {datasetVersions.map((v) => (
            <option key={v.version} value={v.version}>
              v{v.version} — {v.n_rows ?? "?"} rows
            </option>
          ))}
        </select>
      </div>

      {/* Models */}
      <div>
        <label className="block text-xs font-medium text-slate-400 mb-2">Models</label>
        <div className="grid grid-cols-2 gap-1.5">
          {allModels.map((m) => (
            <label key={m} className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={selectedModels.includes(m)}
                onChange={() => onToggleModel(m)}
                className="rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
              />
              <span className="text-xs text-slate-300 group-hover:text-slate-100">
                {MODEL_LABELS[m] ?? m}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Run name */}
      <div>
        <label className="block text-xs font-medium text-slate-400 mb-1">Run Name</label>
        <input
          type="text"
          value={runName}
          onChange={(e) => onRunNameChange(e.target.value)}
          className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          placeholder="training_run"
        />
      </div>

      {/* Optuna trials */}
      <div>
        <label className="block text-xs font-medium text-slate-400 mb-1">
          Optuna Trials: <span className="text-cyan-400 font-mono">{nTrials}</span>
        </label>
        <input
          type="range"
          min={0} max={50} step={5}
          value={nTrials}
          onChange={(e) => onTrialsChange(Number(e.target.value))}
          className="w-full accent-cyan-500"
        />
        <div className="flex justify-between text-xs text-slate-500 mt-0.5">
          <span>0 (skip)</span><span>50</span>
        </div>
      </div>

      {/* Start button */}
      <button
        onClick={onStart}
        disabled={isRunning || starting || selectedModels.length === 0}
        className="w-full flex items-center justify-center gap-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 text-sm transition-colors"
      >
        {(isRunning || starting) && (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
        )}
        {isRunning || starting ? "Training…" : "Start Training"}
      </button>

      {/* Status message */}
      {jobStatus && (
        <p className={`text-xs ${statusColor} text-center`}>{jobStatus.message}</p>
      )}
    </div>
  );
}
