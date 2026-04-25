"use client";

import { useCallback, useEffect, useState } from "react";
import {
  datasetApi,
  DatasetVersion,
  featuresApi,
  FeatureListResponse,
  FeatureStatsResponse,
  LabelDistribution,
  PipelineRunResponse,
} from "@/lib/api";

export type PipelineStatus = "idle" | "running" | "success" | "failed";

export function useStrategyLab(defaultTicker = "AAPL") {
  const [selectedTicker, setSelectedTicker] = useState(defaultTicker);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);

  const [datasetVersions, setDatasetVersions] = useState<DatasetVersion[]>([]);
  const [datasetSummary, setDatasetSummary] = useState<DatasetVersion | null>(null);
  const [featureStats, setFeatureStats] = useState<FeatureStatsResponse | null>(null);
  const [labelDistributions, setLabelDistributions] = useState<LabelDistribution[]>([]);
  const [sampleData, setSampleData] = useState<FeatureListResponse | null>(null);

  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus>("idle");
  const [pipelineMessage, setPipelineMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [isLoadingVersions, setIsLoadingVersions] = useState(false);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [isLoadingLabels, setIsLoadingLabels] = useState(false);
  const [isLoadingSample, setIsLoadingSample] = useState(false);

  // ── Load dataset versions ───────────────────────────────────────────────
  const loadVersions = useCallback(async () => {
    setIsLoadingVersions(true);
    try {
      const versions = await datasetApi.getVersions();
      setDatasetVersions(versions);
      if (versions.length > 0 && selectedVersion === null) {
        setSelectedVersion(versions[0].version);
      }
    } catch {
      // no versions yet — silence
    } finally {
      setIsLoadingVersions(false);
    }
  }, [selectedVersion]);

  // ── Load dataset summary ────────────────────────────────────────────────
  const loadSummary = useCallback(async (version: number) => {
    try {
      const summary = await datasetApi.getSummary(version);
      setDatasetSummary(summary);
    } catch {
      setDatasetSummary(null);
    }
  }, []);

  // ── Load feature stats ──────────────────────────────────────────────────
  const loadFeatureStats = useCallback(async (ticker: string) => {
    setIsLoadingStats(true);
    try {
      const stats = await featuresApi.getStats(ticker);
      setFeatureStats(stats);
    } catch {
      setFeatureStats(null);
    } finally {
      setIsLoadingStats(false);
    }
  }, []);

  // ── Load label distributions ────────────────────────────────────────────
  const loadLabelDistributions = useCallback(async () => {
    setIsLoadingLabels(true);
    try {
      const dists = await featuresApi.getLabelDistributions();
      setLabelDistributions(dists);
    } catch {
      setLabelDistributions([]);
    } finally {
      setIsLoadingLabels(false);
    }
  }, []);

  // ── Load sample data ────────────────────────────────────────────────────
  const loadSampleData = useCallback(async (ticker: string) => {
    setIsLoadingSample(true);
    try {
      const data = await featuresApi.getList(ticker, 30);
      setSampleData(data);
    } catch {
      setSampleData(null);
    } finally {
      setIsLoadingSample(false);
    }
  }, []);

  // ── Initial load ────────────────────────────────────────────────────────
  useEffect(() => {
    loadVersions();
    loadLabelDistributions();
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  // ── Reload when ticker changes ──────────────────────────────────────────
  useEffect(() => {
    loadFeatureStats(selectedTicker);
    loadSampleData(selectedTicker);
  }, [selectedTicker]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Reload summary when selected version changes ────────────────────────
  useEffect(() => {
    if (selectedVersion !== null) {
      loadSummary(selectedVersion);
    }
  }, [selectedVersion]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Trigger pipeline ────────────────────────────────────────────────────
  const triggerPipeline = useCallback(async () => {
    setPipelineStatus("running");
    setPipelineMessage(null);
    setError(null);
    try {
      const result: PipelineRunResponse = await featuresApi.runPipeline({
        build_dataset: true,
      });
      setPipelineStatus("success");
      setPipelineMessage(result.message);
      // Refresh all data
      await loadVersions();
      loadFeatureStats(selectedTicker);
      loadLabelDistributions();
      loadSampleData(selectedTicker);
    } catch (err: unknown) {
      setPipelineStatus("failed");
      const msg = err instanceof Error ? err.message : "Pipeline failed";
      setPipelineMessage(msg);
      setError(msg);
    }
  }, [selectedTicker, loadVersions, loadFeatureStats, loadLabelDistributions, loadSampleData]);

  const hasFeatureData = (featureStats?.total_rows ?? 0) > 0;
  const hasLabelData   = labelDistributions.length > 0;
  const hasDataset     = datasetVersions.length > 0;

  return {
    // State
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
    // Loading flags
    isLoadingVersions,
    isLoadingStats,
    isLoadingLabels,
    isLoadingSample,
    // Derived
    hasFeatureData,
    hasLabelData,
    hasDataset,
    // Actions
    triggerPipeline,
    refresh: () => {
      loadVersions();
      loadFeatureStats(selectedTicker);
      loadLabelDistributions();
      loadSampleData(selectedTicker);
    },
  };
}
