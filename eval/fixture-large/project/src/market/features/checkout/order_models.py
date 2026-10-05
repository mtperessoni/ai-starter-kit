"""CHK-03, CHK-08, PRC-01: order dataclasses, status values and the points base."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from market.features.catalog.category_rules import is_digital
from market.features.pricing.quote_models import PriceQuote
from market.features.shipping.shipping_fee import ShippingQuote
from market.features.tax.tax_calculator import TaxResult
from market.infra.models import Address

PENDING = "pending"
PAID = "paid"
PAYMENT_FAILED = "payment_failed"
CANCELLED = "cancelled"
SHIPPED = "shipped"
DELIVERED = "delivered"
PARTIALLY_REFUNDED = "partially_refunded"
REFUNDED = "refunded"

STATUSES = (PENDING, PAID, PAYMENT_FAILED, CANCELLED, SHIPPED, DELIVERED, PARTIALLY_REFUNDED, REFUNDED)


@dataclass(frozen=True)
class OrderLine:
    sku: str
    category: str
    qty: int
    unit_price: Decimal
    line_subtotal: Decimal
    line_discount: Decimal
    line_total: Decimal
    tax: Decimal
    weight_grams: int


@dataclass
class OrderQuote:
    price: PriceQuote
    shipping: ShippingQuote
    tax: TaxResult
    loyalty_discount: Decimal
    points_to_redeem: int
    total: Decimal


@dataclass
class Order:
    order_id: str
    customer_id: str
    lines: tuple[OrderLine, ...]
    subtotal: Decimal
    discount_total: Decimal
    shipping: Decimal
    tax: Decimal
    loyalty_discount: Decimal
    total: Decimal
    status: str
    address: Address | None
    shipping_method: str
    coupon_codes: tuple[str, ...]
    points_redeemed: int
    payment_id: str | None
    reservation_id: str | None
    decline_code: str | None
    created_at: datetime
    paid_at: datetime | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    returned_units: dict[str, int] = field(default_factory=dict)

    def units_bought(self, sku: str) -> int:
        """Units of a SKU in the order, summed over its lines."""
        return sum(line.qty for line in self.lines if line.sku == sku)

    def units_left_to_return(self, sku: str) -> int:
        return self.units_bought(sku) - self.returned_units.get(sku, 0)


def merchandise_points_base(lines: tuple[OrderLine, ...]) -> Decimal:
    """Sum of line totals after discounts for lines that are not gift cards (LOY-01, LOY-03).

    This is the `points_base` carried by order.paid and order.cancelled.
    """
    return sum((line.line_total for line in lines if not is_digital(line.category)), Decimal("0.00"))


def check_totals(order: Order) -> list[str]:
    """Consistency problems of an order record, empty when the numbers add up (CHK-03, PRC-01).

    Checks that the merchandise after discounts matches the lines, that the line discounts add up
    to the discount total, and that total = merchandise + shipping + tax - loyalty discount (never
    below 0.00). Useful after loading or migrating orders.
    """
    problems: list[str] = []
    merchandise = sum((line.line_total for line in order.lines), Decimal("0.00"))
    discounts = sum((line.line_discount for line in order.lines), Decimal("0.00"))
    if order.subtotal - order.discount_total != merchandise:
        problems.append("merchandise does not match the lines")
    if discounts != order.discount_total:
        problems.append("line discounts do not add up to the discount total")
    expected = max(Decimal("0.00"), merchandise + order.shipping + order.tax - order.loyalty_discount)
    if expected != order.total:
        problems.append(f"total should be {expected}")
    return problems


def order_summary(order: Order) -> list[str]:
    """Short lines for a receipt: id, status, one row per line, then the money rows.

        ORD-0001 paid
        2 x EL-200 240.00
        shipping 0.00 / tax 19.20 / total 259.20
    """
    rows = [f"{order.order_id} {order.status}"]
    rows.extend(f"{line.qty} x {line.sku} {line.line_total}" for line in order.lines)
    rows.append(f"shipping {order.shipping} / tax {order.tax} / total {order.total}")
    return rows
