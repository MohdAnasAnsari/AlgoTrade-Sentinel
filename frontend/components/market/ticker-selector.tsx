"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TickerInfo } from "@/lib/api";

interface TickerSelectorProps {
  tickers: TickerInfo[];
  selected: string;
  onChange: (ticker: string) => void;
  disabled?: boolean;
}

export function TickerSelector({ tickers, selected, onChange, disabled }: TickerSelectorProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = tickers.filter(
    (t) =>
      t.ticker.toLowerCase().includes(search.toLowerCase()) ||
      t.name.toLowerCase().includes(search.toLowerCase())
  );

  const selectedInfo = tickers.find((t) => t.ticker === selected);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch("");
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50);
  }, [open]);

  const select = (ticker: string) => {
    onChange(ticker);
    setOpen(false);
    setSearch("");
  };

  return (
    <div ref={ref} className="relative">
      <button
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "flex items-center gap-2 h-9 px-3 rounded-lg border border-slate-700",
          "bg-slate-900 text-slate-100 text-sm font-medium",
          "hover:border-slate-600 hover:bg-slate-800 transition-all",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          open && "border-cyan-500/50 ring-1 ring-cyan-500/20"
        )}
      >
        <span className="font-mono font-bold text-cyan-400">{selected}</span>
        {selectedInfo && (
          <span className="text-slate-400 text-xs hidden sm:inline truncate max-w-[100px]">
            {selectedInfo.name}
          </span>
        )}
        <ChevronDown
          className={cn("w-3.5 h-3.5 text-slate-500 transition-transform shrink-0", open && "rotate-180")}
        />
      </button>

      {open && (
        <div className="absolute top-11 left-0 z-50 w-72 rounded-xl border border-slate-700 bg-slate-900 shadow-2xl shadow-black/40">
          {/* Search */}
          <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-800">
            <Search className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <input
              ref={inputRef}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search ticker or name…"
              className="flex-1 bg-transparent text-sm text-slate-100 placeholder:text-slate-600 outline-none"
            />
          </div>
          {/* List */}
          <div className="max-h-64 overflow-y-auto py-1">
            {filtered.length === 0 ? (
              <p className="px-4 py-3 text-xs text-slate-500">No results</p>
            ) : (
              filtered.map((t) => (
                <button
                  key={t.ticker}
                  onClick={() => select(t.ticker)}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2 text-sm hover:bg-slate-800 transition-colors",
                    t.ticker === selected && "bg-slate-800"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono font-bold text-cyan-400 w-14 text-left">
                      {t.ticker}
                    </span>
                    <span className="text-slate-400 text-xs truncate">{t.name}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {t.last_close !== null && (
                      <span className="text-slate-300 text-xs font-medium">
                        ${t.last_close.toFixed(2)}
                      </span>
                    )}
                    {t.change_pct !== null && (
                      <span
                        className={cn(
                          "text-xs font-semibold",
                          t.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"
                        )}
                      >
                        {t.change_pct >= 0 ? "+" : ""}
                        {t.change_pct.toFixed(2)}%
                      </span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
