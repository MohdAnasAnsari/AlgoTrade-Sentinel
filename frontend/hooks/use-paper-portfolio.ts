"use client";

import { useCallback, useEffect, useState } from "react";
import {
  alertsApi,
  portfolioApi,
  watchlistApi,
  type AlertListResponse,
  type OrderOut,
  type PnLBreakdown,
  type PortfolioHistoryPoint,
  type PortfolioSummary,
  type PositionOut,
  type WatchlistItem,
} from "@/lib/api";

interface OrderFilters {
  order_type?: string;
  ticker?: string;
  limit?: number;
  offset?: number;
}

export function usePaperPortfolio() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [positions, setPositions] = useState<PositionOut[]>([]);
  const [history, setHistory] = useState<PortfolioHistoryPoint[]>([]);
  const [pnl, setPnl] = useState<PnLBreakdown | null>(null);
  const [orders, setOrders] = useState<OrderOut[]>([]);
  const [ordersTotal, setOrdersTotal] = useState(0);
  const [alerts, setAlerts] = useState<AlertListResponse["items"]>([]);
  const [unreadAlerts, setUnreadAlerts] = useState(0);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOrders = useCallback(async (filters?: OrderFilters) => {
    const response = await portfolioApi.getOrders(filters);
    setOrders(response.items);
    setOrdersTotal(response.total);
  }, []);

  const load = useCallback(
    async (mode: "initial" | "refresh" = "initial", filters?: OrderFilters) => {
      if (mode === "initial") setIsLoading(true);
      else setIsRefreshing(true);

      try {
        setError(null);
        const [summaryData, positionsData, historyData, pnlData, alertsData, unreadData, watchlistData] =
          await Promise.all([
            portfolioApi.getSummary(),
            portfolioApi.getPositions(),
            portfolioApi.getHistory(30),
            portfolioApi.getPnl(),
            alertsApi.list({ limit: 20 }),
            alertsApi.unread(),
            watchlistApi.list(),
          ]);

        setSummary(summaryData);
        setPositions(positionsData);
        setHistory(historyData);
        setPnl(pnlData);
        setAlerts(alertsData.items);
        setUnreadAlerts(unreadData.unread);
        setWatchlist(watchlistData);
        await fetchOrders(filters ?? { limit: 25, offset: 0 });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load paper portfolio");
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [fetchOrders]
  );

  useEffect(() => {
    void load("initial");
  }, [load]);

  return {
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
    refresh: (filters?: OrderFilters) => load("refresh", filters),
    fetchOrders,
    markAlertRead: async (id: number) => {
      await alertsApi.markRead(id);
      await load("refresh");
    },
    markAllAlertsRead: async () => {
      await alertsApi.markAllRead();
      await load("refresh");
    },
    addWatchlistTicker: async (ticker: string, companyName?: string, sector?: string) => {
      const response = await watchlistApi.add({ ticker, company_name: companyName, sector });
      await load("refresh");
      return response;
    },
    removeWatchlistTicker: async (ticker: string) => {
      const response = await watchlistApi.remove(ticker);
      await load("refresh");
      return response;
    },
  };
}
