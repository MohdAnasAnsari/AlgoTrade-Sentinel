"use client";

import { cn } from "@/lib/utils";
import type { IndicatorState } from "@/hooks/use-market-data";

interface IndicatorControlsProps {
  indicators: IndicatorState;
  onChange: (next: IndicatorState) => void;
}

const BUTTONS: { key: keyof IndicatorState; label: string; color: string }[] = [
  { key: "sma20", label: "SMA 20", color: "text-orange-400 border-orange-500/40 bg-orange-500/10" },
  { key: "sma50", label: "SMA 50", color: "text-blue-400 border-blue-500/40 bg-blue-500/10" },
  { key: "ema20", label: "EMA 20", color: "text-purple-400 border-purple-500/40 bg-purple-500/10" },
  { key: "bb",    label: "BB",     color: "text-slate-300 border-slate-500/40 bg-slate-500/10" },
];

export function IndicatorControls({ indicators, onChange }: IndicatorControlsProps) {
  const toggle = (key: keyof IndicatorState) =>
    onChange({ ...indicators, [key]: !indicators[key] });

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {BUTTONS.map(({ key, label, color }) => (
        <button
          key={key}
          onClick={() => toggle(key)}
          className={cn(
            "h-9 px-3 rounded-lg text-xs font-semibold transition-all border",
            indicators[key]
              ? color
              : "border-slate-700 text-slate-500 bg-slate-900 hover:text-slate-300 hover:border-slate-600"
          )}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
