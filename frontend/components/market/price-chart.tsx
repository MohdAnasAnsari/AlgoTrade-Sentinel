"use client";

import { useEffect, useRef } from "react";
import type { OHLCVRow } from "@/lib/api";
import { sma, ema, bollingerBands } from "@/lib/indicators";
import type { IndicatorState } from "@/hooks/use-market-data";

interface PriceChartProps {
  data: OHLCVRow[];
  indicators: IndicatorState;
}

export function PriceChart({ data, indicators }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    let cleanupFn: (() => void) | undefined;

    (async () => {
      const { createChart, CrosshairMode } = await import("lightweight-charts");

      if (!containerRef.current) return;

      const chart = createChart(containerRef.current, {
        width: containerRef.current.clientWidth,
        height: 380,
        layout: {
          background: { color: "transparent" },
          textColor: "#64748b",
        },
        grid: {
          vertLines: { color: "#1e293b" },
          horzLines: { color: "#1e293b" },
        },
        crosshair: { mode: CrosshairMode.Normal },
        rightPriceScale: {
          borderColor: "#1e293b",
          textColor: "#64748b",
        },
        timeScale: {
          borderColor: "#1e293b",
          timeVisible: true,
          secondsVisible: false,
        },
        handleScroll: true,
        handleScale: true,
      });

      // Candlestick series
      const candleSeries = chart.addCandlestickSeries({
        upColor: "#10b981",
        downColor: "#f43f5e",
        borderUpColor: "#10b981",
        borderDownColor: "#f43f5e",
        wickUpColor: "#10b981",
        wickDownColor: "#f43f5e",
      });

      candleSeries.setData(
        data
          .filter((d) => d.open != null && d.high != null && d.low != null && d.close != null)
          .map((d) => ({
            time: d.date as `${number}-${number}-${number}`,
            open: d.open!,
            high: d.high!,
            low: d.low!,
            close: d.close!,
          }))
      );

      const closes = data.map((d) => d.close ?? 0);
      const dates = data.map((d) => d.date as `${number}-${number}-${number}`);

      // SMA 20 (orange)
      if (indicators.sma20) {
        const s20 = sma(closes, 20);
        const lineSeries = chart.addLineSeries({
          color: "#f97316",
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        });
        lineSeries.setData(
          s20
            .map((v, i) => (v !== null ? { time: dates[i], value: v } : null))
            .filter(Boolean) as { time: `${number}-${number}-${number}`; value: number }[]
        );
      }

      // SMA 50 (blue)
      if (indicators.sma50) {
        const s50 = sma(closes, 50);
        const lineSeries = chart.addLineSeries({
          color: "#3b82f6",
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        });
        lineSeries.setData(
          s50
            .map((v, i) => (v !== null ? { time: dates[i], value: v } : null))
            .filter(Boolean) as { time: `${number}-${number}-${number}`; value: number }[]
        );
      }

      // EMA 20 (purple)
      if (indicators.ema20) {
        const e20 = ema(closes, 20);
        const lineSeries = chart.addLineSeries({
          color: "#a855f7",
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        });
        lineSeries.setData(
          e20
            .map((v, i) => (v !== null ? { time: dates[i], value: v } : null))
            .filter(Boolean) as { time: `${number}-${number}-${number}`; value: number }[]
        );
      }

      // Bollinger Bands (grey upper/lower + middle)
      if (indicators.bb) {
        const bb = bollingerBands(closes, 20, 2);

        const upper = chart.addLineSeries({
          color: "#475569",
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
          lineStyle: 2, // dashed
        });
        const lower = chart.addLineSeries({
          color: "#475569",
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
          lineStyle: 2,
        });
        const mid = chart.addLineSeries({
          color: "#64748b",
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        });

        type P = { time: `${number}-${number}-${number}`; value: number };
        const upperPts: P[] = [];
        const lowerPts: P[] = [];
        const midPts: P[] = [];

        bb.forEach((b, i) => {
          if (b.upper !== null && b.lower !== null && b.middle !== null) {
            upperPts.push({ time: dates[i], value: b.upper });
            lowerPts.push({ time: dates[i], value: b.lower });
            midPts.push({ time: dates[i], value: b.middle });
          }
        });

        upper.setData(upperPts);
        lower.setData(lowerPts);
        mid.setData(midPts);
      }

      // Fit content
      chart.timeScale().fitContent();

      // Responsive resize
      const ro = new ResizeObserver((entries) => {
        const w = entries[0]?.contentRect.width;
        if (w) chart.applyOptions({ width: w });
      });
      if (containerRef.current) ro.observe(containerRef.current);

      cleanupFn = () => {
        ro.disconnect();
        chart.remove();
      };
    })();

    return () => cleanupFn?.();
  }, [data, indicators]);

  if (data.length === 0) {
    return (
      <div className="h-[380px] flex items-center justify-center text-slate-500 text-sm">
        No price data available
      </div>
    );
  }

  return <div ref={containerRef} className="w-full" style={{ height: 380 }} />;
}
