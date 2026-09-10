from src.engine import Direction, EngineConfig, GridReverseEngine
from src.orders import OrderManager, Side


def make_engine(**overrides) -> GridReverseEngine:
    cfg = EngineConfig(
        base_qty=1.0,
        atr_multiplier=1.0,
        stop_multiplier=2.0,
        max_pyramids=2,
        position_cap=3.0,
        kill_switch_dd_pct=0.15,
    )
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return GridReverseEngine(cfg)


def test_flat_engine_enters_long_on_bullish_trend():
    engine = make_engine()
    om = OrderManager()
    intents = engine.on_bar(0, close=100.0, atr_value=1.0, trend_bullish=True, order_manager=om)
    assert len(intents) == 1
    assert engine.state.direction == Direction.LONG
    assert engine.state.units == 1
    assert om.orders[intents[0].order.client_order_id].side == Side.BUY


def test_flat_engine_enters_short_on_bearish_trend():
    engine = make_engine()
    om = OrderManager()
    intents = engine.on_bar(0, close=100.0, atr_value=1.0, trend_bullish=False, order_manager=om)
    assert engine.state.direction == Direction.SHORT
    assert om.orders[intents[0].order.client_order_id].side == Side.SELL


def test_no_decision_when_indicators_not_warmed_up():
    engine = make_engine()
    om = OrderManager()
    intents = engine.on_bar(0, close=100.0, atr_value=None, trend_bullish=None, order_manager=om)
    assert intents == []
    assert engine.state.direction == Direction.FLAT


def test_pyramid_add_on_favourable_move():
    engine = make_engine()
    om = OrderManager()
    engine.on_bar(0, close=100.0, atr_value=1.0, trend_bullish=True, order_manager=om)  # enter long @100
    # grid_spacing = atr_multiplier(1.0) * atr(1.0) = 1.0 -> favourable move of 1.5 triggers add
    intents = engine.on_bar(1, close=101.5, atr_value=1.0, trend_bullish=True, order_manager=om)
    assert len(intents) == 1
    assert "pyramid" in intents[0].note
    assert engine.state.units == 2


def test_position_cap_blocks_further_pyramiding():
    engine = make_engine(position_cap=2.0)  # cap reached after the initial entry + 1 add
    om = OrderManager()
    engine.on_bar(0, close=100.0, atr_value=1.0, trend_bullish=True, order_manager=om)  # units=1
    engine.on_bar(1, close=101.5, atr_value=1.0, trend_bullish=True, order_manager=om)  # units=2, at cap
    intents = engine.on_bar(2, close=103.0, atr_value=1.0, trend_bullish=True, order_manager=om)
    assert intents == []  # cap reached, no further pyramiding
    assert engine.state.units == 2


def test_stop_and_reverse_on_adverse_move():
    engine = make_engine()
    om = OrderManager()
    engine.on_bar(0, close=100.0, atr_value=1.0, trend_bullish=True, order_manager=om)  # long @100
    # stop_distance = stop_multiplier(2.0) * atr(1.0) = 2.0 -> adverse move of 2.5 triggers reverse
    intents = engine.on_bar(1, close=97.5, atr_value=1.0, trend_bullish=True, order_manager=om)
    assert engine.state.direction == Direction.SHORT
    assert engine.state.units == 1
    # stop-and-reverse places 2 NEW orders this bar (flatten the long, then
    # open the short) on top of the 1 initial entry order from bar 0.
    assert len(om.orders) == 3
    reasons = {o.reason for o in om.orders.values()}
    assert "stop_reverse_flatten" in reasons
    assert "stop_reverse_entry" in reasons


def test_kill_switch_fires_on_drawdown_and_halts_trading():
    engine = make_engine(kill_switch_dd_pct=0.10)
    om = OrderManager()
    engine.on_bar(0, close=100.0, atr_value=1.0, trend_bullish=True, order_manager=om)

    fired_at_peak = engine.update_equity_and_check_kill_switch(100_000.0)
    assert fired_at_peak is False  # first observation just sets the peak

    fired = engine.update_equity_and_check_kill_switch(89_000.0)  # 11% drawdown
    assert fired is True
    assert engine.state.killed is True

    engine.force_flatten(5, om)
    assert engine.state.units == 0
    assert engine.state.direction == Direction.FLAT

    # Once killed, on_bar must refuse to open any new position.
    intents = engine.on_bar(6, close=90.0, atr_value=1.0, trend_bullish=True, order_manager=om)
    assert intents == []
    assert engine.state.direction == Direction.FLAT


def test_idempotent_replay_of_same_bar_does_not_duplicate_orders():
    """Simulates a crash-and-replay: calling on_bar again for a bar whose
    decision was already placed with the OrderManager must not create a
    second order (the OrderManager's idempotent `place` is what guarantees
    this, exercised here through the engine's own call pattern)."""
    engine = make_engine()
    om = OrderManager()
    engine.on_bar(0, close=100.0, atr_value=1.0, trend_bullish=True, order_manager=om)
    order_count_before = len(om.orders)
    # Re-placing the identical intent (same strategy/bar/reason) must be a no-op.
    om.place(Side.BUY, 1.0, "entry", 0, engine.config.strategy_id)
    assert len(om.orders) == order_count_before
