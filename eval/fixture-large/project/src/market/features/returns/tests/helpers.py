"""Shared world for the returns tests (RET-01 to RET-07): customers, products and delivered orders."""
from datetime import datetime
from decimal import Decimal

from market.features.cart.cart_service import add_item, create_cart
from market.features.catalog.product_store import add_product
from market.features.checkout.order_lifecycle import mark_delivered, mark_shipped
from market.features.checkout.order_models import Order, OrderLine
from market.features.checkout.order_placement import place_order
from market.features.inventory.stock_store import set_on_hand
from market.features.payments.payment_models import PaymentRequest
from market.infra import clock
from market.infra.customers import add_customer
from market.infra.models import Address, Customer, Product

ADDR = Address("BR", "SP", "01000-000")
OK = PaymentRequest("card", "ok_1")
ZERO = Decimal("0.00")


def setup_world() -> None:
    add_customer(Customer("C-REG", "reg@example.com"))
    add_customer(Customer("C-VIP", "vip@example.com", "vip"))
    for sku, name, category, price, grams, stock in (
        ("EL-200", "Headphones", "electronics", "120.00", 300, 5),
        ("HM-100", "Desk Lamp", "home", "80.00", 1500, 50),
        ("BK-100", "Python Basics", "books", "40.00", 400, 50),
        ("GR-100", "Coffee 500g", "grocery", "12.50", 500, 50),
        ("GC-050", "Gift Card 50", "gift_card", "50.00", 0, 0),
    ):
        add_product(Product(sku, name, category, Decimal(price), grams))
        if category != "gift_card":
            set_on_hand(sku, stock)


def delivered_order(items: list[tuple[str, int]], customer: str = "C-REG") -> Order:
    cart = create_cart(customer)
    for sku, qty in items:
        add_item(cart.cart_id, sku, qty)
    order = place_order(cart.cart_id, OK, ADDR)
    mark_shipped(order.order_id)
    return mark_delivered(order.order_id)


def order_line(sku: str, category: str, qty: int, total: str, tax: str = "0.00") -> OrderLine:
    amount = Decimal(total)
    return OrderLine(sku, category, qty, amount / qty, amount, ZERO, amount, Decimal(tax), 100)


def make_order(lines: list[OrderLine], shipping: str = "0.00", status: str = "delivered",
               returned: dict[str, int] | None = None) -> Order:
    """An order built by hand, delivered at the demo clock, for policy and calculator tests."""
    when = datetime(2026, 3, 10, 12, 0) if status != "paid" else None
    return Order(
        "ORD-0001", "C-REG", tuple(lines), ZERO, ZERO, Decimal(shipping), ZERO, ZERO, ZERO, status,
        ADDR, "standard", (), 0, None, None, None, clock.now(), delivered_at=when,
        returned_units=dict(returned or {}),
    )
