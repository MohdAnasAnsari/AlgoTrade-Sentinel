"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  InferenceJobStatus,
  LatestSignal,
  RunInferenceRequest,
  SignalHistoryPoint,
  signalsApi,
} from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

type SignalFilter = "ALL" | "BUY" | "SELL" | "HOLD";

export function useSignalCenter() {
  const { pushToast } = useToast();
  const [latestSignals,  setLatestSignals]  = useState<LatestSignal[]>([]);
  const [signalFilter,   setSignalFilter]   = useState<SignalFilter>("ALL");
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [tickerHistory,  setTickerHistory]  = useState<SignalHistoryPoint[]>([]);
  const [loadingLatest,  setLoadingLatest]  = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error,          setError]          = useState<string | null>(null);

  // Inference job state
  const [jobId,      setJobId]      = useState<string | null>(null);
  const [jobStatus,  setJobStatus]  = useState<InferenceJobStatus | null>(null);
  const [starting,   setStarting]   = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Load latest signals ─────────────────────────────────────────────────
  const loadLatest = useCallback(async () => {
    setLoadingLatest(true);
    setError(null);
    try {
      const filter = signalFilter === "ALL" ? undefined : signalFilter;
      const data   = await signalsApi.getLatest(filter);
      setLatestSignals(data);
    } catch (e) {
      console.error("Failed to load latest signals", e);
      setError(e instanceof Error ? e.message : "Failed to load latest signals.");
    } finally {
      setLoadingLatest(false);
    }
  }, [signalFilter]);

  // ── Load ticker history ─────────────────────────────────────────────────
  const loadTickerHistory = useCallback(async (ticker: string) => {
    setLoadingHistory(true);
    setError(null);
    try {
      const data = await signalsApi.getHistory(ticker, 90);
      setTickerHistory(data);
    } catch (e) {
      console.error("Failed to load signal history", e);
      setError(e instanceof Error ? e.message : "Failed to load signal history.");
      setTickerHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  const selectTicker = useCallback((ticker: string | null) => {
    setSelectedTicker(ticker);
    if (ticker) loadTickerHistory(ticker);
    else setTickerHistory([]);
  }, [loadTickerHistory]);

  // ── Inference job ───────────────────────────────────────────────────────
  const startInference = useCallback(async (req?: Partial<RunInferenceRequest>) => {
    setStarting(true);
    setError(null);
    try {
      const resp = await signalsApi.runInference(req ?? {});
      pushToast({
        title: "Inference started",
        description: "A new inference job was queued successfully.",
        tone: "success",
      });
      setJobId(resp.job_id);
      setJobStatus({ job_id: resp.job_id, status: "running", message: resp.message,
                     total_signals: null, model_run_id: null, model_version: null, error: null });
    } catch (e) {
      console.error("Failed to start inference", e);
      setError(e instanceof Error ? e.message : "Failed to start inference.");
      pushToast({
        title: "Inference failed",
        description: e instanceof Error ? e.message : "Failed to start inference.",
        tone: "error",
      });
    } finally {
      setStarting(false);
    }
  }, [pushToast]);

  // ── Polling ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!jobId) return;
    const tick = async () => {
      try {
        const status = await signalsApi.getStatus(jobId);
        setJobStatus(status);
        if (status.status === "complete" || status.status === "failed") {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          if (status.status === "complete") {
            pushToast({
              title: "Inference complete",
              description: status.message,
              tone: "success",
            });
            loadLatest();
          } else {
            pushToast({
              title: "Inference failed",
              description: status.error ?? status.message,
              tone: "error",
            });
          }
        }
      } catch { /* ignore */ }
    };
    tick();
    pollRef.current = setInterval(tick, 5000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [jobId, loadLatest, pushToast]);

  // ── Filter change reloads latest ────────────────────────────────────────
  useEffect(() => { loadLatest(); }, [loadLatest]);

  const isRunning = jobStatus?.status === "running";

  return {
    latestSignals,
    signalFilter,
    setSignalFilter,
    selectedTicker,
    selectTicker,
    tickerHistory,
    loadingLatest,
    loadingHistory,
    loadLatest,
    startInference,
    starting,
    isRunning,
    jobStatus,
    error,
  };
}
