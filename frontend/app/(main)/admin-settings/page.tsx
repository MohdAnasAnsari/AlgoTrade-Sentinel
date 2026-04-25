"use client";

import { useEffect, useState, type ReactNode } from "react";
import { Database, Plus, RefreshCcw, Save, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { PageHeader } from "@/components/shared/page-header";
import { useAdminSettings } from "@/hooks/use-admin-settings";
import { useToast } from "@/hooks/use-toast";
import { formatDateTime } from "@/lib/format";

function SettingsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-[240px] rounded-[28px] bg-slate-900" />
        ))}
      </div>
      <Skeleton className="h-[280px] rounded-[28px] bg-slate-900" />
    </div>
  );
}

export default function AdminSettingsPage() {
  const { settings, watchlist, isLoading, isSaving, error, reload, save, addWatchlistTicker, removeWatchlistTicker } =
    useAdminSettings();
  const { pushToast } = useToast();
  const [draft, setDraft] = useState<typeof settings | null>(null);
  const [tickerInput, setTickerInput] = useState("");

  useEffect(() => {
    if (settings) setDraft(settings);
  }, [settings]);

  if (isLoading || !draft) {
    return <SettingsSkeleton />;
  }

  const pipelineRuns = draft.environment.last_pipeline_runs as Record<string, { last_finished_at?: string; last_status?: string }>;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Admin Settings"
        subtitle="Control watchlist composition, modeling thresholds, backtest defaults, retraining rules, and platform health from one place."
        actions={
          <>
            <Button
              variant="outline"
              className="border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800"
              onClick={() => reload()}
            >
              <RefreshCcw className="mr-2 h-4 w-4" />
              Reload
            </Button>
            <Button
              className="bg-cyan-500 text-slate-950 hover:bg-cyan-400"
              disabled={isSaving}
              onClick={async () => {
                try {
                  await save({
                    model: draft.model,
                    backtest: draft.backtest,
                    retrain: draft.retrain,
                    portfolio: draft.portfolio,
                  });
                  pushToast({ title: "Settings saved", description: "Configuration changes were persisted successfully.", tone: "success" });
                } catch (err) {
                  pushToast({
                    title: "Save failed",
                    description: err instanceof Error ? err.message : "Settings could not be saved.",
                    tone: "error",
                  });
                }
              }}
            >
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </Button>
          </>
        }
      />

      {error ? <ErrorState message={error} onRetry={() => reload()} /> : null}

      <div className="grid gap-6 xl:grid-cols-2">
        <SettingsCard title="Model Configuration">
          <Field
            label="Signal Threshold"
            value={draft.model.signal_threshold}
            onChange={(value) => setDraft({ ...draft, model: { ...draft.model, signal_threshold: value } })}
          />
          <Field
            label="Confidence Filter"
            value={draft.model.confidence_filter}
            onChange={(value) => setDraft({ ...draft, model: { ...draft.model, confidence_filter: value } })}
          />
          <Field
            label="Position Sizing %"
            value={draft.model.position_sizing_pct}
            onChange={(value) => setDraft({ ...draft, model: { ...draft.model, position_sizing_pct: value } })}
          />
        </SettingsCard>

        <SettingsCard title="Backtest Defaults">
          <Field
            label="Initial Capital"
            value={draft.backtest.initial_capital}
            onChange={(value) => setDraft({ ...draft, backtest: { ...draft.backtest, initial_capital: value } })}
          />
          <Field
            label="Transaction Cost"
            value={draft.backtest.transaction_cost}
            onChange={(value) => setDraft({ ...draft, backtest: { ...draft.backtest, transaction_cost: value } })}
          />
          <Field
            label="Slippage"
            value={draft.backtest.slippage}
            onChange={(value) => setDraft({ ...draft, backtest: { ...draft.backtest, slippage: value } })}
          />
        </SettingsCard>

        <SettingsCard title="Retrain Settings">
          <label className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-slate-100">Auto Retrain</p>
              <p className="text-xs text-slate-500">Enable or pause automatic retraining triggers.</p>
            </div>
            <input
              type="checkbox"
              checked={draft.retrain.auto_retrain_enabled}
              onChange={(event) =>
                setDraft({
                  ...draft,
                  retrain: { ...draft.retrain, auto_retrain_enabled: event.target.checked },
                })
              }
              className="h-4 w-4 rounded border-slate-600 bg-slate-900 text-cyan-400"
            />
          </label>
          <Field
            label="Drift Threshold"
            value={draft.retrain.drift_threshold}
            onChange={(value) => setDraft({ ...draft, retrain: { ...draft.retrain, drift_threshold: value } })}
          />
          <Field
            label="Performance Threshold"
            value={draft.retrain.performance_threshold}
            onChange={(value) => setDraft({ ...draft, retrain: { ...draft.retrain, performance_threshold: value } })}
          />
        </SettingsCard>

        <SettingsCard title="Paper Portfolio Engine">
          <Field
            label="Initial Cash"
            value={draft.portfolio.initial_cash}
            onChange={(value) => setDraft({ ...draft, portfolio: { ...draft.portfolio, initial_cash: value } })}
          />
          <Field
            label="Max Positions"
            value={draft.portfolio.max_positions}
            onChange={(value) => setDraft({ ...draft, portfolio: { ...draft.portfolio, max_positions: Math.round(value) } })}
          />
          <Field
            label="Transaction Cost"
            value={draft.portfolio.transaction_cost}
            onChange={(value) => setDraft({ ...draft, portfolio: { ...draft.portfolio, transaction_cost: value } })}
          />
        </SettingsCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100">Watchlist Configuration</CardTitle>
            <p className="text-sm text-slate-400">Manage the live watchlist and queue ingest → features → inference for new names.</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <input
                value={tickerInput}
                onChange={(event) => setTickerInput(event.target.value.toUpperCase())}
                placeholder="Ticker"
                className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-500"
              />
              <Button
                className="bg-cyan-500 text-slate-950 hover:bg-cyan-400"
                onClick={async () => {
                  if (!tickerInput.trim()) return;
                  const response = await addWatchlistTicker(tickerInput.trim());
                  setTickerInput("");
                  pushToast({ title: "Watchlist updated", description: response.message, tone: "success" });
                }}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Ticker
              </Button>
            </div>
            {watchlist.length === 0 ? (
              <EmptyState
                icon={Database}
                title="No watchlist entries"
                description="Add your first ticker to kick off ingest, feature generation, and inference."
              />
            ) : (
              <div className="space-y-2">
                {watchlist.map((item) => (
                  <div key={item.id} className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3">
                    <div>
                      <p className="font-medium text-slate-100">{item.ticker}</p>
                      <p className="text-xs text-slate-500">{item.company_name}</p>
                    </div>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="text-slate-400 hover:bg-slate-800 hover:text-rose-300"
                      onClick={async () => {
                        const response = await removeWatchlistTicker(item.ticker);
                        pushToast({ title: "Watchlist updated", description: response.message, tone: "success" });
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100">Environment Status</CardTitle>
            <p className="text-sm text-slate-400">Runtime connectivity and latest observed pipeline runs.</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <StatusRow label="Database" ok={draft.environment.database_ok} />
            <StatusRow label="MLflow" ok={draft.environment.mlflow_ok} />
            <StatusRow label="Scheduler" ok={draft.environment.scheduler_running} />
            <StatusRow label="Prefect Available" ok={draft.environment.prefect_available} />
            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Last Pipeline Runs</p>
              <div className="mt-3 space-y-2">
                {Object.entries(pipelineRuns).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <span className="text-slate-300">{key}</span>
                    <span className="text-slate-500">
                      {value?.last_finished_at ? formatDateTime(value.last_finished_at) : value?.last_status ?? "—"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-900">
        <CardHeader className="pb-3">
          <CardTitle className="text-slate-100">System Info</CardTitle>
          <p className="text-sm text-slate-400">Versioning and runtime metadata for the current app instance.</p>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-4">
          {[
            ["App Version", draft.system.app_version],
            ["Python Version", draft.system.python_version],
            ["Model Version", draft.system.model_version ?? "—"],
            ["Dataset Version", draft.system.dataset_version ?? "—"],
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{label}</p>
              <p className="mt-2 text-lg font-semibold text-slate-100">{value}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function SettingsCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card className="border-slate-800 bg-slate-900">
      <CardHeader className="pb-3">
        <CardTitle className="text-slate-100">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">{children}</CardContent>
    </Card>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3">
      <span className="text-sm font-medium text-slate-100">{label}</span>
      <input
        type="number"
        step="0.0001"
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-3 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
      />
    </label>
  );
}

function StatusRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3">
      <span className="text-sm text-slate-300">{label}</span>
      <span className={`rounded-full px-2 py-1 text-xs ${ok ? "bg-emerald-500/10 text-emerald-300" : "bg-rose-500/10 text-rose-300"}`}>
        {ok ? "OK" : "Unavailable"}
      </span>
    </div>
  );
}
