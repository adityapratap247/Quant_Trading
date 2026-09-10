import pytest

from src.costs import CostModel


def test_slippage_moves_buy_price_up():
    cm = CostModel(slippage_bps=10.0)
    price = cm.slipped_price(100.0, "BUY")
    assert price > 100.0
    assert price == pytest.approx(100.1)


def test_slippage_moves_sell_price_down():
    cm = CostModel(slippage_bps=10.0)
    price = cm.slipped_price(100.0, "SELL")
    assert price < 100.0
    assert price == pytest.approx(99.9)


def test_slippage_rejects_unknown_side():
    cm = CostModel()
    with pytest.raises(ValueError):
        cm.slipped_price(100.0, "HOLD")


def test_total_cost_includes_stt_only_on_sell():
    cm = CostModel(brokerage_per_order=20.0, stt_ctt_bps=1.0, exchange_txn_bps=0.0, gst_rate=0.0)
    buy_cost = cm.total_cost(100.0, 10, "BUY")
    sell_cost = cm.total_cost(100.0, 10, "SELL")
    assert sell_cost > buy_cost
    assert buy_cost == pytest.approx(20.0)  # only flat brokerage, no exch/gst in this config


def test_total_cost_scales_with_turnover():
    cm = CostModel(brokerage_per_order=0.0, stt_ctt_bps=0.0, exchange_txn_bps=1.0, gst_rate=0.0)
    small = cm.total_cost(100.0, 1, "BUY")
    large = cm.total_cost(100.0, 100, "BUY")
    assert large == pytest.approx(small * 100, rel=1e-6)
