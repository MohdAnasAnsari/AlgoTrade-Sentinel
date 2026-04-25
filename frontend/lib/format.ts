import { format } from "date-fns";

export function formatCurrency(value: number | null | undefined, options?: { compact?: boolean }) {
  if (value == null || Number.isNaN(value)) return "—";
  if (options?.compact) {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      notation: "compact",
      maximumFractionDigits: 2,
    }).format(value);
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number | null | undefined, digits = 2) {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(digits)}%`;
}

export function formatCompactNumber(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatDate(value: string | Date | null | undefined, pattern = "MMM dd, yyyy") {
  if (!value) return "—";
  try {
    return format(new Date(value), pattern);
  } catch {
    return String(value);
  }
}

export function formatDateTime(value: string | Date | null | undefined) {
  return formatDate(value, "MMM dd, yyyy • HH:mm");
}
