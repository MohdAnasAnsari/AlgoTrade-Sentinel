"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { AlertCircle, CheckCircle2, X } from "lucide-react";

type ToastTone = "success" | "error";

interface ToastItem {
  id: number;
  title: string;
  description?: string;
  tone: ToastTone;
}

interface ToastContextValue {
  pushToast: (toast: Omit<ToastItem, "id">) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(1);

  const pushToast = useCallback((toast: Omit<ToastItem, "id">) => {
    const id = nextId.current++;
    setToasts((prev) => [...prev, { id, ...toast }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((item) => item.id !== id));
    }, 4200);
  }, []);

  const value = useMemo(() => ({ pushToast }), [pushToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed right-4 top-4 z-[100] flex w-full max-w-sm flex-col gap-3">
        {toasts.map((toast) => {
          const isSuccess = toast.tone === "success";
          const Icon = isSuccess ? CheckCircle2 : AlertCircle;
          return (
            <div
              key={toast.id}
              className={`pointer-events-auto rounded-2xl border px-4 py-3 shadow-xl backdrop-blur ${
                isSuccess
                  ? "border-emerald-500/25 bg-emerald-500/12 text-emerald-50"
                  : "border-rose-500/25 bg-rose-500/12 text-rose-50"
              }`}
            >
              <div className="flex items-start gap-3">
                <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${isSuccess ? "text-emerald-300" : "text-rose-300"}`} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">{toast.title}</p>
                  {toast.description ? (
                    <p className="mt-1 text-xs text-white/75">{toast.description}</p>
                  ) : null}
                </div>
                <button
                  type="button"
                  className="rounded-full p-1 text-white/50 transition hover:bg-white/10 hover:text-white"
                  onClick={() => setToasts((prev) => prev.filter((item) => item.id !== toast.id))}
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}
