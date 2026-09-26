"""Simulated order lifecycle: OPEN → FILLED / CANCELLED / REJECTED (§3).

Everything here is a simulation. There is no broker client in this package and
no code path that reaches a real venue — the service contract treats live
integration as a separately negotiated scope, so the default build practises
the workflow without risking anything.

Two behaviours are modelled carefully because they are what an operator has to
rehearse:

  * **Manual fill and cancel** (§3 "모의주문 수동 체결과 취소"). A simulated
    order does not fill itself on a timer. The operator fills it, which forces
    them to see the order sitting open and decide — the same decision a real
    resting order demands.

  * **Rejection carries a reason** (§3 "조건이 실행되지 않은 이유 표시").
    A rejected order records which guard stopped it, so "nothing happened" is
    never the whole story.

Order ids are deterministic per (rule, revision, trigger sequence) so the
idempotency guard in `guards.py` can recognise a duplicate submission of the
same logical trigger after a restart.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from core.rules.model import OrderKind, Side


class OrderStatus(str, Enum):
    OPEN = "OPEN"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

    @property
    def terminal(self) -> bool:
        return self is not OrderStatus.OPEN


@dataclass(frozen=True)
class SimulatedOrder:
    id: str
    rule_id: str
    rule_revision: int
    rule_name: str
    symbol: str
    market: str
    side: Side
    kind: OrderKind
    quantity: Decimal
    limit_price: Optional[Decimal]
    notional: Optional[Decimal]
    trigger_price: Decimal
    status: OrderStatus = OrderStatus.OPEN
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    settled_at: Optional[datetime] = None
    fill_price: Optional[Decimal] = None
    reason: str = ""                    # why rejected, or why cancelled

    @property
    def open(self) -> bool:
        return self.status is OrderStatus.OPEN

    @property
    def age_seconds(self) -> float:
        end = self.settled_at or datetime.now(timezone.utc)
        return (end - self.created_at).total_seconds()

    def describe(self) -> str:
        price = (f"limit {self.limit_price:,}" if self.kind is OrderKind.LIMIT
                 and self.limit_price is not None else "market")
        return (f"{self.side.value} {self.quantity:,} {self.symbol} "
                f"({price}) — {self.status.value}")


def order_id(rule_id: str, revision: int, sequence: int) -> str:
    """Deterministic, so the same logical trigger cannot be submitted twice."""
    return f"{rule_id}-r{revision}-t{sequence}"


class OrderBook:
    """In-memory book of simulated orders. Thread-safe."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._orders: dict[str, SimulatedOrder] = {}

    # -- reads ---------------------------------------------------------------
    def get(self, oid: str) -> Optional[SimulatedOrder]:
        with self._lock:
            return self._orders.get(oid)

    def all(self) -> tuple[SimulatedOrder, ...]:
        with self._lock:
            return tuple(sorted(self._orders.values(),
                                key=lambda o: o.created_at, reverse=True))

    def open_orders(self) -> tuple[SimulatedOrder, ...]:
        return tuple(o for o in self.all() if o.open)

    def for_rule(self, rule_id: str) -> tuple[SimulatedOrder, ...]:
        return tuple(o for o in self.all() if o.rule_id == rule_id)

    def exists(self, oid: str) -> bool:
        with self._lock:
            return oid in self._orders

    def counts_today(self, *, now: Optional[datetime] = None) -> dict[str, int]:
        now = now or datetime.now(timezone.utc)
        today = now.date()
        tally = {s.value: 0 for s in OrderStatus}
        for order in self.all():
            if order.created_at.date() == today:
                tally[order.status.value] += 1
        return tally

    def notional_today(self, *, now: Optional[datetime] = None) -> Decimal:
        """Cash committed today, counting everything that was not rejected."""
        now = now or datetime.now(timezone.utc)
        today = now.date()
        total = Decimal(0)
        for order in self.all():
            if order.created_at.date() != today:
                continue
            if order.status is OrderStatus.REJECTED:
                continue
            total += order.notional or Decimal(0)
        return total

    # -- writes --------------------------------------------------------------
    def place(self, order: SimulatedOrder) -> Optional[SimulatedOrder]:
        """Insert, or return None if this id is already present.

        The duplicate check lives inside the lock rather than in a separate
        `exists()` call by the caller: two evaluation passes overlapping on the
        same rule would both pass a check-then-place and place the same logical
        trigger twice. Returning None makes the guard atomic.
        """
        with self._lock:
            if order.id in self._orders:
                return None
            self._orders[order.id] = order
            return order

    def _settle(self, oid: str, status: OrderStatus, *,
                fill_price: Optional[Decimal] = None,
                reason: str = "") -> tuple[bool, str]:
        with self._lock:
            order = self._orders.get(oid)
            if order is None:
                return False, "No such order."
            if order.status.terminal:
                return False, f"Order is already {order.status.value.lower()}."
            self._orders[oid] = replace(
                order, status=status, settled_at=datetime.now(timezone.utc),
                fill_price=fill_price, reason=reason,
            )
            return True, ""

    def fill(self, oid: str, price: Decimal) -> tuple[bool, str]:
        """Operator-initiated fill (§3). Never happens on its own."""
        return self._settle(oid, OrderStatus.FILLED, fill_price=price)

    def cancel(self, oid: str, reason: str = "cancelled by operator") -> tuple[bool, str]:
        return self._settle(oid, OrderStatus.CANCELLED, reason=reason)

    def reject(self, order: SimulatedOrder, reason: str) -> SimulatedOrder:
        """Record a trigger that a guard stopped, so the refusal is visible."""
        rejected = replace(order, status=OrderStatus.REJECTED,
                           settled_at=datetime.now(timezone.utc), reason=reason)
        with self._lock:
            self._orders[rejected.id] = rejected
        return rejected

    def cancel_all_open(self, reason: str) -> int:
        count = 0
        for order in self.open_orders():
            ok, _ = self.cancel(order.id, reason)
            count += int(ok)
        return count

    def reset(self) -> None:
        """§3 "연습 시나리오 초기화" — clear the practice book."""
        with self._lock:
            self._orders.clear()

    def snapshot(self) -> list[dict]:
        return [
            {
                "id": o.id, "rule_id": o.rule_id, "rule_revision": o.rule_revision,
                "rule_name": o.rule_name, "symbol": o.symbol, "market": o.market,
                "side": o.side.value, "kind": o.kind.value,
                "quantity": str(o.quantity),
                "limit_price": str(o.limit_price) if o.limit_price is not None else None,
                "notional": str(o.notional) if o.notional is not None else None,
                "trigger_price": str(o.trigger_price), "status": o.status.value,
                "created_at": o.created_at.isoformat(),
                "settled_at": o.settled_at.isoformat() if o.settled_at else None,
                "fill_price": str(o.fill_price) if o.fill_price is not None else None,
                "reason": o.reason,
            }
            for o in self.all()
        ]

    def restore(self, rows: list[dict]) -> None:
        with self._lock:
            self._orders.clear()
            for raw in rows or []:
                try:
                    self._orders[raw["id"]] = SimulatedOrder(
                        id=raw["id"], rule_id=raw["rule_id"],
                        rule_revision=int(raw.get("rule_revision") or 1),
                        rule_name=raw.get("rule_name", ""), symbol=raw["symbol"],
                        market=raw.get("market", ""), side=Side(raw["side"]),
                        kind=OrderKind(raw["kind"]),
                        quantity=Decimal(raw["quantity"]),
                        limit_price=Decimal(raw["limit_price"]) if raw.get("limit_price") else None,
                        notional=Decimal(raw["notional"]) if raw.get("notional") else None,
                        trigger_price=Decimal(raw.get("trigger_price") or 0),
                        status=OrderStatus(raw["status"]),
                        created_at=datetime.fromisoformat(raw["created_at"]),
                        settled_at=datetime.fromisoformat(raw["settled_at"]) if raw.get("settled_at") else None,
                        fill_price=Decimal(raw["fill_price"]) if raw.get("fill_price") else None,
                        reason=raw.get("reason", ""),
                    )
                except Exception:
                    continue          # one malformed row must not lose the book
