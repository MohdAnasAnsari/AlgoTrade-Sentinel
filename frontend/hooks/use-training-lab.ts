"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ExperimentRun,
  FeatureImportances,
  RegisteredModel,
  RunDetails,
  StartTrainingRequest,
  TrainingJobStatus,
  datasetApi,
  DatasetVersion,
  experimentsApi,
  modelsApi,
  trainingApi,
} from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

const ALL_MODELS = [
  "LogisticRegression",
  "DecisionTreeClassifier",
  "RandomForestClassifier",
  "GradientBoostingClassifier",
  "XGBClassifier",
  "LGBMClassifier",
  "CatBoostClassifier",
];

export function useTrainingLab() {
  const { pushToast } = useToast();
  const [datasetVersions, setDatasetVersions] = useState<DatasetVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number>(1);
  const [selectedModels, setSelectedModels] = useState<string[]>(ALL_MODELS);
  const [runName, setRunName] = useState("training_run");
  const [nTrials, setNTrials] = useState(10);

  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<TrainingJobStatus | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [runs, setRuns] = useState<ExperimentRun[]>([]);
  const [bestRun, setBestRun] = useState<ExperimentRun | null>(null);
  const [selectedRun, setSelectedRun] = useState<ExperimentRun | null>(null);
  const [runDetails, setRunDetails] = useState<RunDetails | null>(null);
  const [featureImportances, setFeatureImportances] = useState<FeatureImportances | null>(null);

  const [registeredModels, setRegisteredModels] = useState<RegisteredModel[]>([]);

  const [loadingRuns, setLoadingRuns] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    datasetApi
      .getVersions()
      .then((versions) => {
        setDatasetVersions(versions);
        if (versions.length > 0) {
          setSelectedVersion(versions[versions.length - 1].version);
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load dataset versions.");
      });
  }, []);

  const loadRuns = useCallback(async () => {
    setLoadingRuns(true);
    setError(null);
    try {
      const [runsData, best, registry] = await Promise.all([
        experimentsApi.list(100),
        experimentsApi.getBest(),
        modelsApi.getRegistry(),
      ]);
      setRuns(runsData);
      setBestRun(best);
      setRegisteredModels(registry);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load training runs.");
    } finally {
      setLoadingRuns(false);
    }
  }, []);

  useEffect(() => {
    loadRuns();
  }, [loadRuns]);

  useEffect(() => {
    if (!selectedRun) {
      setRunDetails(null);
      setFeatureImportances(null);
      return;
    }

    setLoadingDetails(true);
    Promise.all([
      experimentsApi.getDetails(selectedRun.run_id),
      modelsApi.getImportance(selectedRun.run_id).catch(() => null),
    ])
      .then(([details, importances]) => {
        setRunDetails(details);
        setFeatureImportances(importances);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load run details.");
        setRunDetails(null);
        setFeatureImportances(null);
      })
      .finally(() => setLoadingDetails(false));
  }, [selectedRun]);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!jobId) return;

    pollRef.current = setInterval(async () => {
      try {
        const status = await trainingApi.getStatus(jobId);
        setJobStatus(status);
        if (status.status !== "running") {
          stopPolling();
          setStarting(false);
          pushToast({
            title: status.status === "complete" ? "Training complete" : "Training failed",
            description: status.message,
            tone: status.status === "complete" ? "success" : "error",
          });
          await loadRuns();
        }
      } catch {
        stopPolling();
        setStarting(false);
      }
    }, 5000);

    return () => stopPolling();
  }, [jobId, stopPolling, loadRuns, pushToast]);

  const startTraining = useCallback(async () => {
    setStarting(true);
    setJobStatus(null);
    setError(null);
    try {
      const body: StartTrainingRequest = {
        dataset_version: selectedVersion,
        model_list: selectedModels.length === ALL_MODELS.length ? null : selectedModels,
        run_name: runName || "training_run",
        n_optuna_trials: nTrials,
      };
      const response = await trainingApi.startTraining(body);
      pushToast({
        title: "Training started",
        description: response.message,
        tone: "success",
      });
      setJobId(response.job_id);
      setJobStatus({ job_id: response.job_id, status: "running", message: response.message });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setStarting(false);
      setError(message);
      setJobStatus({ job_id: "", status: "failed", message });
      pushToast({
        title: "Training failed",
        description: message,
        tone: "error",
      });
    }
  }, [selectedVersion, selectedModels, runName, nTrials, pushToast]);

  const toggleModel = useCallback((model: string) => {
    setSelectedModels((prev) =>
      prev.includes(model) ? prev.filter((item) => item !== model) : [...prev, model]
    );
  }, []);

  const selectRun = useCallback((run: ExperimentRun | null) => {
    setSelectedRun(run);
  }, []);

  return {
    datasetVersions,
    selectedVersion,
    setSelectedVersion,
    selectedModels,
    toggleModel,
    runName,
    setRunName,
    nTrials,
    setNTrials,
    allModels: ALL_MODELS,
    starting,
    jobStatus,
    startTraining,
    isRunning: jobStatus?.status === "running",
    runs,
    bestRun,
    loadingRuns,
    loadRuns,
    selectedRun,
    selectRun,
    runDetails,
    loadingDetails,
    featureImportances,
    registeredModels,
    error,
  };
}
