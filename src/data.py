"""
Synthetic OHLCV generator.

This sandbox has no route to Zerodha Kite Connect or any tick vendor (the
container's network is locked down to package registries only), so real
NSE/MCX data cannot be pulled here. This module generates a reproducible
regime-switching synthetic series (trend legs + mean-reverting chop, with
realistic intrabar high/low) purely so the backtest harness and engine have
something deterministic to run against and so tests are reproducible.

In the real system this module is replaced by the Kite Connect / tick
vendor adapter described in the report -- nothing downstream (indicators,
engine, backtester) needs to change, since they only depend on a plain
OHLCV DataFrame.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_ohlcv(
    n_bars: int = 500,
    start_price: float = 1000.0,
    seed: int = 42,
    bar_minutes: int = 5,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Regime schedule: alternating trend / chop legs so the grid+SAR engine
    # sees both pyramiding conditions and stop-and-reverse conditions.
    regimes = []
    remaining = n_bars
    while remaining > 0:
        length = int(rng.integers(40, 90))
        length = min(length, remaining)
        kind = rng.choice(["trend_up", "trend_down", "chop"])
        drift = {"trend_up": 0.0009, "trend_down": -0.0009, "chop": 0.0}[kind]
        vol = {"trend_up": 0.0025, "trend_down": 0.0025, "chop": 0.0018}[kind]
        regimes.append((length, drift, vol))
        remaining -= length

    closes = [start_price]
    for length, drift, vol in regimes:
        for _ in range(length):
            shock = rng.normal(drift, vol)
            closes.append(closes[-1] * (1 + shock))
    closes = np.array(closes[1 : n_bars + 1])

    opens = np.empty(n_bars)
    opens[0] = start_price
    opens[1:] = closes[:-1]

    highs = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0.0008, 0.0006, n_bars)))
    lows = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0.0008, 0.0006, n_bars)))
    volumes = rng.integers(1_000, 50_000, n_bars).astype(float)

    idx = pd.date_range("2026-01-02 09:15:00", periods=n_bars, freq=f"{bar_minutes}min")
    df = pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes},
        index=idx,
    )
    df.index.name = "timestamp"
    return df
