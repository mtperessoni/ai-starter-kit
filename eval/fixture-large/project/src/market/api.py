"""Public facade of the market service: the only module hidden tests import (LG05, SPEC section 5)."""
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal

from market.features import loyalty as _loyalty  # noqa: F401  (import registers the handlers)
from market.features import notifications as _notifications  # noqa: F401
from market.features.cart import cart_coupons, cart_service
from market.features.cart.cart_pricing import price_cart
from market.features.catalog import catalog_search, product_store
from market.features.checkout import order_lifecycle
from market.features.checkout.order_models import Order, OrderQuote
from market.features.checkout.order_placement import place_order as _place_order
from market.features.checkout.order_quote import build_quote
from market.features.checkout.ports import set_loyalty_port
from market.features.inventory import stock_store
from market.features.inventory.reservations import expire_due
from market.features.loyalty import points_ledger
from market.features.loyalty.points_redemption import LoyaltyRedemptionPort
from market.features.notifications.dispatcher import list_sent
from market.features.notifications.notification_models import Notification
from market.features.payments import gift_cards
from market.features.payments import payment_service
from market.features.payments.payment_models import Payment, PaymentRequest
from market.features.pricing.quote_models import PriceQuote
from market.features.promotions import coupon_store
from market.features.promotions.promotion_models import BogoRule, Bundle, CategorySale, Coupon
from market.features.returns import return_service
from market.features.returns.return_models import ReturnRequest
from market.infra import clock, config, customers, events, repositories
from market.infra.errors import (MarketError, NotFoundError, OutOfStockError, PolicyError,
                                 ValidationError)
from market.infra.events import Event
from market.infra.models import Address, Customer, Product
from market.infra.money import D

set_loyalty_port(LoyaltyRedemptionPort())

__all__ = [
    "Address", "PaymentRequest", "Product", "Customer", "Order", "OrderQuote", "PriceQuote",
    "ReturnRequest", "Notification", "Payment", "Event",
    "MarketError", "NotFoundError", "ValidationError", "OutOfStockError", "PolicyError",
]

_DEMO_NOW = datetime(2026, 3, 10, 12, 0)
_DEMO_PRODUCTS = (
    ("BK-100", "Python Basics", "books", "40.00", 400),
    ("BK-200", "Data Patterns", "books", "60.00", 600),
    ("EL-100", "USB Cable", "electronics", "15.00", 100),
    ("EL-200", "Headphones", "electronics", "120.00", 300),
    ("FS-100", "T-Shirt", "fashion", "25.00", 200),
    ("GR-100", "Coffee 500g", "grocery", "12.50", 500),
    ("HM-100", "Desk Lamp", "home", "80.00", 1500),
    ("TY-100", "Puzzle", "toys", "30.00", 700),
    ("GC-050", "Gift Card 50", "gift_card", "50.00", 0),
)
_DEMO_CUSTOMERS = (
    ("C-REG", "reg@example.com", "standard", "SP"),
    ("C-VIP", "vip@example.com", "vip", "SP"),
    ("C-RJ", "rj@example.com", "standard", "RJ"),
    ("C-AM", "am@example.com", "standard", "AM"),
)


def reset() -> None:
    """Clear repositories, ids, config overrides, the clock and the event history."""
    repositories.reset_all()


def seed_demo() -> None:
    """Load the demo data of SPEC section 1 on a clean state, clock at 2026-03-10 12:00."""
    reset()
    set_now(_DEMO_NOW)
    for sku, name, category, price, grams in _DEMO_PRODUCTS:
        add_product(sku, name, category, price, grams)
        if category != "gift_card":
            set_stock(sku, 5 if sku == "EL-200" else 100)
    for customer_id, email, tier, region in _DEMO_CUSTOMERS:
        add_customer(customer_id, email, tier, region)
    add_coupon("SAVE10", "percent", 10, min_subtotal="50.00")
    add_coupon("SAVE20", "percent", 20, min_subtotal="100.00", per_customer_limit=1,
               expires_on=date(2026, 12, 31))
    add_coupon("FIX15", "fixed", 15, min_subtotal="80.00")
    add_coupon("FREESHIP", "free_shipping", 0, min_subtotal="30.00")
    add_category_sale("SALE-TOYS", "toys", 20, date(2026, 3, 1), date(2026, 3, 31))
    add_bogo("BOGO-TSHIRT", "FS-100", 2, 1)
    add_bundle("BUNDLE-READER", ("BK-100", "BK-200"), "15.00")
    issue_gift_card("GIFT-100", "100.00")


def set_now(value: datetime) -> None:
    clock.set_now(value)


def advance_time(days: int = 0, hours: int = 0, minutes: int = 0) -> datetime:
    return clock.advance(days=days, hours=hours, minutes=minutes)


def set_config(key: str, value) -> None:
    config.set(key, value)


def get_config(key: str):
    return config.get(key)


def add_product(sku: str, name: str, category: str, price, weight_grams: int) -> Product:
    return product_store.add_product(Product(sku, name, category, D(price), weight_grams))


def get_product(sku: str) -> Product:
    return product_store.get_product(sku)


def deactivate_product(sku: str) -> Product:
    return product_store.deactivate_product(sku)


def update_price(sku: str, new_price) -> Product:
    return product_store.update_price(sku, D(new_price))


def search_products(query: str = "", category: str | None = None, max_price=None,
                    sort: str = "name") -> list[Product]:
    limit = None if max_price is None else D(max_price)
    return catalog_search.search_products(query, category, limit, sort)


def add_customer(customer_id: str, email: str, tier: str = "standard", region: str = "SP",
                 tax_exempt: bool = False) -> Customer:
    return customers.add_customer(Customer(customer_id, email, tier, region, tax_exempt))


def set_stock(sku: str, on_hand: int) -> None:
    stock_store.set_on_hand(sku, on_hand)


def restock(sku: str, qty: int) -> int:
    return stock_store.add_stock(sku, qty)


def available_stock(sku: str) -> int:
    return stock_store.available(sku)


def expire_reservations() -> int:
    return expire_due()


def add_coupon(code: str, kind: str, value=0, min_subtotal=0, starts_on: date | None = None,
               expires_on: date | None = None, per_customer_limit: int | None = None,
               global_limit: int | None = None, categories: Sequence[str] = ()) -> None:
    coupon_store.add_coupon(Coupon(
        code, kind, D(value), D(min_subtotal), starts_on, expires_on, per_customer_limit,
        global_limit, tuple(categories),
    ))


def add_category_sale(sale_id: str, category: str, percent, starts_on: date, ends_on: date) -> None:
    coupon_store.add_category_sale(CategorySale(sale_id, category, D(percent), starts_on, ends_on))


def add_bogo(rule_id: str, sku: str, buy: int = 2, free: int = 1) -> None:
    coupon_store.add_bogo(BogoRule(rule_id, sku, buy, free))


def add_bundle(bundle_id: str, skus: Sequence[str], amount_off) -> None:
    coupon_store.add_bundle(Bundle(bundle_id, tuple(skus), D(amount_off)))


def create_cart(customer_id: str) -> str:
    return cart_service.create_cart(customer_id).cart_id


def add_to_cart(cart_id: str, sku: str, qty: int = 1) -> None:
    cart_service.add_item(cart_id, sku, qty)


def set_cart_quantity(cart_id: str, sku: str, qty: int) -> None:
    cart_service.set_quantity(cart_id, sku, qty)


def remove_from_cart(cart_id: str, sku: str) -> None:
    cart_service.remove_item(cart_id, sku)


def apply_coupon(cart_id: str, code: str) -> None:
    cart_coupons.apply_coupon(cart_id, code)


def remove_coupon(cart_id: str, code: str) -> None:
    cart_coupons.remove_coupon(cart_id, code)


def quote_cart(cart_id: str) -> PriceQuote:
    return price_cart(cart_id)


def quote_order(cart_id: str, address: Address | None = None, shipping_method: str = "standard",
                points_to_redeem: int = 0) -> OrderQuote:
    cart = cart_service.get_cart(cart_id)
    return build_quote(cart, customers.get_customer(cart.customer_id), address, shipping_method,
                       points_to_redeem)


def place_order(cart_id: str, payment: PaymentRequest, address: Address | None = None,
                shipping_method: str = "standard", points_to_redeem: int = 0) -> Order:
    return _place_order(cart_id, payment, address, shipping_method, points_to_redeem)


def get_order(order_id: str) -> Order:
    return order_lifecycle.get_order(order_id)


def cancel_order(order_id: str) -> Order:
    return order_lifecycle.cancel_order(order_id)


def mark_shipped(order_id: str) -> Order:
    return order_lifecycle.mark_shipped(order_id)


def mark_delivered(order_id: str) -> Order:
    return order_lifecycle.mark_delivered(order_id)


def issue_gift_card(code: str, balance) -> None:
    gift_cards.issue_gift_card(code, D(balance))


def gift_card_balance(code: str) -> Decimal:
    return gift_cards.gift_card_balance(code)


def get_payment(payment_id: str) -> Payment:
    return payment_service.get_payment(payment_id)


def points_balance(customer_id: str) -> int:
    return points_ledger.balance(customer_id)


def grant_points(customer_id: str, points: int) -> None:
    customers.get_customer(customer_id)
    points_ledger.add_points(customer_id, points, "grant")


def request_return(order_id: str, items: list[tuple[str, int]], reason: str) -> ReturnRequest:
    return return_service.request_return(order_id, items, reason)


def get_return(return_id: str) -> ReturnRequest:
    return return_service.get_return(return_id)


def sent_notifications(recipient: str | None = None, template: str | None = None) -> list[Notification]:
    return list_sent(recipient, template)


def event_history(name: str | None = None) -> list[Event]:
    return events.history(name)
