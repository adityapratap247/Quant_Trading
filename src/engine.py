"""
Live grid and stop-and-reverse execution engine.

This is the piece that decides WHAT to trade, bar by bar. It is
deliberately decoupled from fills/costs (that's the backtester's job) and
from raw data fetching (that's a broker adapter's job) -- the same
`on_bar` call is meant to be driven by a live WebSocket bar-close event or
by a backtest loop without any changes, which is what makes backtest
numbers reconcile to live numbers.

Strategy logic (kept deliberately simple so the *engineering* -- spacing,
pyramiding, caps, kill switch, idempotent orders -- is what's being
demonstrated, not a claim of alpha):

  - Direction is set by a trend filter (fast EMA vs slow EMA).
  - Flat -> enter one unit in the trend direction.
  - In position, favourable moves of `atr_multiplier * ATR` add a pyramid
    unit (up to `max_pyramids`, bounded by `position_cap`).
  - Adverse moves of `stop_multiplier * ATR` from the position's high-water
    entry trigger a stop-and-reverse: flatten, then open in the other
    direction.
  - A portfolio-level kill switch flattens everything and halts new entries
    once drawdown from equity peak exceeds `kill_switch_dd_pct`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from .orders import OrderManager, Side


class Direction(Enum):
    FLAT = 0
    LONG = 1
    SHORT = -1


@dataclass
class EngineConfig:
    strategy_id: str = "grid_sar_v1"
    base_qty: float = 1.0
    atr_multiplier: float = 1.0     # grid spacing = atr_multiplier * ATR
    stop_multiplier: float = 2.5    # stop distance = stop_multiplier * ATR
    max_pyramids: int = 4           # max additional units beyond the first
    position_cap: float = 5.0       # hard cap on |net position|, in units
    kill_switch_dd_pct: float = 0.15  # 15% drawdown from equity peak halts trading


@dataclass
class EngineState:
    direction: Direction = Direction.FLAT
    units: int = 0                        # number of base_qty units currently held
    entry_reference_price: Optional[float] = None  # last price a unit was added at
    equity_peak: float = 0.0
    killed: bool = False


class GridReverseEngine:
    """Stateful per-instrument execution engine."""

    def __init__(self, config: EngineConfig):
        self.config = config
        self.state = EngineState()

    # -- kill switch -------------------------------------------------

    def update_equity_and_check_kill_switch(self, equity: float) -> bool:
        """Call once per bar with mark-to-market equity. Returns True if the
        kill switch fired on this call (caller should flatten via
        `force_flatten`)."""
        st = self.state
        st.equity_peak = max(st.equity_peak, equity)
        if st.killed or st.equity_peak <= 0:
            return False
        drawdown = (st.equity_peak - equity) / st.equity_peak
        if drawdown >= self.config.kill_switch_dd_pct:
            st.killed = True
            return True
        return False

    def force_flatten(self, bar_index: int, order_manager: OrderManager) -> Optional["EngineOrderIntent"]:
        st = self.state
        if st.units == 0:
            return None
        side = Side.SELL if st.direction == Direction.LONG else Side.BUY
        qty = self.config.base_qty * st.units
        order = order_manager.place(side, qty, "kill_switch_flatten", bar_index, self.config.strategy_id)
        st.units = 0
        st.direction = Direction.FLAT
        st.entry_reference_price = None
        return EngineOrderIntent(order=order, note="kill switch: flattened all units")

    # -- main decision loop -------------------------------------------------

    def on_bar(
        self,
        bar_index: int,
        close: float,
        atr_value: float,
        trend_bullish: Optional[bool],
        order_manager: OrderManager,
    ) -> List["EngineOrderIntent"]:
        """Evaluate one closed bar and return the list of order intents
        generated (usually 0 or 1; a stop-and-reverse produces 2: a flatten
        then a new entry).

        `atr_value` / `trend_bullish` being None (not enough warm-up bars
        yet) is a valid state -- the engine simply does nothing, which is
        part of the no-lookahead discipline: it never backfills a decision
        using data that wasn't available yet.
        """
        st = self.state
        cfg = self.config
        intents: List[EngineOrderIntent] = []

        if st.killed:
            return intents
        if atr_value is None or trend_bullish is None or atr_value <= 0:
            return intents  # indicators not warmed up yet -- no decision

        if st.direction == Direction.FLAT:
            side = Side.BUY if trend_bullish else Side.SELL
            order = order_manager.place(side, cfg.base_qty, "entry", bar_index, cfg.strategy_id)
            st.direction = Direction.LONG if trend_bullish else Direction.SHORT
            st.units = 1
            st.entry_reference_price = close
            intents.append(EngineOrderIntent(order=order, note="initial entry"))
            return intents

        ref = st.entry_reference_price
        grid_spacing = cfg.atr_multiplier * atr_value
        stop_distance = cfg.stop_multiplier * atr_value

        if st.direction == Direction.LONG:
            adverse_move = ref - close
            favourable_move = close - ref

            if adverse_move >= stop_distance:
                intents.append(self._stop_and_reverse(bar_index, order_manager, to_direction=Direction.SHORT, close=close))
                return intents

            if favourable_move >= grid_spacing and st.units - 1 < cfg.max_pyramids:
                total_qty_if_added = cfg.base_qty * (st.units + 1)
                if total_qty_if_added <= cfg.position_cap:
                    order = order_manager.place(Side.BUY, cfg.base_qty, f"grid_add_{st.units + 1}", bar_index, cfg.strategy_id)
                    st.units += 1
                    st.entry_reference_price = close
                    intents.append(EngineOrderIntent(order=order, note=f"pyramid add #{st.units}"))
                # else: at position cap -- silently skip, this is intentional risk control

        else:  # SHORT
            adverse_move = close - ref
            favourable_move = ref - close

            if adverse_move >= stop_distance:
                intents.append(self._stop_and_reverse(bar_index, order_manager, to_direction=Direction.LONG, close=close))
                return intents

            if favourable_move >= grid_spacing and st.units - 1 < cfg.max_pyramids:
                total_qty_if_added = cfg.base_qty * (st.units + 1)
                if total_qty_if_added <= cfg.position_cap:
                    order = order_manager.place(Side.SELL, cfg.base_qty, f"grid_add_{st.units + 1}", bar_index, cfg.strategy_id)
                    st.units += 1
                    st.entry_reference_price = close
                    intents.append(EngineOrderIntent(order=order, note=f"pyramid add #{st.units}"))

        return intents

    def _stop_and_reverse(self, bar_index: int, order_manager: OrderManager, to_direction: Direction, close: float) -> "EngineOrderIntent":
        st = self.state
        cfg = self.config
        flatten_side = Side.SELL if st.direction == Direction.LONG else Side.BUY
        flatten_qty = cfg.base_qty * st.units
        order_manager.place(flatten_side, flatten_qty, "stop_reverse_flatten", bar_index, cfg.strategy_id)

        entry_side = Side.BUY if to_direction == Direction.LONG else Side.SELL
        new_order = order_manager.place(entry_side, cfg.base_qty, "stop_reverse_entry", bar_index, cfg.strategy_id)

        st.direction = to_direction
        st.units = 1
        st.entry_reference_price = close
        return EngineOrderIntent(order=new_order, note=f"stop-and-reverse -> {to_direction.name}")


@dataclass
class EngineOrderIntent:
    order: object
    note: str = ""
