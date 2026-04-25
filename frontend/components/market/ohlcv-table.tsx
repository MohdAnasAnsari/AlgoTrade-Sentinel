"use client";

import { useMemo, useState } from "react";
import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, ChevronsUpDown } from "lucide-react";
import type { OHLCVRow } from "@/lib/api";

interface OHLCVTableProps {
  data: OHLCVRow[];
}

function fmt(n: number | null | undefined, dec = 2): string {
  if (n == null) return "—";
  return n.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec });
}

function fmtVol(n: number | null | undefined): string {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

const columns: ColumnDef<OHLCVRow>[] = [
  {
    accessorKey: "date",
    header: "Date",
    cell: ({ getValue }) => (
      <span className="font-mono text-slate-300">{getValue<string>()}</span>
    ),
  },
  {
    accessorKey: "open",
    header: "Open",
    cell: ({ getValue }) => <span className="text-slate-300">${fmt(getValue<number | null>())}</span>,
  },
  {
    accessorKey: "high",
    header: "High",
    cell: ({ getValue }) => <span className="text-emerald-400">${fmt(getValue<number | null>())}</span>,
  },
  {
    accessorKey: "low",
    header: "Low",
    cell: ({ getValue }) => <span className="text-rose-400">${fmt(getValue<number | null>())}</span>,
  },
  {
    accessorKey: "close",
    header: "Close",
    cell: ({ row }) => {
      const close = row.getValue<number | null>("close");
      const open = row.getValue<number | null>("open");
      const up = (close ?? 0) >= (open ?? 0);
      return (
        <span className={`font-semibold ${up ? "text-emerald-400" : "text-rose-400"}`}>
          ${fmt(close)}
        </span>
      );
    },
  },
  {
    accessorKey: "adj_close",
    header: "Adj Close",
    cell: ({ getValue }) => <span className="text-slate-400">${fmt(getValue<number | null>())}</span>,
  },
  {
    accessorKey: "volume",
    header: "Volume",
    cell: ({ getValue }) => (
      <span className="text-slate-400 font-mono">{fmtVol(getValue<number | null>())}</span>
    ),
  },
  {
    id: "change",
    header: "Change %",
    cell: ({ row }) => {
      const close = row.original.close;
      const open = row.original.open;
      if (close == null || open == null || open === 0) return <span className="text-slate-600">—</span>;
      const pct = ((close - open) / open) * 100;
      return (
        <span className={`font-semibold ${pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
          {pct >= 0 ? "+" : ""}{pct.toFixed(2)}%
        </span>
      );
    },
  },
];

export function OHLCVTable({ data }: OHLCVTableProps) {
  const [sorting, setSorting] = useState<SortingState>([{ id: "date", desc: true }]);

  // Show data newest-first by default
  const tableData = useMemo(() => [...data].reverse(), [data]);

  const table = useReactTable({
    data: tableData,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 20 } },
  });

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-24 text-slate-500 text-sm">
        No data available
      </div>
    );
  }

  return (
    <div>
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-sm">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="border-b border-slate-800">
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider cursor-pointer hover:text-slate-300 whitespace-nowrap select-none"
                  >
                    <span className="flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getCanSort() &&
                        (header.column.getIsSorted() === "asc" ? (
                          <ChevronUp className="w-3 h-3" />
                        ) : header.column.getIsSorted() === "desc" ? (
                          <ChevronDown className="w-3 h-3" />
                        ) : (
                          <ChevronsUpDown className="w-3 h-3 opacity-40" />
                        ))}
                    </span>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-2.5 whitespace-nowrap">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-3 px-1">
        <span className="text-xs text-slate-500">
          {data.length.toLocaleString()} rows ·{" "}
          page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="w-8 h-8 rounded-lg flex items-center justify-center border border-slate-700 text-slate-400 hover:text-white hover:border-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="w-8 h-8 rounded-lg flex items-center justify-center border border-slate-700 text-slate-400 hover:text-white hover:border-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
