"""
Backtest harness.

Design points, each tied directly to the brief:

- No lookahead: decisions at bar i use only indicator values computable
  from bars <= i (indicators.py is causal). Fills for a decision made at
  bar i execute at bar i+1's OPEN, never at bar i's own close/high/low --
  you cannot trade at a price using information (the very close that
  triggered the signal) that arrives at the same instant as the decision.
- Bar-accurate fills: the fill price is a real, quoted OHLCV price
  (next bar's open) with slippage/cost applied on top, not an
  idealized mid-price.
- Same `GridReverseEngine.on_bar` call this harness drives is exactly what
  a live bar-close handler would call -- so a backtest run and a live run
  of the same engine object are running identical decision code. That is
  the mechanism by which "backtest numbers must reconcile to live numbers":
  there is only one implementation of the strategy logic, not a
  vectorized-backtest version and a separate live version.
- Walk-forward: `walk_forward_windows` produces chronological,
  non-overlapping test windows; the engine's state is reset at the start
  of each window so no information (including position state) leaks across
  a fold boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from .costs import CostModel
from .engine import EngineConfig, GridReverseEngine
from .indicators import atr as atr_fn
from .indicators import ema
from .orders import OrderManager, OrderStatus, Side


def compute_signal_frame(
    df: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    atr_period: int = 14,
) -> pd.DataFrame:
    """Attach the (causal) indicator columns the engine needs. Every column
    here is computable using only data up to and including that row."""
    out = df.copy()
    out["ema_fast"] = ema(out["close"], fast_period)
    out["ema_slow"] = ema(out["close"], slow_period)
    out["atr"] = atr_fn(out["high"], out["low"], out["close"], atr_period)
    # object dtype (not bool) so warmup rows can hold a genuine NaN instead
    # of silently coercing to False, which would look like a real bearish
    # signal to the engine.
    trend_bullish = (out["ema_fast"] > out["ema_slow"]).astype(object)
    warmed = out["ema_fast"].notna() & out["ema_slow"].notna() & out["atr"].notna()
    trend_bullish[~warmed] = np.nan
    out["trend_bullish"] = trend_bullish
    return out


@dataclass
class BlotterRow:
    bar_index: int
    timestamp: object
    side: str
    qty: float
    fill_price: float
    cost: float
    reason: str


@dataclass
class BacktestResult:
    blotter: List[BlotterRow] = field(default_factory=list)
    equity_curve: pd.Series = None
    final_equity: float = 0.0
    starting_cash: float = 0.0
    kill_switch_fired: bool = False
    kill_switch_bar: Optional[int] = None

    def metrics(self) -> dict:
        eq = self.equity_curve.dropna()
        if len(eq) < 2:
            return {"trades": len(self.blotter), "total_return_pct": 0.0}
        rets = eq.pct_change().dropna()
        total_return_pct = (eq.iloc[-1] / self.starting_cash - 1.0) * 100.0
        running_max = eq.cummax()
        drawdown = (eq - running_max) / running_max
        max_dd_pct = drawdown.min() * 100.0
        sharpe = 0.0
        if rets.std() > 0:
            bars_per_year = 252 * 75  # approx 5-min bars in an NSE trading year
            sharpe = (rets.mean() / rets.std()) * np.sqrt(bars_per_year)
        return {
            "trades": len(self.blotter),
            "total_return_pct": round(total_return_pct, 3),
            "max_drawdown_pct": round(max_dd_pct, 3),
            "sharpe_annualized_approx": round(sharpe, 3),
            "final_equity": round(self.equity_curve.iloc[-1], 2),
            "kill_switch_fired": self.kill_switch_fired,
        }


def run_backtest(
    df: pd.DataFrame,
    engine_config: EngineConfig,
    cost_model: CostModel,
    starting_cash: float = 1_000_000.0,
    contract_multiplier: float = 1.0,
) -> BacktestResult:
    """Bar-accurate event loop.

    At each bar i (i from first fully-warmed bar to len-2):
      1. engine.on_bar() looks at bar i's close/ATR/trend and emits order
         intents (PENDING orders).
      2. Those orders are filled at bar i+1's OPEN, with slippage and costs
         applied -- never at bar i's own price.
    This one-bar delay is what keeps the loop lookahead-free.
    """
    sig = compute_signal_frame(df)
    engine = GridReverseEngine(engine_config)
    om = OrderManager()

    cash = starting_cash
    position = 0.0  # in units of base_qty terms (contracts)
    blotter: List[BlotterRow] = []
    equity_series = pd.Series(index=df.index, dtype=float)

    kill_switch_fired = False
    kill_switch_bar = None

    n = len(sig)
    for i in range(n - 1):  # need i+1 to exist for the fill
        row = sig.iloc[i]
        close_i = row["close"]
        atr_i = row["atr"] if pd.notna(row["atr"]) else None
        trend_i = None if pd.isna(row["trend_bullish"]) else bool(row["trend_bullish"])

        # Mark-to-market equity using bar i's own close (available at bar i,
        # so this is not lookahead) BEFORE any new decision this bar.
        equity_now = cash + position * close_i * contract_multiplier
        equity_series.iloc[i] = equity_now

        if not kill_switch_fired:
            fired = engine.update_equity_and_check_kill_switch(equity_now)
            if fired:
                kill_switch_fired = True
                kill_switch_bar = i
                engine.force_flatten(i, om)

        if not kill_switch_fired:
            engine.on_bar(i, close_i, atr_i, trend_i, om)

        # Fill any newly-placed PENDING orders at bar i+1's open.
        next_open = sig.iloc[i + 1]["open"]
        for order in list(om.open_orders()):
            raw_price = cost_model.slipped_price(next_open, order.side.value)
            cost = cost_model.total_cost(raw_price, order.qty, order.side.value)
            om.mark_filled(order.client_order_id, raw_price, broker_order_id=f"SIM-{order.client_order_id}")

            signed_qty = order.qty if order.side == Side.BUY else -order.qty
            cash -= signed_qty * raw_price * contract_multiplier
            cash -= cost
            position += signed_qty

            blotter.append(
                BlotterRow(
                    bar_index=i,
                    timestamp=sig.index[i + 1],
                    side=order.side.value,
                    qty=order.qty,
                    fill_price=raw_price,
                    cost=cost,
                    reason=order.reason,
                )
            )

    # Final bar mark
    equity_series.iloc[n - 1] = cash + position * sig.iloc[n - 1]["close"] * contract_multiplier

    result = BacktestResult(
        blotter=blotter,
        equity_curve=equity_series,
        final_equity=equity_series.iloc[-1],
        starting_cash=starting_cash,
        kill_switch_fired=kill_switch_fired,
        kill_switch_bar=kill_switch_bar,
    )
    return result


def walk_forward_windows(n_bars: int, n_folds: int = 4, warmup: int = 40) -> List[Tuple[int, int]]:
    """Chronological, non-overlapping (start, end) index windows for
    walk-forward evaluation. Each window includes its own `warmup` bars of
    lead-in so indicators inside that window warm up on in-window data only
    -- no fold ever uses indicator state computed from a later fold, and no
    fold's engine carries position state into the next fold (the caller
    constructs a fresh engine per window)."""
    if n_folds < 1:
        raise ValueError("n_folds must be >= 1")
    usable = n_bars - warmup
    if usable < n_folds * 10:
        raise ValueError("not enough bars for the requested number of folds")
    fold_size = usable // n_folds
    windows = []
    cursor = 0
    for f in range(n_folds):
        start = cursor
        end = start + warmup + fold_size if f < n_folds - 1 else n_bars
        windows.append((start, min(end, n_bars)))
        cursor = start + warmup + fold_size
    return windows


def run_walk_forward(
    df: pd.DataFrame,
    engine_config: EngineConfig,
    cost_model: CostModel,
    n_folds: int = 4,
    starting_cash: float = 1_000_000.0,
) -> List[dict]:
    """Run an independent backtest per walk-forward window (fresh engine
    and fresh order manager each time) and report per-fold metrics."""
    windows = walk_forward_windows(len(df), n_folds=n_folds)
    fold_results = []
    for fold_idx, (start, end) in enumerate(windows):
        window_df = df.iloc[start:end].reset_index(drop=False)
        window_df = window_df.set_index("timestamp")
        result = run_backtest(window_df, engine_config, cost_model, starting_cash=starting_cash)
        m = result.metrics()
        m["fold"] = fold_idx
        m["start"] = str(df.index[start])
        m["end"] = str(df.index[end - 1])
        m["bars"] = end - start
        fold_results.append(m)
    return fold_results
