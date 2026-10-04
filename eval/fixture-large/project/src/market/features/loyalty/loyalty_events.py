"""LOY-01, LOY-03, LOY-06: loyalty handlers for order.paid, order.cancelled and return.completed."""
from decimal import Decimal

from market.features.loyalty.points_earning import points_for_order
from market.features.loyalty.points_ledger import add_points, claw_back, spend
from market.infra import events
from market.infra.customers import get_customer
from market.infra.events import Event

ZERO = Decimal("0.00")


def _tier(customer_id: str) -> str:
    return get_customer(customer_id).tier


def on_order_paid(event: Event) -> None:
    """Spend the points redeemed on the order, then add the points it earned (LOY-01).

    points_base already leaves out gift-card lines, so a gift-card-only order earns 0 (LOY-03).
    """
    payload = event.payload
    customer_id = payload["customer_id"]
    redeemed = payload.get("points_redeemed", 0)
    if redeemed > 0:
        spend(customer_id, redeemed)
    earned = points_for_order(payload.get("points_base", ZERO), _tier(customer_id))
    if earned > 0:
        add_points(customer_id, earned, f"order:{payload['order_id']}")


def on_order_cancelled(event: Event) -> None:
    """Take back the points the order earned and give back the points it redeemed (LOY-06).

    The claw-back never goes below a zero balance; the redeemed points return as a fresh lot.
    """
    payload = event.payload
    customer_id = payload["customer_id"]
    earned = points_for_order(payload.get("points_base", ZERO), _tier(customer_id))
    if earned > 0:
        claw_back(customer_id, earned)
    redeemed = payload.get("points_redeemed", 0)
    if redeemed > 0:
        add_points(customer_id, redeemed, f"redeem_refund:{payload['order_id']}")


def on_return_completed(event: Event) -> None:
    """Take back the points earned on the returned merchandise (LOY-06, RET-07)."""
    payload = event.payload
    customer_id = payload["customer_id"]
    earned = points_for_order(payload.get("points_base_returned", ZERO), _tier(customer_id))
    if earned > 0:
        claw_back(customer_id, earned)


def register() -> None:
    """Subscribe the handlers; subscribing twice is ignored by the bus."""
    events.subscribe("order.paid", on_order_paid)
    events.subscribe("order.cancelled", on_order_cancelled)
    events.subscribe("return.completed", on_return_completed)


def handled_events() -> tuple[str, ...]:
    """Names of the events this feature listens to (SPEC 2.9)."""
    return ("order.paid", "order.cancelled", "return.completed")
