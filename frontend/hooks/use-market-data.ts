"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { format, subMonths, subYears } from "date-fns";
import { marketApi, type OHLCVRow, type TickerInfo, type TickerStats } from "@/lib/api";

export type DatePreset = "1M" | "3M" | "6M" | "1Y" | "2Y" | "5Y";

export interface IndicatorState {
  sma20: boolean;
  sma50: boolean;
  ema20: boolean;
  bb: boolean;
}

const today = () => format(new Date(), "yyyy-MM-dd");

function presetToStart(preset: DatePreset): string {
  const now = new Date();
  switch (preset) {
    case "1M": return format(subMonths(now, 1), "yyyy-MM-dd");
    case "3M": return format(subMonths(now, 3), "yyyy-MM-dd");
    case "6M": return format(subMonths(now, 6), "yyyy-MM-dd");
    case "1Y": return format(subYears(now, 1), "yyyy-MM-dd");
    case "2Y": return format(subYears(now, 2), "yyyy-MM-dd");
    case "5Y": return format(subYears(now, 5), "yyyy-MM-dd");
  }
}

export function useMarketData() {
  const [tickers, setTickers] = useState<TickerInfo[]>([]);
  const [selectedTicker, setSelectedTicker] = useState<string>("AAPL");
  const [ohlcv, setOhlcv] = useState<OHLCVRow[]>([]);
  const [stats, setStats] = useState<TickerStats | null>(null);
  const [datePreset, setDatePreset] = useState<DatePreset>("1Y");
  const [customRange, setCustomRange] = useState<{ start: string; end: string } | null>(null);
  const [indicators, setIndicators] = useState<IndicatorState>({
    sma20: true,
    sma50: true,
    ema20: false,
    bb: false,
  });
  const [isLoadingTickers, setIsLoadingTickers] = useState(true);
  const [isLoadingOHLCV, setIsLoadingOHLCV] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ingestResult, setIngestResult] = useState<string | null>(null);

  const dateRange = useMemo(() => {
    if (customRange) return customRange;
    return { start: presetToStart(datePreset), end: today() };
  }, [datePreset, customRange]);

  // ------------------------------------------------------------------
  // Fetch tickers list
  // ------------------------------------------------------------------
  const fetchTickers = useCallback(async () => {
    setIsLoadingTickers(true);
    try {
      const data = await marketApi.getTickers();
      setTickers(data);
    } catch {
      // Tickers endpoint may fail if no data yet — non-blocking
      setTickers([]);
    } finally {
      setIsLoadingTickers(false);
    }
  }, []);

  // ------------------------------------------------------------------
  // Fetch OHLCV + stats for selected ticker
  // ------------------------------------------------------------------
  const fetchOHLCV = useCallback(async () => {
    if (!selectedTicker) return;
    setIsLoadingOHLCV(true);
    setError(null);
    try {
      const [rows, statsData] = await Promise.all([
        marketApi.getOHLCV(selectedTicker, dateRange.start, dateRange.end),
        marketApi.getStats(selectedTicker),
      ]);
      setOhlcv(rows);
      setStats(statsData);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load data";
      // 404 = no data yet, show empty rather than error
      if (msg.includes("404")) {
        setOhlcv([]);
        setStats(null);
      } else {
        setError(msg);
      }
    } finally {
      setIsLoadingOHLCV(false);
    }
  }, [selectedTicker, dateRange]);

  // ------------------------------------------------------------------
  // Manual ingest trigger
  // ------------------------------------------------------------------
  const triggerIngest = useCallback(async () => {
    setIsIngesting(true);
    setIngestResult(null);
    setError(null);
    try {
      const res = await marketApi.triggerIngest();
      setIngestResult(res.message);
      await Promise.all([fetchTickers(), fetchOHLCV()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingestion failed");
    } finally {
      setIsIngesting(false);
    }
  }, [fetchTickers, fetchOHLCV]);

  // ------------------------------------------------------------------
  // Effects
  // ------------------------------------------------------------------
  useEffect(() => { fetchTickers(); }, [fetchTickers]);
  useEffect(() => { fetchOHLCV(); }, [fetchOHLCV]);

  return {
    tickers,
    selectedTicker,
    setSelectedTicker,
    ohlcv,
    stats,
    datePreset,
    setDatePreset: (p: DatePreset) => { setCustomRange(null); setDatePreset(p); },
    customRange,
    setCustomRange,
    dateRange,
    indicators,
    setIndicators,
    isLoadingTickers,
    isLoadingOHLCV,
    isIngesting,
    error,
    ingestResult,
    triggerIngest,
    refetch: fetchOHLCV,
  };
}
