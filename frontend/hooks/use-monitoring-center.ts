"use client";

import { useCallback, useEffect, useState } from "react";
import {
  monitoringApi,
  type DataDriftSummary,
  type FeatureDriftDetail,
  type ManualRetrainResponse,
  type MonitoringAlert,
  type MonitoringFreshnessReport,
  type MonitoringHistoryItem,
  type MonitoringPerformanceReport,
  type MonitoringSummary,
  type PredictionDriftReport,
  type RetrainHistoryItem,
} from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export function useMonitoringCenter() {
  const { pushToast } = useToast();
  const [summary, setSummary] = useState<MonitoringSummary | null>(null);
  const [history, setHistory] = useState<MonitoringHistoryItem[]>([]);
  const [dataDrift, setDataDrift] = useState<DataDriftSummary | null>(null);
  const [featureDrift, setFeatureDrift] = useState<FeatureDriftDetail[]>([]);
  const [predictionDrift, setPredictionDrift] = useState<PredictionDriftReport | null>(null);
  const [performance, setPerformance] = useState<MonitoringPerformanceReport | null>(null);
  const [freshness, setFreshness] = useState<MonitoringFreshnessReport | null>(null);
  const [alerts, setAlerts] = useState<MonitoringAlert[]>([]);
  const [retrainHistory, setRetrainHistory] = useState<RetrainHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isTriggeringRetrain, setIsTriggeringRetrain] = useState(false);
  const [retrainResult, setRetrainResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    if (mode === "initial") setIsLoading(true);
    else setIsRefreshing(true);

    try {
      setError(null);
      const latest = await monitoringApi.getLatest();
      setSummary(latest);

      const [
        historyData,
        dataDriftData,
        featureDriftData,
        predictionDriftData,
        performanceData,
        freshnessData,
        alertsData,
        retrainHistoryData,
      ] = await Promise.all([
        monitoringApi.getHistory(),
        monitoringApi.getDataDrift(),
        monitoringApi.getFeatureDrift(),
        monitoringApi.getPredictionDrift(),
        monitoringApi.getPerformance(),
        monitoringApi.getFreshness(),
        monitoringApi.getAlerts(),
        monitoringApi.getRetrainHistory(),
      ]);

      setHistory(historyData);
      setDataDrift(dataDriftData);
      setFeatureDrift(featureDriftData);
      setPredictionDrift(predictionDriftData);
      setPerformance(performanceData);
      setFreshness(freshnessData);
      setAlerts(alertsData);
      setRetrainHistory(retrainHistoryData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load monitoring data");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  const triggerRetraining = useCallback(
    async (reason = "Manual trigger from Monitoring Center"): Promise<ManualRetrainResponse> => {
      setIsTriggeringRetrain(true);
      try {
        setError(null);
        const result = await monitoringApi.triggerRetrain({ reason });
        setRetrainResult(
          result.promoted
            ? `Retraining completed and promoted model v${result.new_model_version ?? "?"}.`
            : `Retraining completed. ${result.notes ?? "Review retrain history for details."}`
        );
        pushToast({
          title: "Retraining complete",
          description: result.notes ?? "The retraining workflow finished.",
          tone: "success",
        });
        await fetchAll("refresh");
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Retraining failed";
        setError(message);
        pushToast({
          title: "Retraining failed",
          description: message,
          tone: "error",
        });
        throw err;
      } finally {
        setIsTriggeringRetrain(false);
      }
    },
    [fetchAll, pushToast]
  );

  useEffect(() => {
    void fetchAll("initial");
  }, [fetchAll]);

  return {
    summary,
    history,
    dataDrift,
    featureDrift,
    predictionDrift,
    performance,
    freshness,
    alerts,
    retrainHistory,
    isLoading,
    isRefreshing,
    isTriggeringRetrain,
    retrainResult,
    error,
    refetch: () => fetchAll("refresh"),
    triggerRetraining,
  };
}
