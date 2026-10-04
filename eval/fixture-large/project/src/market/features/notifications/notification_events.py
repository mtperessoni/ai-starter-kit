"""NTF-01, NTF-02, NTF-03, NTF-04: event handlers that send the emails."""
from market.features.notifications.dispatcher import send
from market.infra import events
from market.infra.customers import get_customer
from market.infra.events import Event

OPS_EMAIL = "ops@market.test"


def _email(customer_id: str) -> str:
    return get_customer(customer_id).email


def on_order_paid(event: Event) -> None:
    """A paid order sends order_confirmation to the customer (NTF-01)."""
    payload = event.payload
    send("order_confirmation", _email(payload["customer_id"]), payload["order_id"])


def on_payment_failed(event: Event) -> None:
    """A failed payment sends payment_failed to the customer (NTF-02)."""
    payload = event.payload
    send("payment_failed", _email(payload["customer_id"]), payload["order_id"])


def on_order_cancelled(event: Event) -> None:
    """A cancelled order sends order_cancelled (NTF-03)."""
    payload = event.payload
    send("order_cancelled", _email(payload["customer_id"]), payload["order_id"])


def on_return_completed(event: Event) -> None:
    """A completed return sends return_completed (NTF-03)."""
    payload = event.payload
    send("return_completed", _email(payload["customer_id"]), payload["order_id"],
         return_id=payload["return_id"])


def on_low_stock(event: Event) -> None:
    """A low-stock event sends low_stock to ops (NTF-04)."""
    payload = event.payload
    send("low_stock", OPS_EMAIL, None, sku=payload["sku"], available=payload["available"])


def register() -> None:
    """Subscribe every handler; subscribing twice is ignored by the bus."""
    events.subscribe("order.paid", on_order_paid)
    events.subscribe("payment.failed", on_payment_failed)
    events.subscribe("order.cancelled", on_order_cancelled)
    events.subscribe("return.completed", on_return_completed)
    events.subscribe("inventory.low_stock", on_low_stock)


def handled_events() -> tuple[str, ...]:
    """Names of the events this feature listens to (SPEC 2.9)."""
    return ("order.paid", "payment.failed", "order.cancelled", "return.completed", "inventory.low_stock")
