import { cn } from "@/lib/utils";

interface FreshnessBadgeProps {
  status: "fresh" | "stale" | "missing" | undefined;
  lastDate?: string | null;
  className?: string;
}

const CONFIG = {
  fresh: {
    dot: "bg-emerald-400",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
    bg: "bg-emerald-500/10",
    label: "Live",
  },
  stale: {
    dot: "bg-amber-400 animate-pulse",
    text: "text-amber-400",
    border: "border-amber-500/30",
    bg: "bg-amber-500/10",
    label: "Stale",
  },
  missing: {
    dot: "bg-rose-400",
    text: "text-rose-400",
    border: "border-rose-500/30",
    bg: "bg-rose-500/10",
    label: "No Data",
  },
};

export function FreshnessBadge({ status, lastDate, className }: FreshnessBadgeProps) {
  const cfg = CONFIG[status ?? "missing"];
  return (
    <div
      className={cn(
        "flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium",
        cfg.bg,
        cfg.border,
        cfg.text,
        className
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full shrink-0", cfg.dot)} />
      <span>{cfg.label}</span>
      {lastDate && (
        <span className="text-slate-500 font-normal hidden sm:inline">· {lastDate}</span>
      )}
    </div>
  );
}
