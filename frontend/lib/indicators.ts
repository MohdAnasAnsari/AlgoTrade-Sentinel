/**
 * Client-side technical indicator calculations.
 * All functions return arrays of the same length as the input,
 * with null for positions where the indicator is not yet defined.
 */

export function sma(values: number[], period: number): (number | null)[] {
  return values.map((_, i) => {
    if (i < period - 1) return null;
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += values[j];
    return sum / period;
  });
}

export function ema(values: number[], period: number): (number | null)[] {
  const k = 2 / (period + 1);
  const result: (number | null)[] = new Array(values.length).fill(null);
  if (values.length < period) return result;

  // Seed with simple average of first `period` values
  let prev = 0;
  for (let i = 0; i < period; i++) prev += values[i];
  prev /= period;
  result[period - 1] = prev;

  for (let i = period; i < values.length; i++) {
    const cur = values[i] * k + prev * (1 - k);
    result[i] = cur;
    prev = cur;
  }
  return result;
}

export interface BBands {
  upper: number | null;
  middle: number | null;
  lower: number | null;
}

export function bollingerBands(
  values: number[],
  period = 20,
  stdMult = 2
): BBands[] {
  const midArr = sma(values, period);
  return values.map((_, i) => {
    const mid = midArr[i];
    if (mid === null) return { upper: null, middle: null, lower: null };
    const slice = values.slice(i - period + 1, i + 1);
    const variance =
      slice.reduce((acc, v) => acc + (v - mid) ** 2, 0) / period;
    const sd = Math.sqrt(variance) * stdMult;
    return { upper: mid + sd, middle: mid, lower: mid - sd };
  });
}
