"use client";

import { useEffect, useState } from "react";

const SIDEBAR_KEY = "algotrade-sidebar-collapsed";

export function useSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(SIDEBAR_KEY);
    if (stored !== null) {
      setCollapsed(JSON.parse(stored));
    }
    setMounted(true);
  }, []);

  const toggle = () => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(SIDEBAR_KEY, JSON.stringify(next));
      return next;
    });
  };

  return { collapsed, toggle, mounted };
}
