"""CHK-01, CHK-02, CHK-03, CHK-04, CHK-05, CHK-06, CHK-07: checkout of a cart into a receipt."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from orders.features.pricing import compute_discount
from orders.features.shipping import shipping_fee
from orders.infra.cart_models import Cart, CartItem, Coupon, Customer

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
MAX_COUPON_PERCENT = Decimal("100")
MAX_SKU_LENGTH = 64
MAX_LINE_QTY = 10000
RECEIPT_LABEL_WIDTH = 10


class CheckoutError(ValueError):
    pass


class EmptyCartError(CheckoutError):
    pass


class InvalidItemError(CheckoutError):
    pass


class InvalidCouponError(CheckoutError):
    pass


class InvalidCustomerError(CheckoutError):
    pass


@dataclass(frozen=True)
class Receipt:
    subtotal: Decimal
    discount: Decimal
    shipping: Decimal
    total: Decimal

    def as_dict(self) -> dict[str, str]:
        return {
            "subtotal": format_money(self.subtotal),
            "discount": format_money(self.discount),
            "shipping": format_money(self.shipping),
            "total": format_money(self.total),
        }

    def render(self) -> str:
        return render_receipt_text(self)


def validate_customer(customer: Customer) -> None:
    if customer is None:
        raise InvalidCustomerError("a customer is required")
    if not isinstance(customer.id, str) or not customer.id.strip():
        raise InvalidCustomerError("the customer id must be a non-empty string")


def validate_sku(sku: str) -> None:
    if not isinstance(sku, str) or not sku.strip():
        raise InvalidItemError("the sku must be a non-empty string")
    if len(sku) > MAX_SKU_LENGTH:
        raise InvalidItemError(f"the sku {sku[:8]}... is longer than {MAX_SKU_LENGTH} characters")


def validate_unit_price(sku: str, unit_price: Decimal) -> None:
    if not isinstance(unit_price, Decimal):
        raise InvalidItemError(f"the unit price of {sku} must be a Decimal")
    if not unit_price.is_finite():
        raise InvalidItemError(f"the unit price of {sku} must be finite")
    if unit_price < ZERO:
        raise InvalidItemError(f"the unit price of {sku} cannot be negative")


def validate_quantity(sku: str, qty: int) -> None:
    if isinstance(qty, bool) or not isinstance(qty, int):
        raise InvalidItemError(f"the quantity of {sku} must be an integer")
    if qty < 1:
        raise InvalidItemError(f"the quantity of {sku} must be at least 1")
    if qty > MAX_LINE_QTY:
        raise InvalidItemError(f"the quantity of {sku} is above {MAX_LINE_QTY}")


def validate_item(item: CartItem) -> None:
    validate_sku(item.sku)
    validate_unit_price(item.sku, item.unit_price)
    validate_quantity(item.sku, item.qty)


def validate_cart(cart: Cart) -> None:
    if cart is None or not cart.items:
        raise EmptyCartError("the cart has no items")
    for item in cart.items:
        validate_item(item)


def validate_coupon(coupon: Coupon | None) -> None:
    if coupon is None:
        return
    if not isinstance(coupon.code, str) or not coupon.code.strip():
        raise InvalidCouponError("the coupon code must be a non-empty string")
    if not isinstance(coupon.percent, Decimal) or not coupon.percent.is_finite():
        raise InvalidCouponError("the coupon percent must be a finite Decimal")
    if coupon.percent <= Decimal("0"):
        raise InvalidCouponError("the coupon percent must be above zero")
    if coupon.percent > MAX_COUPON_PERCENT:
        raise InvalidCouponError("the coupon percent cannot exceed 100")


def validate_request(cart: Cart, customer: Customer, coupon: Coupon | None) -> None:
    validate_customer(customer)
    validate_cart(cart)
    validate_coupon(coupon)


def round_cents(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def line_total(item: CartItem) -> Decimal:
    return item.unit_price * item.qty


def merge_lines(items: list[CartItem]) -> dict[str, Decimal]:
    merged: dict[str, Decimal] = {}
    for item in items:
        merged[item.sku] = merged.get(item.sku, Decimal("0")) + line_total(item)
    return merged


def compute_subtotal(cart: Cart) -> Decimal:
    lines = merge_lines(cart.items)
    return round_cents(sum(lines.values(), Decimal("0")))


def compute_rounded_discount(subtotal: Decimal, customer: Customer, coupon: Coupon | None) -> Decimal:
    raw = compute_discount(subtotal, customer, coupon)
    return round_cents(raw)


def compute_amount_after_discount(subtotal: Decimal, discount: Decimal) -> Decimal:
    return round_cents(subtotal - discount)


def compute_total(subtotal: Decimal, discount: Decimal, shipping: Decimal) -> Decimal:
    return round_cents(subtotal - discount + shipping)


@dataclass(frozen=True)
class Totals:
    subtotal: Decimal
    discount: Decimal
    shipping: Decimal
    total: Decimal


def compute_totals(cart: Cart, customer: Customer, coupon: Coupon | None) -> Totals:
    subtotal = compute_subtotal(cart)
    discount = compute_rounded_discount(subtotal, customer, coupon)
    after_discount = compute_amount_after_discount(subtotal, discount)
    shipping = round_cents(shipping_fee(after_discount))
    total = compute_total(subtotal, discount, shipping)
    return Totals(subtotal, discount, shipping, total)


def format_money(amount: Decimal) -> str:
    return f"{round_cents(amount):.2f}"


def render_line(label: str, amount: Decimal) -> str:
    return f"{label + ':':<{RECEIPT_LABEL_WIDTH}}{format_money(amount):>10}"


def render_receipt_text(receipt: Receipt) -> str:
    lines = [
        render_line("Subtotal", receipt.subtotal),
        render_line("Discount", -receipt.discount),
        render_line("Shipping", receipt.shipping),
        render_line("Total", receipt.total),
    ]
    return "\n".join(lines)


def build_receipt(totals: Totals) -> Receipt:
    return Receipt(
        subtotal=totals.subtotal,
        discount=totals.discount,
        shipping=totals.shipping,
        total=totals.total,
    )


def checkout(cart: Cart, customer: Customer, coupon: Coupon | None = None) -> Receipt:
    validate_request(cart, customer, coupon)
    totals = compute_totals(cart, customer, coupon)
    return build_receipt(totals)
