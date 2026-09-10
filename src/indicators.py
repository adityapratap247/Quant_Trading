"""
Technical analysis indicators.

Design rule for this module: one tested implementation per indicator family,
no duplicated math. Every function is a pure function of a pandas Series /
DataFrame -> pandas Series, so it is trivially testable and trivially
composable inside the execution engine and the backtester.

All indicators are causal: indicator value at index i only uses data up to
and including bar i. This is what "no lookahead" means at the indicator
level -- the backtester relies on this property.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------------

def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential moving average. Trend indicator.

    Uses pandas' adjust=False recursive form, which is the form used in
    live/incremental computation (matches what you'd compute bar-by-bar in
    production, not just in a vectorized backtest).
    """
    if period <= 0:
        raise ValueError("period must be positive")
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple moving average. Used as a building block by other indicators
    (e.g. ATR's SMA variant) -- kept separate from `ema` so nothing computes
    a moving average two different ways."""
    if period <= 0:
        raise ValueError("period must be positive")
    return series.rolling(window=period, min_periods=period).mean()


# ---------------------------------------------------------------------------
# Momentum
# ---------------------------------------------------------------------------

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder's smoothing). Momentum indicator.

    Wilder's original smoothing is an EMA with alpha = 1/period, implemented
    directly (not delegated to `ema`, whose span-based alpha is different)
    to keep the classic RSI values.
    """
    if period <= 0:
        raise ValueError("period must be positive")
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - (100.0 / (1.0 + rs))
    # Where avg_loss is exactly 0 (pure uptrend) RSI is defined as 100.
    out = out.where(avg_loss != 0.0, 100.0)
    out[avg_gain.isna() | avg_loss.isna()] = np.nan
    return out


# ---------------------------------------------------------------------------
# Volatility
# ---------------------------------------------------------------------------

def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """True Range: the building block for ATR. Kept as its own function
    because the execution engine also wants raw TR for some spacing
    calculations, not just its smoothed ATR form."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    # First bar has no previous close -> TR is just high-low.
    tr.iloc[0] = (high.iloc[0] - low.iloc[0])
    return tr


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range (Wilder's smoothing). Volatility indicator.

    This is THE volatility measure used everywhere else in this codebase
    (grid spacing, stop distance) -- there is no second ATR implementation
    anywhere in the engine or backtester.
    """
    tr = true_range(high, low, close)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


# ---------------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------------

def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume. Volume indicator.

    OBV[0] = volume[0]; thereafter add volume on up closes, subtract on down
    closes, and hold flat on unchanged closes.
    """
    direction = np.sign(close.diff()).fillna(0.0)
    signed_volume = direction * volume
    signed_volume.iloc[0] = volume.iloc[0]
    return signed_volume.cumsum()
