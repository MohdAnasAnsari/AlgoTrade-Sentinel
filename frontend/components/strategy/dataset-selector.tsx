"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import type { DatasetVersion } from "@/lib/api";
import { cn } from "@/lib/utils";

interface DatasetSelectorProps {
  versions:  DatasetVersion[];
  selected:  number | null;
  onChange:  (version: number) => void;
}

export function DatasetSelector({ versions, selected, onChange }: DatasetSelectorProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handle(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, []);

  const current = versions.find((v) => v.version === selected);
  const label = current
    ? `v${current.version} · ${current.n_rows?.toLocaleString() ?? "?"} rows`
    : "No datasets";

  if (versions.length === 0) {
    return (
      <div className="h-9 px-3 rounded-lg border border-slate-700 bg-slate-900 text-slate-500 text-sm flex items-center">
        No datasets built
      </div>
    );
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "flex items-center gap-2 h-9 px-3 rounded-lg border text-sm transition-all min-w-[200px]",
          "bg-slate-900 border-slate-700 text-slate-200",
          "hover:border-slate-500 hover:bg-slate-800"
        )}
      >
        <span className="flex-1 text-left truncate">{label}</span>
        <ChevronDown className={cn("w-4 h-4 text-slate-400 shrink-0 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="absolute top-10 left-0 z-50 w-full min-w-[240px] bg-slate-900 border border-slate-700 rounded-xl shadow-xl overflow-hidden">
          {versions.map((v) => (
            <button
              key={v.version}
              onClick={() => { onChange(v.version); setOpen(false); }}
              className={cn(
                "w-full px-3 py-2.5 text-left text-sm hover:bg-slate-800 transition-colors",
                v.version === selected ? "text-cyan-400 bg-slate-800/60" : "text-slate-300"
              )}
            >
              <div className="font-semibold">Dataset v{v.version}</div>
              <div className="text-xs text-slate-500 mt-0.5">
                {v.n_rows?.toLocaleString()} rows · {v.tickers?.join(", ") ?? "—"}
                {v.date_range_start && ` · ${v.date_range_start}`}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
