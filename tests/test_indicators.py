import numpy as np
import pandas as pd
import pytest

from src.indicators import atr, ema, obv, rsi, sma, true_range


def test_sma_matches_hand_calculation():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    result = sma(s, 3)
    assert result.iloc[2] == pytest.approx(2.0)
    assert result.iloc[3] == pytest.approx(3.0)
    assert result.iloc[4] == pytest.approx(4.0)
    assert result.iloc[:2].isna().all()


def test_ema_converges_to_constant_series():
    s = pd.Series([10.0] * 50)
    result = ema(s, 10)
    assert result.iloc[-1] == pytest.approx(10.0, abs=1e-6)


def test_rsi_is_100_for_strictly_increasing_series():
    s = pd.Series(np.arange(1, 40, dtype=float))
    result = rsi(s, period=14)
    assert result.iloc[-1] == pytest.approx(100.0)


def test_rsi_is_0_for_strictly_decreasing_series():
    s = pd.Series(np.arange(40, 1, -1, dtype=float))
    result = rsi(s, period=14)
    assert result.iloc[-1] == pytest.approx(0.0)


def test_rsi_bounded_0_100_on_random_walk():
    rng = np.random.default_rng(0)
    s = pd.Series(100 + np.cumsum(rng.normal(0, 1, 200)))
    result = rsi(s, period=14).dropna()
    assert (result >= 0).all() and (result <= 100).all()


def test_true_range_first_bar_is_high_minus_low():
    high = pd.Series([105.0, 110.0])
    low = pd.Series([95.0, 100.0])
    close = pd.Series([100.0, 108.0])
    tr = true_range(high, low, close)
    assert tr.iloc[0] == pytest.approx(10.0)


def test_true_range_captures_gap():
    # Gap up: previous close 100, today's low is 105 -> range vs prev close (5)
    # should dominate over today's high-low range if that's larger.
    high = pd.Series([100.0, 120.0])
    low = pd.Series([95.0, 105.0])
    close = pd.Series([100.0, 118.0])
    tr = true_range(high, low, close)
    # max(120-105, |120-100|, |105-100|) = max(15, 20, 5) = 20
    assert tr.iloc[1] == pytest.approx(20.0)


def test_atr_positive_and_causal_length():
    rng = np.random.default_rng(1)
    n = 60
    close = pd.Series(100 + np.cumsum(rng.normal(0, 1, n)))
    high = close + np.abs(rng.normal(0, 1, n))
    low = close - np.abs(rng.normal(0, 1, n))
    result = atr(high, low, close, period=14)
    assert result.dropna().gt(0).all()
    # Same-length output, causal (no data from the future needed to produce
    # the first non-NaN value beyond the warmup window).
    assert len(result) == n


def test_obv_accumulates_on_up_and_down_closes():
    close = pd.Series([10, 11, 10.5, 12])
    volume = pd.Series([100, 100, 100, 100])
    result = obv(close, volume)
    # bar0: 100 (seed), bar1 up: +100 -> 200, bar2 down: -100 -> 100, bar3 up: +100 -> 200
    assert list(result) == [100, 200, 100, 200]


def test_indicators_reject_nonpositive_period():
    s = pd.Series([1.0, 2.0, 3.0])
    with pytest.raises(ValueError):
        sma(s, 0)
    with pytest.raises(ValueError):
        ema(s, -1)
    with pytest.raises(ValueError):
        rsi(s, 0)
