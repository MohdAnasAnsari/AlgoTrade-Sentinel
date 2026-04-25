"use client";
import React from "react";

type Filter = "ALL" | "BUY" | "SELL" | "HOLD";

interface Props {
  active:   Filter;
  onChange: (f: Filter) => void;
  counts?:  Partial<Record<Filter, number>>;
}

const FILTERS: Filter[] = ["ALL", "BUY", "SELL", "HOLD"];

const COLOR: Record<Filter, string> = {
  ALL:  "border-cyan-500 text-cyan-300",
  BUY:  "border-emerald-500 text-emerald-300",
  SELL: "border-rose-500 text-rose-300",
  HOLD: "border-amber-500 text-amber-300",
};
const INACTIVE = "border-slate-700 text-slate-500 hover:border-slate-500 hover:text-slate-300";

export function SignalFilterBar({ active, onChange, counts }: Props) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {FILTERS.map((f) => (
        <button
          key={f}
          onClick={() => onChange(f)}
          className={`px-3 py-1 text-xs font-medium rounded-lg border transition-all ${
            active === f ? COLOR[f] + " bg-slate-800" : INACTIVE
          }`}
        >
          {f}
          {counts?.[f] != null && (
            <span className="ml-1.5 opacity-60">({counts[f]})</span>
          )}
        </button>
      ))}
    </div>
  );
}
