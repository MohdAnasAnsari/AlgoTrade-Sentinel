"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart2,
  Brain,
  Briefcase,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Database,
  FlaskConical,
  HelpCircle,
  LayoutDashboard,
  Settings,
  TrendingUp,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/hooks/use-sidebar";
import type { LucideIcon } from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

interface NavSection {
  section: string;
  items: NavItem[];
}

const navigation: NavSection[] = [
  {
    section: "Overview",
    items: [
      { label: "Dashboard", href: "/", icon: LayoutDashboard },
    ],
  },
  {
    section: "Research",
    items: [
      { label: "Market Explorer", href: "/market-explorer", icon: TrendingUp },
      { label: "Strategy Lab", href: "/strategy-lab", icon: FlaskConical },
    ],
  },
  {
    section: "ML",
    items: [
      { label: "Training Lab", href: "/training-lab", icon: Brain },
      { label: "Model Registry", href: "/model-registry", icon: Database },
    ],
  },
  {
    section: "Trading",
    items: [
      { label: "Backtesting Center", href: "/backtesting-center", icon: BarChart2 },
      { label: "Signal Center", href: "/signal-center", icon: Zap },
      { label: "Paper Portfolio", href: "/paper-portfolio", icon: Briefcase },
    ],
  },
  {
    section: "Ops",
    items: [
      { label: "Monitoring Center", href: "/monitoring-center", icon: Activity },
    ],
  },
  {
    section: "System",
    items: [
      { label: "Admin Settings", href: "/admin-settings", icon: Settings },
      { label: "Help / Docs", href: "/help-docs", icon: HelpCircle },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { collapsed, toggle, mounted } = useSidebar();

  return (
    <aside
      className={cn(
        "relative flex flex-col h-screen bg-slate-950 border-r border-slate-800/80 transition-all duration-300 ease-in-out shrink-0",
        mounted ? (collapsed ? "w-[64px]" : "w-[240px]") : "w-[240px]"
      )}
    >
      <div
        className={cn(
          "flex items-center h-16 border-b border-slate-800/80 px-4 gap-3 shrink-0 overflow-hidden",
          collapsed ? "justify-center px-0" : "justify-start"
        )}
      >
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shrink-0">
          <Cpu className="w-4 h-4 text-white" />
        </div>
        {!collapsed && (
          <div className="leading-tight">
            <span className="block text-sm font-bold text-white tracking-tight">
              AlgoTrade
            </span>
            <span className="block text-xs font-semibold text-cyan-400 tracking-widest uppercase">
              Sentinel
            </span>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto py-3 space-y-0.5">
        {navigation.map((group, gi) => (
          <div key={group.section} className={cn(gi > 0 ? "mt-3" : "")}>
            {!collapsed && (
              <p className="px-4 mb-1 text-[10px] font-semibold text-slate-500 uppercase tracking-widest">
                {group.section}
              </p>
            )}
            {collapsed && gi > 0 && (
              <div className="mx-3 my-2 border-t border-slate-800/60" />
            )}
            <div className="space-y-0.5 px-2">
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive =
                  pathname === item.href ||
                  pathname.startsWith(item.href + "/");
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={collapsed ? item.label : undefined}
                    className={cn(
                      "flex items-center rounded-lg text-sm transition-all duration-150 group relative",
                      collapsed
                        ? "justify-center h-10 w-10 mx-auto"
                        : "gap-3 px-3 py-2",
                      isActive
                        ? "bg-slate-800 text-cyan-400"
                        : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60"
                    )}
                  >
                    {isActive && (
                      <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-r-full bg-cyan-400" />
                    )}
                    <Icon
                      className={cn(
                        "shrink-0 transition-colors",
                        collapsed ? "w-5 h-5" : "w-4 h-4",
                        isActive
                          ? "text-cyan-400"
                          : "text-slate-400 group-hover:text-slate-100"
                      )}
                    />
                    {!collapsed && (
                      <span className="truncate font-medium">{item.label}</span>
                    )}
                    {isActive && !collapsed && (
                      <span className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0" />
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {!collapsed && (
        <div className="px-4 py-3 border-t border-slate-800/80">
          <span className="text-[10px] text-slate-600 font-mono">
            v0.1.0 Phase 10
          </span>
        </div>
      )}

      <button
        onClick={toggle}
        className={cn(
          "absolute -right-3 top-[72px] w-6 h-6 rounded-full bg-slate-800 border border-slate-700",
          "flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-700",
          "transition-all duration-150 z-10 shadow-md"
        )}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? (
          <ChevronRight className="w-3 h-3" />
        ) : (
          <ChevronLeft className="w-3 h-3" />
        )}
      </button>
    </aside>
  );
}
