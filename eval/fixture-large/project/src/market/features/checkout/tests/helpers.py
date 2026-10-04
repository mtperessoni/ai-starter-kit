"""Shared world for the checkout tests (CHK-01 to CHK-10): customers, products, coupons, carts."""
from decimal import Decimal

from market.features.cart.cart_coupons import apply_coupon
from market.features.cart.cart_service import add_item, create_cart
from market.features.catalog.product_store import add_product
from market.features.inventory.stock_store import set_on_hand
from market.features.payments.payment_models import PaymentRequest
from market.features.promotions.coupon_store import add_coupon
from market.features.promotions.promotion_models import Coupon
from market.infra.customers import add_customer
from market.infra.models import Address, Customer, Product

ADDR = Address("BR", "SP", "01000-000")
OK = PaymentRequest("card", "ok_1")
DECLINE = PaymentRequest("card", "decline_1")


def setup_world() -> None:
    add_customer(Customer("C-REG", "reg@example.com"))
    add_customer(Customer("C-VIP", "vip@example.com", "vip"))
    add_customer(Customer("C-RJ", "rj@example.com", "standard", "RJ"))
    for sku, name, category, price, grams, stock in (
        ("EL-200", "Headphones", "electronics", "120.00", 300, 5),
        ("HM-100", "Desk Lamp", "home", "80.00", 1500, 50),
        ("BK-100", "Python Basics", "books", "40.00", 400, 50),
        ("PN-001", "Pen", "home", "8.00", 50, 50),
        ("GC-050", "Gift Card 50", "gift_card", "50.00", 0, 0),
    ):
        add_product(Product(sku, name, category, Decimal(price), grams))
        if category != "gift_card":
            set_on_hand(sku, stock)
    add_coupon(Coupon("SAVE10", "percent", Decimal("10"), Decimal("50.00")))
    add_coupon(Coupon("SAVE20", "percent", Decimal("20"), Decimal("100.00"), per_customer_limit=1))
    add_coupon(Coupon("FREESHIP", "free_shipping", Decimal("0"), Decimal("30.00")))


def cart_with(customer: str, items: list[tuple[str, int]], coupons: tuple[str, ...] = ()) -> str:
    cart = create_cart(customer)
    for sku, qty in items:
        add_item(cart.cart_id, sku, qty)
    for code in coupons:
        apply_coupon(cart.cart_id, code)
    return cart.cart_id
