"use client";

import { AlertTriangle, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  onConfirm: () => void;
  onCancel: () => void;
  loading: boolean;
  lastReason: string | null;
}

export function RetrainConfirmModal({ onConfirm, onCancel, loading, lastReason }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm px-4">
      <div className="w-full max-w-lg rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl">
        <div className="border-b border-slate-800 px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-300">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-100">Trigger Retraining</h3>
              <p className="mt-1 text-sm text-slate-400">
                This will run feature engineering, model training, promotion checks, and fresh inference.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-4 px-6 py-5">
          <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Last Trigger Reason
            </p>
            <p className="mt-2 text-sm text-slate-300">
              {lastReason ?? "No retraining has been logged yet."}
            </p>
          </div>
          <p className="text-sm text-slate-400">
            Manual retraining should be used when you want to refresh the champion model immediately, even if the
            automated thresholds have not fired yet.
          </p>
        </div>

        <div className="flex items-center justify-end gap-3 border-t border-slate-800 px-6 py-4">
          <Button variant="outline" className="border-slate-700 bg-slate-900 text-slate-300" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            disabled={loading}
            className="bg-cyan-500 text-slate-950 hover:bg-cyan-400"
          >
            <RefreshCcw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Running..." : "Confirm Retraining"}
          </Button>
        </div>
      </div>
    </div>
  );
}
