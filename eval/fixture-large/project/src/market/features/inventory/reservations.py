"""INV-02, INV-03, INV-04, INV-05, INV-06, INV-07: all-or-nothing stock holds."""
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from market.features.catalog.category_rules import is_stock_tracked
from market.features.catalog.product_store import get_product
from market.features.inventory.low_stock import check_low_stock
from market.features.inventory.stock_store import available, on_hand
from market.infra import clock, config, ids
from market.infra.errors import OutOfStockError, PolicyError, ValidationError
from market.infra.repositories import repo

_RESERVATIONS = "reservations"
_STOCK = "stock"


@dataclass
class Reservation:
    reservation_id: str
    order_id: str
    lines: tuple[tuple[str, int], ...]
    status: str
    expires_at: datetime


def _merge(lines: Sequence[tuple[str, int]]) -> tuple[tuple[str, int], ...]:
    merged: dict[str, int] = {}
    for sku, qty in lines:
        if qty <= 0:
            raise ValidationError(f"quantity of {sku} must be positive")
        merged[sku] = merged.get(sku, 0) + qty
    return tuple(merged.items())


def get_reservation(reservation_id: str) -> Reservation:
    return repo(_RESERVATIONS).get(reservation_id)


def reserve(order_id: str, lines: Sequence[tuple[str, int]]) -> Reservation:
    """Hold every line or none: the error names each short SKU (INV-03)."""
    wanted = _merge(lines)
    if not wanted:
        raise ValidationError("a reservation needs at least one line")
    tracked = [(sku, qty) for sku, qty in wanted if is_stock_tracked(get_product(sku).category)]
    short = tuple(sku for sku, qty in tracked if available(sku) < qty)
    if short:
        raise OutOfStockError("not enough stock for " + ", ".join(short), short)
    before = {sku: available(sku) for sku, _ in tracked}
    reservation = Reservation(
        ids.next_id("RSV"), order_id, wanted, "active",
        clock.now() + timedelta(minutes=config.get("inventory.reservation_minutes")),
    )
    repo(_RESERVATIONS).add(reservation.reservation_id, reservation)
    for sku, _ in tracked:
        check_low_stock(sku, before[sku], available(sku))
    return reservation


def _expire_if_due(reservation: Reservation) -> None:
    if reservation.status == "active" and reservation.expires_at <= clock.now():
        reservation.status = "expired"


def release(reservation_id: str) -> Reservation:
    reservation = get_reservation(reservation_id)
    _expire_if_due(reservation)
    if reservation.status == "active":
        reservation.status = "released"
    return reservation


def commit(reservation_id: str) -> Reservation:
    reservation = get_reservation(reservation_id)
    _expire_if_due(reservation)
    if reservation.status != "active":
        raise PolicyError(f"reservation_{reservation.status}")
    for sku, qty in reservation.lines:
        if is_stock_tracked(get_product(sku).category):
            repo(_STOCK).save(sku, max(0, on_hand(sku) - qty))
    reservation.status = "committed"
    return reservation


def expire_due() -> int:
    expired = 0
    for reservation in repo(_RESERVATIONS).all():
        if reservation.status == "active" and reservation.expires_at <= clock.now():
            reservation.status = "expired"
            expired += 1
    return expired
