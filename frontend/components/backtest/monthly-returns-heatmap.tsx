"use client";
import React from "react";

interface Props {
  data: Record<string, number>;
}

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function cellBg(val: number | undefined): string {
  if (val == null) return "bg-slate-800/40";
  const intensity = Math.min(Math.abs(val) / 6, 1); // ±6% = full intensity
  if (val > 0) {
    const alpha = Math.round((0.2 + intensity * 0.65) * 255).toString(16).padStart(2, "0");
    return `bg-emerald-600`;
  }
  return `bg-rose-600`;
}

function cellStyle(val: number | undefined): React.CSSProperties {
  if (val == null) return {};
  const intensity = Math.min(Math.abs(val) / 6, 1);
  const opacity   = 0.18 + intensity * 0.65;
  return val > 0
    ? { backgroundColor: `rgba(16,185,129,${opacity})` }
    : { backgroundColor: `rgba(244,63,94,${opacity})` };
}

export function MonthlyReturnsHeatmap({ data }: Props) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 flex items-center justify-center h-32 text-slate-500 text-sm">
        No monthly returns data
      </div>
    );
  }

  const years = Array.from(new Set(Object.keys(data).map((k) => k.slice(0, 4)))).sort();

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
      <h3 className="text-sm font-semibold text-slate-200 mb-4">Monthly Returns Heatmap</h3>
      <div className="overflow-x-auto">
        <table className="text-xs border-separate border-spacing-1 w-full">
          <thead>
            <tr>
              <th className="text-right pr-2 text-slate-500 font-normal w-12">Year</th>
              {MONTHS.map((m) => (
                <th key={m} className="text-center text-slate-500 font-normal w-14">{m}</th>
              ))}
              <th className="text-center text-slate-500 font-normal w-14">Ann.</th>
            </tr>
          </thead>
          <tbody>
            {years.map((year) => {
              const monthVals = Array.from({ length: 12 }, (_, i) => {
                const key = `${year}-${String(i + 1).padStart(2, "0")}`;
                return data[key] ?? null;
              });
              const annReturn = monthVals.reduce<number>((acc, v) => {
                return v != null ? acc * (1 + v / 100) : acc;
              }, 1);
              const annPct = (annReturn - 1) * 100;

              return (
                <tr key={year}>
                  <td className="text-right pr-2 text-slate-400 font-medium">{year}</td>
                  {monthVals.map((val, mi) => (
                    <td
                      key={mi}
                      className="text-center rounded py-1.5 px-0.5 font-mono"
                      style={cellStyle(val ?? undefined)}
                      title={val != null ? `${val >= 0 ? "+" : ""}${val.toFixed(2)}%` : "N/A"}
                    >
                      {val != null ? (
                        <span className="text-white/90">{val >= 0 ? "+" : ""}{val.toFixed(1)}</span>
                      ) : (
                        <span className="text-slate-700">·</span>
                      )}
                    </td>
                  ))}
                  <td
                    className="text-center rounded py-1.5 px-0.5 font-mono font-semibold"
                    style={cellStyle(annPct)}
                  >
                    <span className="text-white/90">
                      {annPct >= 0 ? "+" : ""}{annPct.toFixed(1)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="flex items-center gap-3 mt-3 justify-end text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm" style={{ background: "rgba(16,185,129,0.7)" }}/>
          Positive
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-sm" style={{ background: "rgba(244,63,94,0.7)" }}/>
          Negative
        </span>
      </div>
    </div>
  );
}
