"use client";
import React from "react";
import { ComparisonResult } from "@/lib/api";

interface Props {
  comparison: ComparisonResult;
}

function fmt(v: number | null | undefined, decimals = 4) {
  return v != null ? v.toFixed(decimals) : "—";
}

export function MetricsComparison({ comparison: cmp }: Props) {
  const c   = cmp.champion;
  const chs = cmp.challengers;

  if (!c && !chs.length) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-5 text-center text-slate-500 text-sm">
        No models to compare
      </div>
    );
  }

  const metrics = [
    { key: "f1_macro",  label: "F1 Macro"  },
    { key: "accuracy",  label: "Accuracy"  },
    { key: "roc_auc",   label: "ROC-AUC"   },
  ] as const;

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
      <div className="px-5 py-3 border-b border-slate-700">
        <h3 className="text-sm font-semibold text-slate-200">Champion vs Challengers</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-800/50">
            <tr>
              <th className="px-5 py-2 text-left text-xs font-medium text-slate-400">Metric</th>
              <th className="px-5 py-2 text-right text-xs font-medium text-cyan-400">
                Champion {c ? `v${c.version}` : ""}
              </th>
              {chs.map((ch) => (
                <th key={ch.version} className="px-5 py-2 text-right text-xs font-medium text-amber-400">
                  Challenger v{ch.version}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {metrics.map(({ key, label }) => (
              <tr key={key} className="border-t border-slate-800/60">
                <td className="px-5 py-2.5 text-slate-400">{label}</td>
                <td className="px-5 py-2.5 text-right font-mono text-slate-100">
                  {c ? fmt(c[key]) : "—"}
                </td>
                {chs.map((ch) => {
                  const champVal = c?.[key] ?? 0;
                  const chal     = ch[key] ?? 0;
                  const better   = c ? chal > champVal : null;
                  return (
                    <td key={ch.version} className="px-5 py-2.5 text-right font-mono">
                      <span className={better === true ? "text-emerald-400" : better === false ? "text-rose-400" : "text-slate-400"}>
                        {fmt(ch[key])}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
