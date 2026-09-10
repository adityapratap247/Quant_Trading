from src.orders import OrderManager, OrderStatus, Side, make_client_order_id


def test_client_order_id_deterministic():
    a = make_client_order_id("strat1", 5, "entry")
    b = make_client_order_id("strat1", 5, "entry")
    assert a == b


def test_client_order_id_differs_by_intent_or_bar():
    base = make_client_order_id("strat1", 5, "entry")
    assert make_client_order_id("strat1", 6, "entry") != base
    assert make_client_order_id("strat1", 5, "grid_add_1") != base


def test_place_is_idempotent():
    om = OrderManager()
    o1 = om.place(Side.BUY, 1.0, "entry", 10, "strat1")
    o2 = om.place(Side.BUY, 1.0, "entry", 10, "strat1")
    assert o1.client_order_id == o2.client_order_id
    assert len(om.orders) == 1  # no duplicate order created on replay


def test_mark_filled_updates_status():
    om = OrderManager()
    order = om.place(Side.BUY, 2.0, "entry", 1, "strat1")
    om.mark_filled(order.client_order_id, fill_price=101.5, broker_order_id="B-1")
    assert order.status == OrderStatus.FILLED
    assert order.fill_price == 101.5


def test_net_position_only_counts_filled_orders():
    om = OrderManager()
    buy = om.place(Side.BUY, 3.0, "entry", 1, "strat1")
    om.place(Side.SELL, 1.0, "grid_reduce", 2, "strat1")  # left PENDING
    om.mark_filled(buy.client_order_id, 100.0, "B-1")
    assert om.net_position() == 3.0  # pending sell must not count


def test_reconcile_adopts_unknown_broker_order():
    om = OrderManager()
    snapshot = {
        "abc123": {
            "side": "BUY",
            "qty": 1.0,
            "status": "FILLED",
            "fill_price": 99.0,
            "broker_order_id": "B-99",
        }
    }
    notes = om.reconcile(snapshot)
    assert len(notes) == 1
    assert om.orders["abc123"].status == OrderStatus.FILLED
    assert om.net_position() == 1.0


def test_reconcile_corrects_status_mismatch():
    om = OrderManager()
    order = om.place(Side.BUY, 1.0, "entry", 1, "strat1")
    # Locally we still think it's pending, but broker says it filled
    # (e.g. we crashed before processing the fill confirmation).
    snapshot = {
        order.client_order_id: {
            "side": "BUY",
            "qty": 1.0,
            "status": "FILLED",
            "fill_price": 105.0,
            "broker_order_id": "B-5",
        }
    }
    notes = om.reconcile(snapshot)
    assert len(notes) == 1
    assert order.status == OrderStatus.FILLED
    assert order.fill_price == 105.0


def test_reconcile_no_mismatch_no_notes():
    om = OrderManager()
    order = om.place(Side.BUY, 1.0, "entry", 1, "strat1")
    om.mark_filled(order.client_order_id, 100.0, "B-1")
    snapshot = {
        order.client_order_id: {
            "side": "BUY",
            "qty": 1.0,
            "status": "FILLED",
            "fill_price": 100.0,
            "broker_order_id": "B-1",
        }
    }
    notes = om.reconcile(snapshot)
    assert notes == []
