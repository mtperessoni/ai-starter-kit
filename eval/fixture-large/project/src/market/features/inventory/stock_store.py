"""INV-01, INV-02, INV-07, INV-08: stock levels, availability and restock events."""
from market.features.catalog.category_rules import is_stock_tracked
from market.features.catalog.product_store import get_product
from market.infra import clock, events
from market.infra.errors import ValidationError
from market.infra.repositories import repo

UNTRACKED_AVAILABLE = 10**9
_STOCK = "stock"
_RESERVATIONS = "reservations"


def set_on_hand(sku: str, qty: int) -> None:
    get_product(sku)
    if qty < 0:
        raise ValidationError("stock on hand cannot be negative")
    repo(_STOCK).save(sku, qty)


def on_hand(sku: str) -> int:
    return repo(_STOCK).find(sku) or 0


def reserved(sku: str) -> int:
    """Units held by reservations that are active and not past their expiry (INV-02, INV-04)."""
    now = clock.now()
    held = 0
    for reservation in repo(_RESERVATIONS).all():
        if reservation.status != "active" or reservation.expires_at <= now:
            continue
        held += sum(qty for line_sku, qty in reservation.lines if line_sku == sku)
    return held


def available(sku: str) -> int:
    if not is_stock_tracked(get_product(sku).category):
        return UNTRACKED_AVAILABLE
    return max(0, on_hand(sku) - reserved(sku))


def add_stock(sku: str, qty: int) -> int:
    if qty <= 0:
        raise ValidationError("restock quantity must be positive")
    tracked = is_stock_tracked(get_product(sku).category)
    before = available(sku)
    repo(_STOCK).save(sku, on_hand(sku) + qty)
    after = available(sku)
    if tracked and before == 0 and after > 0:
        events.publish("inventory.restocked", sku=sku, available=after)
    return on_hand(sku)
