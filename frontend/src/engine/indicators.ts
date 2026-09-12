/**
 * Pure, causal technical indicators in TypeScript.
 * Matches src/indicators.py identically: one implementation per concept, no lookahead.
 */

export function ema(series: number[], period: number): (number | null)[] {
  if (period <= 0) throw new Error("period must be positive");
  const n = series.length;
  const out: (number | null)[] = new Array(n).fill(null);
  if (n < period) return out;

  const alpha = 2.0 / (period + 1.0);

  // In pandas adjust=False ewm, the first value is the first data point
  // pandas: series.ewm(span=period, adjust=False, min_periods=period).mean()
  let current = series[0];
  for (let i = 1; i < period - 1; i++) {
    current = alpha * series[i] + (1.0 - alpha) * current;
  }

  for (let i = period - 1; i < n; i++) {
    if (i === 0) {
      current = series[0];
    } else {
      current = alpha * series[i] + (1.0 - alpha) * current;
    }
    out[i] = current;
  }
  return out;
}

export function sma(series: number[], period: number): (number | null)[] {
  if (period <= 0) throw new Error("period must be positive");
  const n = series.length;
  const out: (number | null)[] = new Array(n).fill(null);
  if (n < period) return out;

  let sum = 0;
  for (let i = 0; i < period; i++) sum += series[i];
  out[period - 1] = sum / period;

  for (let i = period; i < n; i++) {
    sum += series[i] - series[i - period];
    out[i] = sum / period;
  }
  return out;
}

export function rsi(closes: number[], period: number = 14): (number | null)[] {
  if (period <= 0) throw new Error("period must be positive");
  const n = closes.length;
  const out: (number | null)[] = new Array(n).fill(null);
  if (n <= period) return out;

  const gains: number[] = new Array(n).fill(0);
  const losses: number[] = new Array(n).fill(0);

  for (let i = 1; i < n; i++) {
    const diff = closes[i] - closes[i - 1];
    if (diff > 0) gains[i] = diff;
    else losses[i] = -diff;
  }

  const alpha = 1.0 / period;
  let avgGain = gains[0];
  let avgLoss = losses[0];

  for (let i = 1; i < n; i++) {
    avgGain = alpha * gains[i] + (1.0 - alpha) * avgGain;
    avgLoss = alpha * losses[i] + (1.0 - alpha) * avgLoss;

    if (i >= period) {
      if (avgLoss === 0) {
        out[i] = 100.0;
      } else {
        const rs = avgGain / avgLoss;
        out[i] = 100.0 - (100.0 / (1.0 + rs));
      }
    }
  }
  return out;
}

export function trueRange(highs: number[], lows: number[], closes: number[]): number[] {
  const n = highs.length;
  const tr: number[] = new Array(n);
  if (n === 0) return tr;

  tr[0] = highs[0] - lows[0];
  for (let i = 1; i < n; i++) {
    const prevClose = closes[i - 1];
    const hl = highs[i] - lows[i];
    const hpc = Math.abs(highs[i] - prevClose);
    const lpc = Math.abs(lows[i] - prevClose);
    tr[i] = Math.max(hl, hpc, lpc);
  }
  return tr;
}

export function atr(highs: number[], lows: number[], closes: number[], period: number = 14): (number | null)[] {
  if (period <= 0) throw new Error("period must be positive");
  const tr = trueRange(highs, lows, closes);
  const n = tr.length;
  const out: (number | null)[] = new Array(n).fill(null);
  if (n < period) return out;

  const alpha = 1.0 / period;
  let current = tr[0];
  for (let i = 1; i < period - 1; i++) {
    current = alpha * tr[i] + (1.0 - alpha) * current;
  }

  for (let i = period - 1; i < n; i++) {
    if (i === 0) current = tr[0];
    else current = alpha * tr[i] + (1.0 - alpha) * current;
    out[i] = current;
  }
  return out;
}

export function obv(closes: number[], volumes: number[]): number[] {
  const n = closes.length;
  const out: number[] = new Array(n).fill(0);
  if (n === 0) return out;

  out[0] = volumes[0];
  for (let i = 1; i < n; i++) {
    if (closes[i] > closes[i - 1]) {
      out[i] = out[i - 1] + volumes[i];
    } else if (closes[i] < closes[i - 1]) {
      out[i] = out[i - 1] - volumes[i];
    } else {
      out[i] = out[i - 1];
    }
  }
  return out;
}

