"""CHK-01, CHK-02, CHK-06, PRM-04, INV-03: placing an order and rolling back a failed payment."""
from decimal import Decimal

from market.features.cart.cart_service import editable_cart, mark_converted
from market.features.catalog.product_store import require_sellable
from market.features.checkout.order_models import (PAID, PAYMENT_FAILED, PENDING, Order, OrderLine,
                                                    OrderQuote, merchandise_points_base)
from market.features.checkout.order_quote import build_quote
from market.features.checkout.order_validation import validate_checkout
from market.features.inventory.reservations import commit, release, reserve
from market.features.payments.payment_models import STATUS_CAPTURED, PaymentRequest
from market.features.payments.payment_service import charge
from market.features.promotions.promotion_usage import commit_uses, hold_uses
from market.infra import clock, events, ids
from market.infra.customers import get_customer
from market.infra.errors import MarketError, ValidationError
from market.infra.models import Address, Cart
from market.infra.repositories import repo

_ORDERS = "orders"
ZERO = Decimal("0.00")


def _check_cart(cart: Cart) -> None:
    """The cart must have lines and every product must still be sellable (CHK-01, CAT-05)."""
    if not cart.lines:
        raise ValidationError("the cart is empty")
    for line in cart.lines:
        require_sellable(line.sku)


def _order_lines(quote: OrderQuote) -> tuple[OrderLine, ...]:
    """Freeze the quoted prices into order lines so later price changes do not touch them (PRC-01)."""
    return tuple(
        OrderLine(
            sku=line.sku, category=line.category, qty=line.qty, unit_price=line.unit_price,
            line_subtotal=line.line_subtotal, line_discount=line.line_discount,
            line_total=line.line_total, tax=quote.tax.per_line.get(line.sku, ZERO),
            weight_grams=line.weight_grams,
        )
        for line in quote.price.lines
    )


def _create_order(order_id: str, cart: Cart, quote: OrderQuote, address: Address | None,
                  shipping_method: str, reservation_id: str) -> Order:
    order = Order(
        order_id=order_id, customer_id=cart.customer_id, lines=_order_lines(quote),
        subtotal=quote.price.subtotal, discount_total=quote.price.discount_total,
        shipping=quote.shipping.fee, tax=quote.tax.total, loyalty_discount=quote.loyalty_discount,
        total=quote.total, status=PENDING, address=address, shipping_method=shipping_method,
        coupon_codes=tuple(cart.coupon_codes), points_redeemed=quote.points_to_redeem,
        payment_id=None, reservation_id=reservation_id, decline_code=None, created_at=clock.now(),
    )
    repo(_ORDERS).add(order_id, order)
    return order


def _rollback(order: Order, reservation_id: str) -> None:
    """Give back what placement took: the stock hold, then the coupon uses (CHK-06)."""
    release(reservation_id)


def _mark_paid(order: Order, cart_id: str) -> None:
    commit(order.reservation_id)
    commit_uses(order.order_id)
    order.status = PAID
    order.paid_at = clock.now()
    mark_converted(cart_id)
    events.publish(
        "order.paid", order_id=order.order_id, customer_id=order.customer_id,
        points_base=merchandise_points_base(order.lines), points_redeemed=order.points_redeemed,
        total=order.total,
    )


def place_order(cart_id: str, payment: PaymentRequest, address: Address | None = None,
                shipping_method: str = "standard", points_to_redeem: int = 0) -> Order:
    """Place an order from an open cart; a declined payment returns the order, it does not raise.

    Sequence (CHK-02, SPEC 2.11): load cart and customer, quote, validate, reserve stock, hold
    coupon uses, create the pending order, charge, then commit or roll back.

    Errors before the order exists (empty or expired cart, address, minimum, coupon, stock) raise
    the MarketError of the rule and leave no hold behind. When the payment is declined the order is
    saved as payment_failed with the decline code, the hold and the uses are given back, and the
    cart stays open so the customer can try again; each try is a new order id (CHK-06).
    """
    cart = editable_cart(cart_id)
    _check_cart(cart)
    customer = get_customer(cart.customer_id)
    quote = build_quote(cart, customer, address, shipping_method, points_to_redeem)
    validate_checkout(cart, address, quote.price)

    order_id = ids.next_id("ORD")
    reservation = reserve(order_id, [(line.sku, line.qty) for line in cart.lines])
    hold_uses(order_id, customer.customer_id, cart.coupon_codes)
    order = _create_order(order_id, cart, quote, address, shipping_method, reservation.reservation_id)

    try:
        result = charge(order_id, customer.customer_id, quote.total, payment)
    except MarketError:
        _rollback(order, reservation.reservation_id)
        repo(_ORDERS).delete(order_id)
        raise
    order.payment_id = result.payment_id
    if result.status == STATUS_CAPTURED:
        _mark_paid(order, cart_id)
        return order
    _rollback(order, reservation.reservation_id)
    order.status = PAYMENT_FAILED
    order.decline_code = result.decline_code
    return order
