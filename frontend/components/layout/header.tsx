"use client";

import { usePathname } from "next/navigation";
import { Bell } from "lucide-react";
import { ThemeToggle } from "@/components/shared/theme-toggle";

const BREADCRUMB_MAP: Record<string, string[]> = {
  "/": ["Overview", "Dashboard"],
  "/dashboard": ["Overview", "Dashboard"],
  "/market-explorer": ["Research", "Market Explorer"],
  "/strategy-lab": ["Research", "Strategy Lab"],
  "/training-lab": ["ML", "Training Lab"],
  "/model-registry": ["ML", "Model Registry"],
  "/backtesting": ["Trading", "Backtesting Center"],
  "/backtesting-center": ["Trading", "Backtesting Center"],
  "/signal-center": ["Trading", "Signal Center"],
  "/paper-portfolio": ["Trading", "Paper Portfolio"],
  "/monitoring": ["Ops", "Monitoring Center"],
  "/monitoring-center": ["Ops", "Monitoring Center"],
  "/settings": ["System", "Admin Settings"],
  "/admin-settings": ["System", "Admin Settings"],
  "/help": ["System", "Help / Docs"],
  "/help-docs": ["System", "Help / Docs"],
};

export function Header() {
  const pathname = usePathname();
  const crumbs = BREADCRUMB_MAP[pathname] ?? ["AlgoTrade Sentinel"];

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-sm flex items-center justify-between px-6 shrink-0">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm" aria-label="Breadcrumb">
        <span className="text-xs font-semibold text-cyan-500 uppercase tracking-widest mr-1">
          ATS
        </span>
        {crumbs.map((crumb, i) => (
          <span key={crumb} className="flex items-center gap-1.5">
            <span className="text-slate-700">/</span>
            <span
              className={
                i === crumbs.length - 1
                  ? "text-slate-100 font-medium"
                  : "text-slate-500"
              }
            >
              {crumb}
            </span>
          </span>
        ))}
      </nav>

      {/* Right Actions */}
      <div className="flex items-center gap-1">
        <button
          className="relative w-9 h-9 rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-cyan-400 ring-2 ring-slate-950" />
        </button>
        <ThemeToggle />
        <div className="ml-2 w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-[11px] font-bold text-white shrink-0">
          AT
        </div>
      </div>
    </header>
  );
}
