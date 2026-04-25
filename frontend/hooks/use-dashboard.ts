"use client";

import { useCallback, useEffect, useState } from "react";
import { dashboardApi, type DashboardOverview } from "@/lib/api";

export function useDashboard() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    if (mode === "initial") setIsLoading(true);
    else setIsRefreshing(true);

    try {
      setError(null);
      setOverview(await dashboardApi.overview());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void load("initial");
  }, [load]);

  return {
    overview,
    isLoading,
    isRefreshing,
    error,
    refresh: () => load("refresh"),
  };
}
