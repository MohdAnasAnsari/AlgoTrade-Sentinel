"use client";

import { CheckCircle2, Loader2, Play, XCircle } from "lucide-react";
import type { PipelineStatus } from "@/hooks/use-strategy-lab";
import { cn } from "@/lib/utils";

interface PipelineStatusBarProps {
  status:   PipelineStatus;
  message:  string | null;
  onRun:    () => void;
}

const STATUS_CONFIG = {
  idle:    { label: "Idle",    color: "text-slate-400",   dot: "bg-slate-600"  },
  running: { label: "Running", color: "text-cyan-400",    dot: "bg-cyan-400 animate-pulse" },
  success: { label: "Done",    color: "text-emerald-400", dot: "bg-emerald-400" },
  failed:  { label: "Failed",  color: "text-rose-400",    dot: "bg-rose-400"   },
} satisfies Record<PipelineStatus, { label: string; color: string; dot: string }>;

export function PipelineStatusBar({ status, message, onRun }: PipelineStatusBarProps) {
  const cfg      = STATUS_CONFIG[status];
  const running  = status === "running";

  return (
    <div className="flex items-center justify-between gap-4 flex-wrap">
      {/* Status indicator */}
      <div className="flex items-center gap-2">
        <span className={cn("w-2 h-2 rounded-full", cfg.dot)} />
        <span className={cn("text-xs font-semibold", cfg.color)}>
          Pipeline {cfg.label}
        </span>
        {message && (
          <span className="text-xs text-slate-500 max-w-[400px] truncate">
            · {message}
          </span>
        )}
      </div>

      {/* Run button */}
      <button
        onClick={onRun}
        disabled={running}
        className={cn(
          "flex items-center gap-2 h-9 px-4 rounded-lg text-sm font-semibold transition-all",
          "bg-cyan-500/10 border border-cyan-500/30 text-cyan-400",
          "hover:bg-cyan-500/20 hover:border-cyan-500/50",
          "disabled:opacity-50 disabled:cursor-not-allowed"
        )}
      >
        {running ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : status === "success" ? (
          <CheckCircle2 className="w-4 h-4" />
        ) : status === "failed" ? (
          <XCircle className="w-4 h-4" />
        ) : (
          <Play className="w-4 h-4" />
        )}
        {running ? "Running Pipeline…" : "Run Feature Pipeline"}
      </button>
    </div>
  );
}
