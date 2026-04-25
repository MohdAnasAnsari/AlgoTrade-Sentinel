"use client";

import { useEffect, useMemo, useState } from "react";
import { format, formatDistanceToNow } from "date-fns";
import {
  AlertTriangle,
  Gauge,
  RefreshCcw,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Siren,
  Sparkles,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { FeatureDriftTable } from "@/components/monitoring/feature-drift-table";
import { RetrainConfirmModal } from "@/components/monitoring/retrain-confirm-modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useMonitoringCenter } from "@/hooks/use-monitoring-center";
import type { MonitoringAlert } from "@/lib/api";

const STATUS_STYLES = {
  HEALTHY: {
    label: "HEALTHY",
    badge: "border border-emerald-500/25 bg-emerald-500/10 text-emerald-300",
    accent: "#34d399",
    panel: "from-emerald-500/12 via-emerald-500/5 to-transparent",
    icon: ShieldCheck,
  },
  WARNING: {
    label: "WARNING",
    badge: "border border-amber-500/25 bg-amber-500/10 text-amber-300",
    accent: "#fbbf24",
    panel: "from-amber-500/12 via-amber-500/5 to-transparent",
    icon: ShieldAlert,
  },
  CRITICAL: {
    label: "CRITICAL",
    badge: "border border-rose-500/25 bg-rose-500/10 text-rose-300",
    accent: "#fb7185",
    panel: "from-rose-500/12 via-rose-500/5 to-transparent",
    icon: ShieldX,
  },
} as const;

function fmtPct(value: number | null | undefined, digits = 1) {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(digits)}%`;
}

function fmtMaybeDate(value: string | null | undefined) {
  if (!value) return "—";
  try {
    return format(new Date(value), "dd MMM yyyy, HH:mm");
  } catch {
    return value;
  }
}

function relativeTime(value: string | null | undefined) {
  if (!value) return "—";
  try {
    return formatDistanceToNow(new Date(value), { addSuffix: true });
  } catch {
    return value;
  }
}

function alertDismissKey(alert: MonitoringAlert) {
  return `${alert.id}:${alert.timestamp}`;
}

export default function MonitoringCenterPage() {
  const {
    summary,
    history,
    dataDrift,
    featureDrift,
    predictionDrift,
    performance,
    freshness,
    alerts,
    retrainHistory,
    isLoading,
    isRefreshing,
    isTriggeringRetrain,
    retrainResult,
    error,
    refetch,
    triggerRetraining,
  } = useMonitoringCenter();

  const [showRetrainModal, setShowRetrainModal] = useState(false);
  const [dismissedAlerts, setDismissedAlerts] = useState<string[]>([]);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem("ats-monitoring-dismissed-alerts");
      if (raw) setDismissedAlerts(JSON.parse(raw));
    } catch {
      // Ignore localStorage issues.
    }
  }, []);

  const visibleAlerts = useMemo(
    () => alerts.filter((alert) => !dismissedAlerts.includes(alertDismissKey(alert))),
    [alerts, dismissedAlerts]
  );

  const status = summary?.system_status ?? "HEALTHY";
  const statusStyle = STATUS_STYLES[status];
  const StatusIcon = statusStyle.icon;

  const driftTrendData = history.map((item) => ({
    date: format(new Date(item.report_date), "dd MMM"),
    drift_share: item.drift_share ?? 0,
  }));

  const predictionChartData = predictionDrift
    ? [
        {
          window: "Reference",
          BUY: Math.round((predictionDrift.reference_ratios.BUY ?? 0) * 100),
          SELL: Math.round((predictionDrift.reference_ratios.SELL ?? 0) * 100),
          HOLD: Math.round((predictionDrift.reference_ratios.HOLD ?? 0) * 100),
        },
        {
          window: "Current",
          BUY: Math.round((predictionDrift.current_ratios.BUY ?? 0) * 100),
          SELL: Math.round((predictionDrift.current_ratios.SELL ?? 0) * 100),
          HOLD: Math.round((predictionDrift.current_ratios.HOLD ?? 0) * 100),
        },
      ]
    : [];

  const latestRetrain = retrainHistory[0] ?? null;

  function dismissAlert(alert: MonitoringAlert) {
    const next = [...dismissedAlerts, alertDismissKey(alert)];
    setDismissedAlerts(next);
    try {
      window.localStorage.setItem("ats-monitoring-dismissed-alerts", JSON.stringify(next));
    } catch {
      // Ignore localStorage issues.
    }
  }

  async function handleManualRetrain() {
    try {
      await triggerRetraining("Manual trigger from Monitoring Center");
      setShowRetrainModal(false);
    } catch {
      // Error state is handled by the hook.
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-900 px-5 py-4 text-slate-300">
          <RefreshCcw className="h-4 w-4 animate-spin text-cyan-400" />
          Loading monitoring center...
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Monitoring Center</h1>
          <p className="mt-1 text-sm text-slate-400">
            Daily drift monitoring, live model health, data freshness, and automated retraining controls.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge className="border border-slate-700 bg-slate-900 text-slate-300">
            Updated {relativeTime(summary?.created_at)}
          </Badge>
          <Button
            variant="outline"
            className="border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800"
            onClick={refetch}
            disabled={isRefreshing}
          >
            <RefreshCcw className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/8 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      {retrainResult && (
        <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/8 px-4 py-3 text-sm text-cyan-100">
          {retrainResult}
        </div>
      )}

      <section
        className={`relative overflow-hidden rounded-[28px] border border-slate-800 bg-gradient-to-br ${statusStyle.panel}`}
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.08),transparent_35%)]" />
        <div className="relative grid gap-5 px-6 py-6 lg:grid-cols-[1.4fr_0.9fr]">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <div
                className="flex h-12 w-12 items-center justify-center rounded-2xl"
                style={{ backgroundColor: `${statusStyle.accent}18`, color: statusStyle.accent }}
              >
                <StatusIcon className="h-6 w-6" />
              </div>
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-semibold text-slate-100">System Health</h2>
                  <Badge className={statusStyle.badge}>{statusStyle.label}</Badge>
                </div>
                <p className="mt-1 text-sm text-slate-400">
                  Drift, prediction mix, performance, and ingestion freshness are rolled into one operational status.
                </p>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {[
                {
                  label: "Drift Share",
                  value: fmtPct(summary?.drift_share, 2),
                  subtext: `${summary?.drifted_count ?? 0} / ${summary?.feature_count ?? 0} features`,
                },
                {
                  label: "Active Alerts",
                  value: String(summary?.active_alerts ?? 0),
                  subtext: predictionDrift?.detected ? "Prediction drift active" : "No prediction mix alert",
                },
                {
                  label: "Last Retrain",
                  value: latestRetrain ? relativeTime(latestRetrain.triggered_at) : "—",
                  subtext: latestRetrain?.trigger_reason ?? "No retraining logged",
                },
              ].map((item) => (
                <div key={item.label} className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{item.label}</p>
                  <p className="mt-2 text-2xl font-semibold text-slate-100">{item.value}</p>
                  <p className="mt-1 text-xs text-slate-500">{item.subtext}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[24px] border border-slate-800 bg-slate-950/70 p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Operational Snapshot</p>
                <p className="mt-2 text-sm text-slate-400">
                  {summary?.alert_level === "CRITICAL"
                    ? "At least one critical signal needs immediate action."
                    : summary?.alert_level === "WARN"
                    ? "Thresholds are being crossed and should be reviewed."
                    : "The monitoring stack is operating within expected limits."}
                </p>
              </div>
              <Sparkles className="h-5 w-5 text-cyan-400" />
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs text-slate-500">Latest Report Date</p>
                <p className="mt-2 text-lg font-semibold text-slate-100">
                  {summary?.report_date ? format(new Date(summary.report_date), "dd MMM yyyy") : "—"}
                </p>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs text-slate-500">Performance F1</p>
                <p className="mt-2 text-lg font-semibold text-slate-100">
                  {summary?.model_perf_f1 == null ? "—" : summary.model_perf_f1.toFixed(4)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Siren className="h-4 w-4 text-cyan-400" />
          <h2 className="text-lg font-semibold text-slate-100">Active Alerts</h2>
        </div>
        {visibleAlerts.length === 0 ? (
          <div className="rounded-2xl border border-emerald-500/15 bg-emerald-500/6 px-5 py-4 text-sm text-emerald-200">
            No active alerts are currently visible. Dismissed alerts stay hidden in this browser.
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-3">
            {visibleAlerts.map((alert) => {
              const tone =
                alert.severity === "CRITICAL"
                  ? "border-rose-500/20 bg-rose-500/8"
                  : "border-amber-500/20 bg-amber-500/8";
              return (
                <div key={alertDismissKey(alert)} className={`rounded-2xl border px-5 py-4 ${tone}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge
                          className={
                            alert.severity === "CRITICAL"
                              ? "border border-rose-500/25 bg-rose-500/10 text-rose-300"
                              : "border border-amber-500/25 bg-amber-500/10 text-amber-300"
                          }
                        >
                          {alert.severity}
                        </Badge>
                        <span className="text-xs text-slate-500">{relativeTime(alert.timestamp)}</span>
                      </div>
                      <h3 className="mt-3 text-base font-semibold text-slate-100">{alert.title}</h3>
                      <p className="mt-2 text-sm text-slate-300">{alert.description}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => dismissAlert(alert)}
                      className="text-xs text-slate-500 transition-colors hover:text-slate-200"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="flex flex-row items-start justify-between pb-3">
            <div>
              <CardTitle className="text-slate-100">Drift Overview</CardTitle>
              <p className="mt-2 text-sm text-slate-400">{dataDrift?.summary_text ?? "No drift report yet."}</p>
            </div>
            <Gauge className="h-5 w-5 text-cyan-400" />
          </CardHeader>
          <CardContent className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="relative mx-auto flex h-[240px] w-full max-w-[280px] items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart
                  data={[{ name: "Drift Share", value: summary?.drift_share ?? 0, fill: statusStyle.accent }]}
                  innerRadius="68%"
                  outerRadius="100%"
                  startAngle={210}
                  endAngle={-30}
                  barSize={18}
                >
                  <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                  <RadialBar background dataKey="value" cornerRadius={18} />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-4xl font-bold text-slate-100">{Math.round(summary?.drift_share ?? 0)}%</span>
                <span className="mt-1 text-xs uppercase tracking-[0.22em] text-slate-500">Drift Share</span>
              </div>
            </div>

            <div>
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Trend</p>
                  <p className="mt-1 text-sm text-slate-300">Daily drift share over the latest reports.</p>
                </div>
                <Badge className="border border-slate-700 bg-slate-950 text-slate-300">
                  {summary?.drifted_count ?? 0} of {summary?.feature_count ?? 0}
                </Badge>
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={driftTrendData} margin={{ left: -18, right: 12, top: 10, bottom: 0 }}>
                  <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
                  <YAxis
                    tick={{ fill: "#64748b", fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    domain={[0, 100]}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#020617",
                      border: "1px solid #1e293b",
                      borderRadius: "12px",
                    }}
                    formatter={(value: number) => [`${value.toFixed(2)}%`, "Drift Share"]}
                  />
                  <Line type="monotone" dataKey="drift_share" stroke={statusStyle.accent} strokeWidth={2.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-slate-100">Prediction Drift</CardTitle>
              <Badge
                className={
                  predictionDrift?.detected
                    ? "border border-amber-500/25 bg-amber-500/10 text-amber-300"
                    : "border border-emerald-500/25 bg-emerald-500/10 text-emerald-300"
                }
              >
                {predictionDrift?.detected ? "Alert Active" : "Stable"}
              </Badge>
            </div>
            <p className="mt-2 text-sm text-slate-400">
              BUY, SELL, and HOLD mix compared with the training reference distribution.
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={predictionChartData}>
                <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                <XAxis dataKey="window" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  tickFormatter={(value) => `${value}%`}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#020617",
                    border: "1px solid #1e293b",
                    borderRadius: "12px",
                  }}
                  formatter={(value: number, name: string) => [`${value}%`, name]}
                />
                <Bar dataKey="BUY" stackId="mix" fill="#34d399" radius={[4, 4, 0, 0]} />
                <Bar dataKey="HOLD" stackId="mix" fill="#38bdf8" />
                <Bar dataKey="SELL" stackId="mix" fill="#fb7185" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              {["BUY", "SELL", "HOLD"].map((label) => (
                <div key={label} className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3">
                  <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label} Shift</p>
                  <p className="mt-2 text-xl font-semibold text-slate-100">
                    {fmtPct((predictionDrift?.ratio_shifts?.[label] ?? 0) * 100, 1)}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-slate-100">Model Performance</CardTitle>
              <Badge
                className={
                  performance?.degradation_detected
                    ? "border border-amber-500/25 bg-amber-500/10 text-amber-300"
                    : "border border-emerald-500/25 bg-emerald-500/10 text-emerald-300"
                }
              >
                {performance?.ground_truth_available
                  ? performance.degradation_detected
                    ? "Degradation Detected"
                    : "Within Baseline"
                  : "Awaiting Ground Truth"}
              </Badge>
            </div>
            <p className="mt-2 text-sm text-slate-400">
              Rolling F1 over the current evaluation window, compared against the training baseline.
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={performance?.rolling ?? []} margin={{ left: -18, right: 10, top: 10, bottom: 0 }}>
                <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis
                  domain={[0, 1]}
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#020617",
                    border: "1px solid #1e293b",
                    borderRadius: "12px",
                  }}
                  formatter={(value: number, name: string) => [value.toFixed(4), name]}
                />
                <Line type="monotone" dataKey="f1" stroke="#38bdf8" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              {[
                { label: "Current F1", value: performance?.current_f1 == null ? "—" : performance.current_f1.toFixed(4) },
                { label: "Baseline F1", value: performance?.baseline_f1 == null ? "—" : performance.baseline_f1.toFixed(4) },
                { label: "Degradation", value: performance?.degradation_pct == null ? "—" : fmtPct(performance.degradation_pct, 2) },
              ].map((item) => (
                <div key={item.label} className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3">
                  <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{item.label}</p>
                  <p className="mt-2 text-xl font-semibold text-slate-100">{item.value}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-slate-100">Data Freshness</CardTitle>
              <Badge
                className={
                  (freshness?.stale_count ?? 0) > 0
                    ? "border border-amber-500/25 bg-amber-500/10 text-amber-300"
                    : "border border-emerald-500/25 bg-emerald-500/10 text-emerald-300"
                }
              >
                {(freshness?.stale_count ?? 0) > 0 ? `${freshness?.stale_count} stale` : "All fresh"}
              </Badge>
            </div>
            <p className="mt-2 text-sm text-slate-400">
              Market data recency by ticker, using a stale threshold of {freshness?.stale_threshold_days ?? 1} day.
            </p>
          </CardHeader>
          <CardContent>
            <div className="overflow-hidden rounded-2xl border border-slate-800">
              <table className="w-full text-sm">
                <thead className="bg-slate-950/80">
                  <tr>
                    {["Ticker", "Last Market Date", "Last Ingested", "Status"].map((label) => (
                      <th
                        key={label}
                        className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500"
                      >
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(freshness?.tickers ?? []).map((row) => (
                    <tr key={row.ticker} className="border-t border-slate-800/70">
                      <td className="px-4 py-3 font-medium text-slate-100">{row.ticker}</td>
                      <td className="px-4 py-3 text-slate-400">{row.last_market_date ?? "—"}</td>
                      <td className="px-4 py-3 text-slate-500">{fmtMaybeDate(row.last_ingested_at)}</td>
                      <td className="px-4 py-3">
                        <Badge
                          className={
                            row.status === "fresh"
                              ? "border border-emerald-500/25 bg-emerald-500/10 text-emerald-300"
                              : "border border-amber-500/25 bg-amber-500/10 text-amber-300"
                          }
                        >
                          {row.status === "fresh" ? "Fresh" : `${row.days_stale ?? "?"}d stale`}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-900">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-slate-100">Feature Drift Table</CardTitle>
              <p className="mt-2 text-sm text-slate-400">
                Sort by drift score to surface the most unstable input features first.
              </p>
            </div>
            <AlertTriangle className="h-5 w-5 text-cyan-400" />
          </div>
        </CardHeader>
        <CardContent>
          <FeatureDriftTable rows={featureDrift} />
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-900">
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <CardTitle className="text-slate-100">Retraining</CardTitle>
              <p className="mt-2 text-sm text-slate-400">
                Review the latest retraining decisions and manually run the full refresh pipeline when needed.
              </p>
            </div>
            <Button
              onClick={() => setShowRetrainModal(true)}
              className="bg-cyan-500 text-slate-950 hover:bg-cyan-400"
            >
              <RefreshCcw className="mr-2 h-4 w-4" />
              Trigger Retraining
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 lg:grid-cols-3">
            {[
              {
                label: "Last Retrain Date",
                value: latestRetrain ? fmtMaybeDate(latestRetrain.triggered_at) : "—",
                subtext: latestRetrain ? relativeTime(latestRetrain.triggered_at) : "No retraining runs yet",
              },
              {
                label: "Last Trigger Reason",
                value: latestRetrain?.trigger_reason ?? "—",
                subtext: latestRetrain?.promoted ? "Resulted in model promotion" : "No promotion logged",
              },
              {
                label: "Latest Model Outcome",
                value: latestRetrain?.new_model_version ? `v${latestRetrain.new_model_version}` : "—",
                subtext:
                  latestRetrain?.new_f1 == null ? "No F1 recorded" : `Best F1 ${latestRetrain.new_f1.toFixed(4)}`,
              },
            ].map((item) => (
              <div key={item.label} className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{item.label}</p>
                <p className="mt-2 text-lg font-semibold text-slate-100">{item.value}</p>
                <p className="mt-1 text-xs text-slate-500">{item.subtext}</p>
              </div>
            ))}
          </div>

          {retrainHistory.length === 0 ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-8 text-center text-sm text-slate-500">
              No retraining events have been logged yet.
            </div>
          ) : (
            <div className="overflow-hidden rounded-2xl border border-slate-800">
              <table className="w-full min-w-[860px] text-sm">
                <thead className="bg-slate-950/80">
                  <tr>
                    {["Triggered", "Reason", "Old", "New", "New F1", "Promoted", "Notes"].map((label) => (
                      <th
                        key={label}
                        className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500"
                      >
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {retrainHistory.map((row) => (
                    <tr key={row.id} className="border-t border-slate-800/70">
                      <td className="px-4 py-3 whitespace-nowrap text-slate-300">{fmtMaybeDate(row.triggered_at)}</td>
                      <td className="px-4 py-3 text-slate-300">{row.trigger_reason}</td>
                      <td className="px-4 py-3 font-mono text-slate-500">{row.old_model_version ? `v${row.old_model_version}` : "—"}</td>
                      <td className="px-4 py-3 font-mono text-slate-200">{row.new_model_version ? `v${row.new_model_version}` : "—"}</td>
                      <td className="px-4 py-3 font-mono text-slate-300">{row.new_f1 == null ? "—" : row.new_f1.toFixed(4)}</td>
                      <td className="px-4 py-3">
                        <Badge
                          className={
                            row.promoted
                              ? "border border-emerald-500/25 bg-emerald-500/10 text-emerald-300"
                              : "border border-slate-700 bg-slate-900 text-slate-300"
                          }
                        >
                          {row.promoted ? "Yes" : "No"}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-500">{row.notes ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {showRetrainModal && (
        <RetrainConfirmModal
          loading={isTriggeringRetrain}
          lastReason={latestRetrain?.trigger_reason ?? null}
          onCancel={() => setShowRetrainModal(false)}
          onConfirm={handleManualRetrain}
        />
      )}
    </div>
  );
}
