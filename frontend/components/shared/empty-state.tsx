import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { ArrowRight } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  action?: React.ReactNode;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  actionHref,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-[28px] border border-dashed border-slate-700/70 bg-slate-900/55 px-6 py-12 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-800/80">
        <Icon className="h-6 w-6 text-cyan-400" />
      </div>
      <h3 className="mt-5 text-lg font-semibold text-slate-100">{title}</h3>
      <p className="mt-2 max-w-md text-sm text-slate-400">{description}</p>
      {action ? (
        <div className="mt-5">{action}</div>
      ) : actionLabel && actionHref ? (
        <Link
          href={actionHref}
          className="mt-5 inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-200 transition hover:border-cyan-500/50 hover:text-white"
        >
          {actionLabel}
          <ArrowRight className="h-4 w-4" />
        </Link>
      ) : null}
    </div>
  );
}
