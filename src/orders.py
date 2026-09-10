"""
Order and state management.

Covers the "idempotent placement, order-state reconciliation after
restarts, position and P&L truth" requirement at the level a 3-day
assignment can actually demonstrate:

- Every order gets a deterministic client_order_id derived from
  (strategy_id, bar_index, intent) so re-submitting the same intent after a
  crash/restart is a no-op instead of a duplicate order.
- OrderManager keeps local state (its own book) and can `reconcile` against
  an external "broker truth" snapshot, flagging and resolving mismatches --
  this is the same shape a real Kite Connect reconciliation pass would take,
  with the broker API swapped for a stub.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


def make_client_order_id(strategy_id: str, bar_index: int, intent: str) -> str:
    """Deterministic idempotency key. Same (strategy, bar, intent) always
    produces the same id, so replaying an event stream after a crash never
    creates a second order for the same decision."""
    raw = f"{strategy_id}|{bar_index}|{intent}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


@dataclass
class Order:
    client_order_id: str
    side: Side
    qty: float
    reason: str                 # e.g. "grid_add", "stop_reverse", "kill_switch_flatten"
    bar_index: int
    status: OrderStatus = OrderStatus.PENDING
    fill_price: Optional[float] = None
    broker_order_id: Optional[str] = None


@dataclass
class OrderManager:
    """Local order book. `place` is idempotent: submitting the same
    client_order_id twice returns the existing order instead of creating a
    duplicate, which is what makes restart-and-replay safe."""

    orders: Dict[str, Order] = field(default_factory=dict)

    def place(self, side: Side, qty: float, reason: str, bar_index: int, strategy_id: str) -> Order:
        coid = make_client_order_id(strategy_id, bar_index, reason)
        if coid in self.orders:
            return self.orders[coid]  # idempotent: no duplicate submission
        order = Order(client_order_id=coid, side=side, qty=qty, reason=reason, bar_index=bar_index)
        self.orders[coid] = order
        return order

    def mark_filled(self, client_order_id: str, fill_price: float, broker_order_id: str) -> None:
        order = self.orders[client_order_id]
        order.status = OrderStatus.FILLED
        order.fill_price = fill_price
        order.broker_order_id = broker_order_id

    def open_orders(self) -> List[Order]:
        return [o for o in self.orders.values() if o.status == OrderStatus.PENDING]

    def reconcile(self, broker_snapshot: Dict[str, dict]) -> List[str]:
        """Reconcile local book against a broker "truth" snapshot after a
        restart. broker_snapshot maps client_order_id -> {status, fill_price,
        broker_order_id}. Returns a list of human-readable mismatch notes
        for anything that had to be corrected (this is what would get
        logged/alerted in production)."""
        notes: List[str] = []

        for coid, remote in broker_snapshot.items():
            local = self.orders.get(coid)
            if local is None:
                # Broker knows about an order we have no local record of
                # (e.g. we crashed before persisting it) -- adopt it as truth.
                notes.append(f"adopted unknown order {coid} from broker snapshot")
                self.orders[coid] = Order(
                    client_order_id=coid,
                    side=Side(remote["side"]),
                    qty=remote["qty"],
                    reason=remote.get("reason", "recovered"),
                    bar_index=remote.get("bar_index", -1),
                    status=OrderStatus(remote["status"]),
                    fill_price=remote.get("fill_price"),
                    broker_order_id=remote.get("broker_order_id"),
                )
                continue

            remote_status = OrderStatus(remote["status"])
            if local.status != remote_status:
                notes.append(
                    f"{coid}: local status {local.status.value} != broker status "
                    f"{remote_status.value}; adopting broker status"
                )
                local.status = remote_status
                local.fill_price = remote.get("fill_price", local.fill_price)
                local.broker_order_id = remote.get("broker_order_id", local.broker_order_id)

        return notes

    def net_position(self) -> float:
        """Position truth derived solely from FILLED orders -- this is the
        single source of truth the engine's position cap / kill switch
        checks against, so it can never drift from what actually executed."""
        pos = 0.0
        for o in self.orders.values():
            if o.status != OrderStatus.FILLED:
                continue
            pos += o.qty if o.side == Side.BUY else -o.qty
        return pos
