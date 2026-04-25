"use client";

import { AlertCircle, Download, Loader2, RefreshCw } from "lucide-react";
import { useMarketData } from "@/hooks/use-market-data";
import { TickerSelector } from "@/components/market/ticker-selector";
import { DateRangePicker } from "@/components/market/date-range-picker";
import { IndicatorControls } from "@/components/market/indicator-controls";
import { FreshnessBadge } from "@/components/market/freshness-badge";
import { StatsBar } from "@/components/market/stats-bar";
import { PriceChart } from "@/components/market/price-chart";
import { VolumeChart } from "@/components/market/volume-chart";
import { OHLCVTable } from "@/components/market/ohlcv-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export default function MarketExplorerPage() {
  const {
    tickers,
    selectedTicker,
    setSelectedTicker,
    ohlcv,
    stats,
    datePreset,
    setDatePreset,
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
  } = useMarketData();

  const selectedInfo = tickers.find((t) => t.ticker === selectedTicker);
  const freshnessStatus = selectedInfo?.freshness;
  const hasData = ohlcv.length > 0;
  const noData = !isLoadingOHLCV && !hasData;

  return (
    <div className="flex flex-col gap-4">
      {/* ------------------------------------------------------------------ */}
      {/* Header                                                               */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Market Explorer</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Real-time OHLCV data with technical indicator overlays.
          </p>
        </div>

        {/* Ingest button */}
        <button
          onClick={triggerIngest}
          disabled={isIngesting}
          className={cn(
            "flex items-center gap-2 h-9 px-4 rounded-lg text-sm font-semibold transition-all",
            "bg-cyan-500/10 border border-cyan-500/30 text-cyan-400",
            "hover:bg-cyan-500/20 hover:border-cyan-500/50",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        >
          {isIngesting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Download className="w-4 h-4" />
          )}
          {isIngesting ? "Ingesting…" : "Refresh Data"}
        </button>
      </div>

      {/* Ingest result toast */}
      {ingestResult && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
          <RefreshCw className="w-4 h-4 shrink-0" />
          {ingestResult}
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Controls Row                                                         */}
      {/* ------------------------------------------------------------------ */}
      <Card className="bg-slate-900 border-slate-800">
        <CardContent className="pt-4 pb-4">
          <div className="flex items-center gap-3 flex-wrap">
            {/* Ticker */}
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

            {/* Date presets */}
            <DateRangePicker
              activePreset={customRange ? null : datePreset}
              customRange={customRange}
              onPreset={setDatePreset}
              onCustom={setCustomRange}
            />

            <div className="w-px h-6 bg-slate-800 hidden lg:block" />

            {/* Indicators */}
            <IndicatorControls indicators={indicators} onChange={setIndicators} />

            <div className="ml-auto flex items-center gap-2">
              <FreshnessBadge
                status={freshnessStatus}
                lastDate={selectedInfo?.last_date}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ------------------------------------------------------------------ */}
      {/* Stats Bar                                                            */}
      {/* ------------------------------------------------------------------ */}
      <StatsBar ticker={selectedTicker} stats={stats} isLoading={isLoadingOHLCV} />

      {/* ------------------------------------------------------------------ */}
      {/* Charts                                                               */}
      {/* ------------------------------------------------------------------ */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <span className="font-mono text-cyan-400">{selectedTicker}</span>
              <span className="text-slate-500 font-normal">· Price Chart</span>
            </CardTitle>
            <span className="text-xs text-slate-500">
              {ohlcv.length > 0 &&
                `${dateRange.start} → ${dateRange.end} · ${ohlcv.length} bars`}
            </span>
          </div>
        </CardHeader>
        <CardContent className="pt-2">
          {isLoadingOHLCV ? (
            <Skeleton className="w-full bg-slate-800 rounded-lg" style={{ height: 380 }} />
          ) : noData ? (
            <NoDataState onIngest={triggerIngest} isIngesting={isIngesting} />
          ) : (
            <PriceChart data={ohlcv} indicators={indicators} />
          )}
        </CardContent>
      </Card>

      {/* Volume */}
      {!isLoadingOHLCV && hasData && (
        <Card className="bg-slate-900 border-slate-800">
          <CardContent className="pt-4 pb-2">
            <VolumeChart data={ohlcv} />
          </CardContent>
        </Card>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* OHLCV Table                                                          */}
      {/* ------------------------------------------------------------------ */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-semibold text-slate-100">
              OHLCV Data
            </CardTitle>
            {hasData && (
              <span className="text-xs text-slate-500">{ohlcv.length} rows</span>
            )}
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {isLoadingOHLCV ? (
            <div className="space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full bg-slate-800 rounded-lg" />
              ))}
            </div>
          ) : (
            <OHLCVTable data={ohlcv} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function NoDataState({
  onIngest,
  isIngesting,
}: {
  onIngest: () => void;
  isIngesting: boolean;
}) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-slate-700 bg-slate-800/20"
      style={{ height: 380 }}
    >
      <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center">
        <Download className="w-5 h-5 text-slate-400" />
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-slate-300">No market data yet</p>
        <p className="text-xs text-slate-500 mt-1">
          Click below to download historical OHLCV data for all watchlist tickers.
        </p>
      </div>
      <button
        onClick={onIngest}
        disabled={isIngesting}
        className="flex items-center gap-2 h-9 px-5 rounded-lg bg-cyan-500 text-slate-950 text-sm font-bold hover:bg-cyan-400 transition-colors disabled:opacity-50"
      >
        {isIngesting ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Download className="w-4 h-4" />
        )}
        {isIngesting ? "Downloading…" : "Download Market Data"}
      </button>
    </div>
  );
}
