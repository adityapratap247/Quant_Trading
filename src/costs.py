"""
Cost model: slippage + brokerage + statutory charges.

Kept as one place so backtest fills and any future live order sizing use
the exact same cost function -- this is part of "backtest numbers must
reconcile to live numbers."

Numbers are configurable per instrument; defaults are illustrative
approximations of Indian equity-derivative-style costs (flat brokerage +
STT on sell side for options-style, approximate CTT for commodities), NOT
a claim of current exact statutory rates -- in a real desk these would be
loaded from a rate card, not hardcoded.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostModel:
    slippage_bps: float = 2.0          # price impact, in basis points of fill price
    brokerage_per_order: float = 20.0  # flat fee per executed order (INR)
    stt_ctt_bps: float = 1.0           # securities/commodity transaction tax, bps, sell-side only
    exchange_txn_bps: float = 0.35     # exchange transaction charges, bps, both sides
    gst_rate: float = 0.18             # GST on (brokerage + exchange charges)

    def slipped_price(self, reference_price: float, side: str) -> float:
        """Apply slippage in the adverse direction for the given side."""
        adj = reference_price * (self.slippage_bps / 10_000.0)
        if side == "BUY":
            return reference_price + adj
        elif side == "SELL":
            return reference_price - adj
        raise ValueError(f"unknown side: {side}")

    def total_cost(self, fill_price: float, qty: float, side: str) -> float:
        """Total transaction cost in INR for one fill (excludes the
        slippage, which is already embedded in fill_price via slipped_price)."""
        turnover = fill_price * qty
        exch = turnover * (self.exchange_txn_bps / 10_000.0)
        stt = turnover * (self.stt_ctt_bps / 10_000.0) if side == "SELL" else 0.0
        gst = (self.brokerage_per_order + exch) * self.gst_rate
        return round(self.brokerage_per_order + exch + stt + gst, 4)
