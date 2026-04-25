"use client";

import { Activity, BriefcaseBusiness, BrainCircuit, DollarSign, RefreshCcw, Siren, Zap } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { PageHeader } from "@/components/shared/page-header";
import { useDashboard } from "@/hooks/use-dashboard";
import { formatCompactNumber, formatCurrency, formatDate, formatDateTime, formatPercent } from "@/lib/format";

const SIGNAL_COLORS: Record<string, string> = {
  BUY: "#34d399",
  SELL: "#fb7185",
  HOLD: "#38bdf8",
};

const STATUS_STYLES: Record<string, string> = {
  HEALTHY: "border-emerald-500/25 bg-emerald-500/10 text-emerald-300",
  WARNING: "border-amber-500/25 bg-amber-500/10 text-amber-300",
  CRITICAL: "border-rose-500/25 bg-rose-500/10 text-rose-300",
  healthy: "border-emerald-500/25 bg-emerald-500/10 text-emerald-300",
  warning: "border-amber-500/25 bg-amber-500/10 text-amber-300",
  critical: "border-rose-500/25 bg-rose-500/10 text-rose-300",
  idle: "border-slate-700 bg-slate-800 text-slate-300",
};

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, index) => (
          <Card key={index} className="border-slate-800 bg-slate-900">
            <CardHeader className="p-4">
              <Skeleton className="h-4 w-24 bg-slate-800" />
            </CardHeader>
            <CardContent className="space-y-2 p-4 pt-0">
              <Skeleton className="h-8 w-28 bg-slate-800" />
              <Skeleton className="h-3 w-20 bg-slate-800" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Skeleton className="h-[360px] rounded-[24px] bg-slate-900" />
        <Skeleton className="h-[360px] rounded-[24px] bg-slate-900" />
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <Skeleton className="h-[320px] rounded-[24px] bg-slate-900" />
        <Skeleton className="h-[320px] rounded-[24px] bg-slate-900" />
      </div>
    </div>
  );
}

export function DashboardHome() {
  const { overview, isLoading, isRefreshing, error, refresh } = useDashboard();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (!overview) {
    return <ErrorState message={error ?? "Dashboard data is unavailable."} onRetry={() => refresh()} />;
  }

  const summaryCards = [
    {
      label: "Portfolio Value",
      value: formatCurrency(overview.portfolio.total_value),
      subtext: formatPercent(overview.portfolio.daily_change_pct),
      icon: DollarSign,
    },
    {
      label: "Today's Signals",
      value: `${overview.signals_today.BUY ?? 0} | ${overview.signals_today.SELL ?? 0} | ${overview.signals_today.HOLD ?? 0}`,
      subtext: "BUY | SELL | HOLD",
      icon: Zap,
    },
    {
      label: "Open Positions",
      value: String(overview.open_positions_count),
      subtext: "Live paper trades",
      icon: BriefcaseBusiness,
    },
    {
      label: "Total PnL",
      value: formatCurrency(overview.portfolio.total_pnl),
      subtext: formatPercent(overview.portfolio.total_pnl_pct),
      icon: Activity,
    },
    {
      label: "Champion Model F1",
      value: overview.model_performance.champion_f1?.toFixed(4) ?? "—",
      subtext: overview.model_performance.champion_model_version
        ? `v${overview.model_performance.champion_model_version}`
        : "No champion registered",
      icon: BrainCircuit,
    },
    {
      label: "Monitoring Status",
      value: overview.monitoring_status,
      subtext: "Latest health signal",
      icon: Siren,
      badge: overview.monitoring_status,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        subtitle="Portfolio, signals, watchlist momentum, and pipeline health in one live operational view."
        actions={
          <Button
            variant="outline"
            className="border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800"
            onClick={() => refresh()}
            disabled={isRefreshing}
          >
            <RefreshCcw className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        }
      />

      {error ? <ErrorState message={error} onRetry={() => refresh()} /> : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        {summaryCards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.label} className="border-slate-800 bg-slate-900">
              <CardHeader className="flex flex-row items-center justify-between p-4 pb-2">
                <p className="text-sm text-slate-400">{card.label}</p>
                <Icon className="h-4 w-4 text-cyan-400" />
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <div className="flex items-center gap-2">
                  <p className="text-2xl font-semibold text-slate-100">{card.value}</p>
                  {card.badge ? (
                    <Badge className={STATUS_STYLES[card.badge] ?? "border-slate-700 bg-slate-800 text-slate-200"}>
                      {card.badge}
                    </Badge>
                  ) : null}
                </div>
                <p className="mt-1 text-xs text-slate-500">{card.subtext}</p>
              </CardContent>
            </Card>
          );
        })}
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100">Portfolio Value</CardTitle>
            <p className="text-sm text-slate-400">
              30-day simulated portfolio value versus initial capital of {formatCurrency(overview.portfolio.initial_capital)}.
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={overview.portfolio_history}>
                <defs>
                  <linearGradient id="portfolioFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.32} />
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                <XAxis
                  dataKey="snapshot_date"
                  tickFormatter={(value) => formatDate(value, "MMM dd")}
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tickFormatter={(value) => formatCompactNumber(value)}
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: "#020617", border: "1px solid #1e293b", borderRadius: 16 }}
                  formatter={(value: number) => [formatCurrency(value), "Portfolio"]}
                  labelFormatter={(value) => formatDate(value)}
                />
                <Area type="monotone" dataKey="total_value" stroke="#38bdf8" fill="url(#portfolioFill)" strokeWidth={2.5} />
                <Line type="monotone" dataKey={() => overview.portfolio.initial_capital} stroke="#64748b" dot={false} strokeDasharray="6 4" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100">Market Overview</CardTitle>
            <p className="text-sm text-slate-400">1-month price action for the lead watchlist names.</p>
          </CardHeader>
          <CardContent className="space-y-4">
            {overview.market_overview.length === 0 ? (
              <EmptyState
                icon={Activity}
                title="No watchlist data yet"
                description="Add tickers or ingest market data to populate the sparkline overview."
                actionLabel="Open Admin Settings"
                actionHref="/admin-settings"
              />
            ) : (
              overview.market_overview.map((ticker) => (
                <div key={ticker.ticker} className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-100">{ticker.ticker}</p>
                      <p className="text-xs text-slate-500">{ticker.company_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-slate-100">{formatCurrency(ticker.current_price)}</p>
                      <p className={`text-xs ${ticker.change_pct && ticker.change_pct >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
                        {formatPercent(ticker.change_pct)}
                      </p>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={72}>
                    <LineChart data={ticker.points}>
                      <Tooltip
                        contentStyle={{ backgroundColor: "#020617", border: "1px solid #1e293b", borderRadius: 14 }}
                        formatter={(value: number) => [formatCurrency(value), ticker.ticker]}
                        labelFormatter={(value) => formatDate(value)}
                      />
                      <Line type="monotone" dataKey="close" stroke="#f59e0b" strokeWidth={2.2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100">Latest Signals</CardTitle>
            <p className="text-sm text-slate-400">The ten most recent signal events available to the platform.</p>
          </CardHeader>
          <CardContent className="space-y-3">
            {overview.latest_signals.length === 0 ? (
              <EmptyState
                icon={Zap}
                title="No signals yet"
                description="Run inference or use the demo setup script to populate the live signal feed."
                actionLabel="Go To Signal Center"
                actionHref="/signal-center"
              />
            ) : (
              overview.latest_signals.map((signal) => (
                <div key={`${signal.ticker}-${signal.signal_date}`} className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-slate-100">{signal.ticker}</p>
                      <Badge
                        className="border-0"
                        style={{ backgroundColor: `${SIGNAL_COLORS[signal.signal] ?? "#64748b"}22`, color: SIGNAL_COLORS[signal.signal] ?? "#cbd5e1" }}
                      >
                        {signal.signal}
                      </Badge>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">{formatDateTime(signal.created_at ?? signal.signal_date)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-slate-100">
                      {signal.confidence == null ? "—" : formatPercent(signal.confidence * 100)}
                    </p>
                    <p className="text-xs text-slate-500">confidence</p>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100">Recent Alerts</CardTitle>
            <p className="text-sm text-slate-400">Operational and trading alerts raised by the platform.</p>
          </CardHeader>
          <CardContent className="space-y-3">
            {overview.recent_alerts.length === 0 ? (
              <EmptyState
                icon={Siren}
                title="No alerts yet"
                description="Alerts will appear here when fresh signals, drift, or portfolio events are detected."
                actionLabel="View Monitoring"
                actionHref="/monitoring-center"
              />
            ) : (
              overview.recent_alerts.map((alert) => (
                <div key={alert.id} className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <Badge className={STATUS_STYLES[alert.severity] ?? "border-slate-700 bg-slate-800 text-slate-200"}>
                        {alert.severity}
                      </Badge>
                      <p className="mt-3 text-sm text-slate-200">{alert.message}</p>
                    </div>
                    <span className="text-xs text-slate-500">{formatDateTime(alert.created_at)}</span>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100">Pipeline Status</CardTitle>
            <p className="text-sm text-slate-400">Last observed status for the daily ingest, feature, inference, and monitoring jobs.</p>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            {overview.pipeline_status.map((pipeline) => (
              <div key={pipeline.key} className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium text-slate-100">{pipeline.label}</p>
                  <Badge className={STATUS_STYLES[pipeline.status] ?? "border-slate-700 bg-slate-800 text-slate-200"}>
                    {pipeline.status}
                  </Badge>
                </div>
                <p className="mt-3 text-sm text-slate-400">{pipeline.description}</p>
                <p className="mt-2 text-xs text-slate-500">Last run: {formatDateTime(pipeline.last_run_at)}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100">Model Performance</CardTitle>
            <p className="text-sm text-slate-400">Champion model and the most recent monitored F1 snapshot.</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Champion Model</p>
              <p className="mt-2 text-xl font-semibold text-slate-100">
                {overview.model_performance.champion_model_name ?? "No registered model"}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                {overview.model_performance.champion_model_version
                  ? `Version ${overview.model_performance.champion_model_version}`
                  : "Waiting for model registry promotion"}
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                <p className="text-xs text-slate-500">Champion F1</p>
                <p className="mt-2 text-xl font-semibold text-slate-100">
                  {overview.model_performance.champion_f1?.toFixed(4) ?? "—"}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                <p className="text-xs text-slate-500">Current F1</p>
                <p className="mt-2 text-xl font-semibold text-slate-100">
                  {overview.model_performance.current_f1?.toFixed(4) ?? "—"}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                <p className="text-xs text-slate-500">Days Since Training</p>
                <p className="mt-2 text-xl font-semibold text-slate-100">
                  {overview.model_performance.days_since_last_training ?? "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
