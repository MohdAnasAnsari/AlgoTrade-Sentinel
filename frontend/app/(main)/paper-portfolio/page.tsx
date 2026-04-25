"use client";

import { useEffect, useState } from "react";
import { BellRing, BriefcaseBusiness, Plus, RefreshCcw, Search, Trash2 } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
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
import { usePaperPortfolio } from "@/hooks/use-paper-portfolio";
import { useToast } from "@/hooks/use-toast";
import { portfolioApi, type PositionDetail } from "@/lib/api";
import { formatCurrency, formatDate, formatDateTime, formatPercent } from "@/lib/format";

function PortfolioSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, index) => (
          <Card key={index} className="border-slate-800 bg-slate-900">
            <CardContent className="space-y-2 p-4">
              <Skeleton className="h-4 w-24 bg-slate-800" />
              <Skeleton className="h-8 w-28 bg-slate-800" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Skeleton className="h-[340px] rounded-[28px] bg-slate-900" />
      <Skeleton className="h-[420px] rounded-[28px] bg-slate-900" />
    </div>
  );
}

export default function PaperPortfolioPage() {
  const {
    summary,
    positions,
    history,
    pnl,
    orders,
    ordersTotal,
    alerts,
    unreadAlerts,
    watchlist,
    isLoading,
    isRefreshing,
    error,
    refresh,
    fetchOrders,
    markAlertRead,
    markAllAlertsRead,
    addWatchlistTicker,
    removeWatchlistTicker,
  } = usePaperPortfolio();
  const { pushToast } = useToast();

  const [orderType, setOrderType] = useState("");
  const [orderTicker, setOrderTicker] = useState("");
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [positionDetail, setPositionDetail] = useState<PositionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [newTicker, setNewTicker] = useState("");

  useEffect(() => {
    void fetchOrders({
      limit: 25,
      offset: 0,
      order_type: orderType || undefined,
      ticker: orderTicker || undefined,
    });
  }, [fetchOrders, orderTicker, orderType]);

  useEffect(() => {
    if (!selectedTicker) {
      setPositionDetail(null);
      return;
    }
    setDetailLoading(true);
    void portfolioApi
      .getPositionDetail(selectedTicker)
      .then((detail) => setPositionDetail(detail))
      .catch(() => setPositionDetail(null))
      .finally(() => setDetailLoading(false));
  }, [selectedTicker]);

  if (isLoading) {
    return <PortfolioSkeleton />;
  }

  if (!summary || !pnl) {
    return <ErrorState message={error ?? "Paper portfolio data is unavailable."} onRetry={() => refresh()} />;
  }

  const pnlCards = [
    { label: "Realized PnL", value: formatCurrency(pnl.realized_pnl) },
    { label: "Unrealized PnL", value: formatCurrency(pnl.unrealized_pnl) },
    { label: "Total Return", value: formatPercent(pnl.total_pnl_pct) },
    { label: "Best Performer", value: pnl.best_position ? `${pnl.best_position.ticker} • ${formatPercent(pnl.best_position.unrealized_pnl_pct)}` : "—" },
    { label: "Worst Performer", value: pnl.worst_position ? `${pnl.worst_position.ticker} • ${formatPercent(pnl.worst_position.unrealized_pnl_pct)}` : "—" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Paper Portfolio"
        subtitle="Live paper trading ledger with portfolio snapshots, order execution history, alerts, and watchlist control."
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

      <section className="grid gap-4 lg:grid-cols-5">
        {[
          { label: "Total Value", value: formatCurrency(summary.total_value), subtext: `Daily ${formatPercent(summary.daily_change_pct)}` },
          { label: "Daily Change", value: formatCurrency(summary.daily_change), subtext: formatPercent(summary.daily_change_pct) },
          { label: "Total PnL", value: formatCurrency(summary.total_pnl), subtext: formatPercent(summary.total_pnl_pct) },
          { label: "Cash Balance", value: formatCurrency(summary.cash_balance), subtext: "Available buying power" },
          { label: "Invested Value", value: formatCurrency(summary.invested_value), subtext: `${summary.open_positions} open position(s)` },
        ].map((item) => (
          <Card key={item.label} className="border-slate-800 bg-slate-900">
            <CardContent className="p-4">
              <p className="text-sm text-slate-400">{item.label}</p>
              <p className="mt-3 text-2xl font-semibold text-slate-100">{item.value}</p>
              <p className="mt-1 text-xs text-slate-500">{item.subtext}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100">Portfolio Value History</CardTitle>
            <p className="text-sm text-slate-400">Portfolio value from inception against the initial capital baseline.</p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="portfolioArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
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
                  tickFormatter={(value) => formatCurrency(value, { compact: true })}
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: "#020617", border: "1px solid #1e293b", borderRadius: 16 }}
                  formatter={(value: number) => [formatCurrency(value), "Portfolio"]}
                  labelFormatter={(value) => formatDate(value)}
                />
                <Area type="monotone" dataKey="total_value" stroke="#38bdf8" fill="url(#portfolioArea)" strokeWidth={2.5} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100">PnL Breakdown</CardTitle>
            <p className="text-sm text-slate-400">Realized, unrealized, and best/worst position snapshots.</p>
          </CardHeader>
          <CardContent className="grid gap-4">
            {pnlCards.map((item) => (
              <div key={item.label} className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{item.label}</p>
                <p className="mt-2 text-xl font-semibold text-slate-100">{item.value}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100">Open Positions</CardTitle>
            <p className="text-sm text-slate-400">Click a row to inspect the matching order history and position metadata.</p>
          </CardHeader>
          <CardContent>
            {positions.length === 0 ? (
              <EmptyState
                icon={BriefcaseBusiness}
                title="No open positions"
                description="The portfolio is currently in cash. Signals and paper trades will appear here once positions are opened."
                actionLabel="View Signal Center"
                actionHref="/signal-center"
              />
            ) : (
              <div className="overflow-hidden rounded-2xl border border-slate-800">
                <table className="w-full text-sm">
                  <thead className="bg-slate-950/80">
                    <tr>
                      {["Ticker", "Entry", "Entry Price", "Current", "Shares", "Market Value", "Unrealized", "Change %"].map((label) => (
                        <th key={label} className="px-4 py-3 text-left text-[11px] uppercase tracking-[0.18em] text-slate-500">
                          {label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((position) => (
                      <tr
                        key={position.id}
                        className="cursor-pointer border-t border-slate-800/70 transition hover:bg-slate-950/70"
                        onClick={() => setSelectedTicker(position.ticker)}
                      >
                        <td className="px-4 py-3 font-medium text-slate-100">
                          <div>{position.ticker}</div>
                          <div className="text-xs text-slate-500">{position.company_name ?? "Unknown"}</div>
                        </td>
                        <td className="px-4 py-3 text-slate-300">{formatDate(position.entry_date)}</td>
                        <td className="px-4 py-3 text-slate-300">{formatCurrency(position.entry_price)}</td>
                        <td className="px-4 py-3 text-slate-300">{formatCurrency(position.current_price)}</td>
                        <td className="px-4 py-3 text-slate-300">{position.shares.toFixed(4)}</td>
                        <td className="px-4 py-3 text-slate-300">{formatCurrency(position.market_value)}</td>
                        <td className={`px-4 py-3 ${position.unrealized_pnl >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
                          {formatCurrency(position.unrealized_pnl)}
                        </td>
                        <td className={`px-4 py-3 ${position.unrealized_pnl_pct >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
                          {formatPercent(position.unrealized_pnl_pct)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-slate-100">Position Detail</CardTitle>
            <p className="text-sm text-slate-400">Focused detail for the currently selected position.</p>
          </CardHeader>
          <CardContent>
            {detailLoading ? (
              <Skeleton className="h-48 rounded-2xl bg-slate-800" />
            ) : positionDetail ? (
              <div className="space-y-4">
                <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                  <p className="text-lg font-semibold text-slate-100">{positionDetail.position.ticker}</p>
                  <p className="mt-1 text-sm text-slate-500">{positionDetail.position.company_name ?? "Unknown company"}</p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div>
                      <p className="text-xs text-slate-500">Entry Date</p>
                      <p className="text-sm text-slate-200">{formatDate(positionDetail.position.entry_date)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Entry Price</p>
                      <p className="text-sm text-slate-200">{formatCurrency(positionDetail.position.entry_price)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Current Price</p>
                      <p className="text-sm text-slate-200">{formatCurrency(positionDetail.position.current_price)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Market Value</p>
                      <p className="text-sm text-slate-200">{formatCurrency(positionDetail.position.market_value)}</p>
                    </div>
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Orders</p>
                  <div className="mt-3 space-y-2">
                    {positionDetail.orders.map((order) => (
                      <div key={order.id} className="flex items-center justify-between rounded-xl border border-slate-800 px-3 py-2">
                        <div>
                          <p className="text-sm font-medium text-slate-100">{order.order_type}</p>
                          <p className="text-xs text-slate-500">{formatDate(order.order_date)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-slate-200">{formatCurrency(order.total_value)}</p>
                          <p className="text-xs text-slate-500">{order.shares.toFixed(4)} shares</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <EmptyState
                icon={Search}
                title="Select a position"
                description="Choose a row from the open positions table to inspect the related trade record."
              />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle className="text-slate-100">Orders History</CardTitle>
                <p className="text-sm text-slate-400">{ordersTotal} order(s) logged from signal-driven trades.</p>
              </div>
              <div className="flex gap-2">
                <select
                  value={orderType}
                  onChange={(event) => setOrderType(event.target.value)}
                  className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200"
                >
                  <option value="">All Types</option>
                  <option value="BUY">BUY</option>
                  <option value="SELL">SELL</option>
                </select>
                <input
                  value={orderTicker}
                  onChange={(event) => setOrderTicker(event.target.value.toUpperCase())}
                  placeholder="Ticker"
                  className="w-28 rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-500"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {orders.length === 0 ? (
              <EmptyState
                icon={RefreshCcw}
                title="No orders found"
                description="Adjust the filters or generate signals to populate the paper trading ledger."
              />
            ) : (
              <div className="overflow-hidden rounded-2xl border border-slate-800">
                <table className="w-full text-sm">
                  <thead className="bg-slate-950/80">
                    <tr>
                      {["Date", "Ticker", "Type", "Price", "Shares", "Value", "Cost"].map((label) => (
                        <th key={label} className="px-4 py-3 text-left text-[11px] uppercase tracking-[0.18em] text-slate-500">
                          {label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((order) => (
                      <tr key={order.id} className="border-t border-slate-800/70">
                        <td className="px-4 py-3 text-slate-300">{formatDate(order.order_date)}</td>
                        <td className="px-4 py-3 text-slate-100">{order.ticker}</td>
                        <td className="px-4 py-3">
                          <Badge className={order.order_type === "BUY" ? "border-emerald-500/25 bg-emerald-500/10 text-emerald-300" : "border-rose-500/25 bg-rose-500/10 text-rose-300"}>
                            {order.order_type}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-slate-300">{formatCurrency(order.price)}</td>
                        <td className="px-4 py-3 text-slate-300">{order.shares.toFixed(4)}</td>
                        <td className="px-4 py-3 text-slate-300">{formatCurrency(order.total_value)}</td>
                        <td className="px-4 py-3 text-slate-500">{formatCurrency(order.transaction_cost)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="border-slate-800 bg-slate-900">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-slate-100">Alerts</CardTitle>
                  <p className="text-sm text-slate-400">{unreadAlerts} unread alert(s)</p>
                </div>
                <Button
                  variant="ghost"
                  className="text-slate-300 hover:bg-slate-800 hover:text-white"
                  onClick={async () => {
                    await markAllAlertsRead();
                    pushToast({ title: "Alerts updated", description: "All alerts were marked as read.", tone: "success" });
                  }}
                >
                  Mark All Read
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {alerts.length === 0 ? (
                <EmptyState
                  icon={BellRing}
                  title="No alerts available"
                  description="Trading, monitoring, and data alerts will appear here once they are generated."
                />
              ) : (
                alerts.map((alert) => (
                  <div key={alert.id} className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge className="border-slate-700 bg-slate-800 text-slate-200">{alert.alert_type}</Badge>
                          {!alert.is_read ? <Badge className="border-cyan-500/25 bg-cyan-500/10 text-cyan-300">Unread</Badge> : null}
                        </div>
                        <p className="mt-3 text-sm text-slate-200">{alert.message}</p>
                        <p className="mt-1 text-xs text-slate-500">{formatDateTime(alert.created_at)}</p>
                      </div>
                      {!alert.is_read ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-slate-300 hover:bg-slate-800 hover:text-white"
                          onClick={async () => {
                            await markAlertRead(alert.id);
                            pushToast({ title: "Alert updated", description: "The alert was marked as read.", tone: "success" });
                          }}
                        >
                          Read
                        </Button>
                      ) : null}
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card className="border-slate-800 bg-slate-900">
            <CardHeader className="pb-3">
              <CardTitle className="text-slate-100">Watchlist</CardTitle>
              <p className="text-sm text-slate-400">Add or remove tickers and queue ingest → features → inference automatically.</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <input
                  value={newTicker}
                  onChange={(event) => setNewTicker(event.target.value.toUpperCase())}
                  placeholder="Add ticker"
                  className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-500"
                />
                <Button
                  onClick={async () => {
                    if (!newTicker.trim()) return;
                    const response = await addWatchlistTicker(newTicker.trim());
                    setNewTicker("");
                    pushToast({ title: "Watchlist updated", description: response.message, tone: "success" });
                  }}
                  className="bg-cyan-500 text-slate-950 hover:bg-cyan-400"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add
                </Button>
              </div>
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
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
