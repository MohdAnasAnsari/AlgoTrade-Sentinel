import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AppStore {
  // Sidebar
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (v: boolean) => void;
  toggleSidebar: () => void;

  // Alerts badge
  unreadAlertsCount: number;
  setUnreadAlertsCount: (n: number) => void;
  incrementUnreadAlerts: () => void;
  clearUnreadAlerts: () => void;

  // Active ticker selection (shared across pages)
  activeTicker: string | null;
  setActiveTicker: (ticker: string | null) => void;
}

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

      unreadAlertsCount: 0,
      setUnreadAlertsCount: (n) => set({ unreadAlertsCount: n }),
      incrementUnreadAlerts: () =>
        set((s) => ({ unreadAlertsCount: s.unreadAlertsCount + 1 })),
      clearUnreadAlerts: () => set({ unreadAlertsCount: 0 }),

      activeTicker: null,
      setActiveTicker: (ticker) => set({ activeTicker: ticker }),
    }),
    {
      name: "algotrade-app-store",
      partialize: (s) => ({
        sidebarCollapsed: s.sidebarCollapsed,
        activeTicker: s.activeTicker,
      }),
    }
  )
);
