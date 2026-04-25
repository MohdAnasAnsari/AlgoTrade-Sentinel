"use client";

import { useCallback, useEffect, useState } from "react";
import { settingsApi, watchlistApi, type AppSettings, type WatchlistItem } from "@/lib/api";

export function useAdminSettings() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      setError(null);
      const [settingsData, watchlistData] = await Promise.all([
        settingsApi.get(),
        watchlistApi.list(),
      ]);
      setSettings(settingsData);
      setWatchlist(watchlistData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return {
    settings,
    watchlist,
    isLoading,
    isSaving,
    error,
    reload: load,
    save: async (payload: Partial<AppSettings>) => {
      setIsSaving(true);
      try {
        const saved = await settingsApi.save(payload);
        setSettings(saved);
        return saved;
      } finally {
        setIsSaving(false);
      }
    },
    addWatchlistTicker: async (ticker: string, companyName?: string, sector?: string) => {
      const response = await watchlistApi.add({ ticker, company_name: companyName, sector });
      await load();
      return response;
    },
    removeWatchlistTicker: async (ticker: string) => {
      const response = await watchlistApi.remove(ticker);
      await load();
      return response;
    },
  };
}
