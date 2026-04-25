"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  BacktestDetail,
  BacktestJobStatus,
  BacktestSummary,
  ExperimentRun,
  StartBacktestRequest,
  backtestApi,
  experimentsApi,
} from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export function useBacktesting(_availableTickers: string[]) {
  const { pushToast } = useToast();
  const [modelRunId, setModelRunId] = useState<string>("");
  const [selectedTickers, setSelectedTickers] = useState<string[]>([]);
  const [startDate, setStartDate] = useState("2023-01-01");
  const [endDate, setEndDate] = useState("2024-12-31");
  const [initialCapital, setInitialCapital] = useState(100_000);
  const [transactionCost, setTransactionCost] = useState(0.001);
  const [slippage, setSlippage] = useState(0.0005);
  const [positionFrac, setPositionFrac] = useState(0.10);
  const [strategyName, setStrategyName] = useState("");

  const [experimentRuns, setExperimentRuns] = useState<ExperimentRun[]>([]);

  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<BacktestJobStatus | null>(null);
  const [starting, setStarting] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [runs, setRuns] = useState<BacktestSummary[]>([]);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedRun, setSelectedRun] = useState<BacktestSummary | null>(null);
  const [runDetail, setRunDetail] = useState<BacktestDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    experimentsApi
      .list(100)
      .then((runsData) => setExperimentRuns(runsData.filter((run) => run.status === "FINISHED")))
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load experiment runs.");
      });
  }, []);

  const loadRuns = useCallback(async () => {
    setLoadingRuns(true);
    setError(null);
    try {
      const data = await backtestApi.listRuns();
      setRuns(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load backtest runs.");
    } finally {
      setLoadingRuns(false);
    }
  }, []);

  useEffect(() => {
    loadRuns();
  }, [loadRuns]);

  useEffect(() => {
    if (!selectedRun) {
      setRunDetail(null);
      return;
    }

    setLoadingDetail(true);
    backtestApi
      .getDetail(selectedRun.run_id)
      .then((detail) => {
        setRunDetail(detail);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load backtest detail.");
        setRunDetail(null);
      })
      .finally(() => setLoadingDetail(false));
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
        const status = await backtestApi.getStatus(jobId);
        setJobStatus(status);
        if (status.status !== "running") {
          stopPolling();
          setStarting(false);
          pushToast({
            title: status.status === "complete" ? "Backtest complete" : "Backtest failed",
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

  const startBacktest = useCallback(async () => {
    if (selectedTickers.length === 0) return;

    setStarting(true);
    setJobStatus(null);
    setError(null);
    try {
      const body: StartBacktestRequest = {
        model_run_id: modelRunId || null,
        tickers: selectedTickers,
        start_date: startDate,
        end_date: endDate,
        initial_capital: initialCapital,
        transaction_cost: transactionCost,
        slippage,
        position_frac: positionFrac,
        strategy_name: strategyName || null,
      };
      const response = await backtestApi.run(body);
      pushToast({
        title: "Backtest started",
        description: response.message,
        tone: "success",
      });
      setJobId(response.job_id);
      setJobStatus({
        job_id: response.job_id,
        status: "running",
        message: response.message,
        run_ids: [],
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setStarting(false);
      setError(message);
      setJobStatus({ job_id: "", status: "failed", message, run_ids: [] });
      pushToast({
        title: "Backtest failed",
        description: message,
        tone: "error",
      });
    }
  }, [
    modelRunId,
    selectedTickers,
    startDate,
    endDate,
    initialCapital,
    transactionCost,
    slippage,
    positionFrac,
    strategyName,
    pushToast,
  ]);

  const toggleTicker = useCallback((ticker: string) => {
    setSelectedTickers((prev) =>
      prev.includes(ticker) ? prev.filter((item) => item !== ticker) : [...prev, ticker]
    );
  }, []);

  const selectRun = useCallback((run: BacktestSummary | null) => {
    setSelectedRun(run);
  }, []);

  return {
    modelRunId,
    setModelRunId,
    selectedTickers,
    toggleTicker,
    setSelectedTickers,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    initialCapital,
    setInitialCapital,
    transactionCost,
    setTransactionCost,
    slippage,
    setSlippage,
    positionFrac,
    setPositionFrac,
    strategyName,
    setStrategyName,
    experimentRuns,
    starting,
    jobStatus,
    startBacktest,
    isRunning: jobStatus?.status === "running",
    runs,
    loadingRuns,
    loadRuns,
    error,
    selectedRun,
    selectRun,
    runDetail,
    loadingDetail,
  };
}
