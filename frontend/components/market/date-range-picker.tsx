"use client";

import { useState } from "react";
import { Calendar } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DatePreset } from "@/hooks/use-market-data";

interface DateRangePickerProps {
  activePreset: DatePreset | null;
  customRange: { start: string; end: string } | null;
  onPreset: (preset: DatePreset) => void;
  onCustom: (range: { start: string; end: string }) => void;
}

const PRESETS: DatePreset[] = ["1M", "3M", "6M", "1Y", "2Y", "5Y"];

export function DateRangePicker({
  activePreset,
  customRange,
  onPreset,
  onCustom,
}: DateRangePickerProps) {
  const [showCustom, setShowCustom] = useState(false);
  const [tmpStart, setTmpStart] = useState(customRange?.start ?? "");
  const [tmpEnd, setTmpEnd] = useState(customRange?.end ?? "");

  const applyCustom = () => {
    if (tmpStart && tmpEnd && tmpStart <= tmpEnd) {
      onCustom({ start: tmpStart, end: tmpEnd });
      setShowCustom(false);
    }
  };

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {PRESETS.map((p) => (
        <button
          key={p}
          onClick={() => { onPreset(p); setShowCustom(false); }}
          className={cn(
            "h-9 px-3 rounded-lg text-xs font-semibold transition-all border",
            activePreset === p && !customRange
              ? "bg-cyan-500/15 border-cyan-500/40 text-cyan-400"
              : "border-slate-700 text-slate-400 hover:text-slate-100 hover:border-slate-600 bg-slate-900"
          )}
        >
          {p}
        </button>
      ))}

      {/* Custom range toggle */}
      <button
        onClick={() => setShowCustom((s) => !s)}
        className={cn(
          "h-9 px-3 rounded-lg text-xs font-semibold transition-all border flex items-center gap-1.5",
          customRange
            ? "bg-cyan-500/15 border-cyan-500/40 text-cyan-400"
            : "border-slate-700 text-slate-400 hover:text-slate-100 hover:border-slate-600 bg-slate-900"
        )}
      >
        <Calendar className="w-3.5 h-3.5" />
        {customRange ? `${customRange.start} → ${customRange.end}` : "Custom"}
      </button>

      {showCustom && (
        <div className="flex items-center gap-2 mt-1 w-full sm:w-auto sm:mt-0">
          <input
            type="date"
            value={tmpStart}
            onChange={(e) => setTmpStart(e.target.value)}
            className="h-9 px-2 rounded-lg border border-slate-700 bg-slate-900 text-slate-100 text-xs outline-none focus:border-cyan-500/50"
          />
          <span className="text-slate-600 text-xs">to</span>
          <input
            type="date"
            value={tmpEnd}
            onChange={(e) => setTmpEnd(e.target.value)}
            className="h-9 px-2 rounded-lg border border-slate-700 bg-slate-900 text-slate-100 text-xs outline-none focus:border-cyan-500/50"
          />
          <button
            onClick={applyCustom}
            disabled={!tmpStart || !tmpEnd || tmpStart > tmpEnd}
            className="h-9 px-3 rounded-lg bg-cyan-500 text-slate-950 text-xs font-bold hover:bg-cyan-400 transition-colors disabled:opacity-40"
          >
            Apply
          </button>
        </div>
      )}
    </div>
  );
}
