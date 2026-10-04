"""CRT-06, PRM-01, PRM-06: coupons on a cart, valid only when they would apply now."""
from market.features.cart.cart_service import editable_cart
from market.features.pricing.price_calculator import quote_lines
from market.features.promotions.coupon_store import normalize_code
from market.infra import clock
from market.infra.customers import get_customer
from market.infra.errors import ValidationError
from market.infra.models import Cart


def apply_coupon(cart_id: str, code: str) -> Cart:
    cart = editable_cart(cart_id)
    normalized = normalize_code(code)
    if normalized in cart.coupon_codes:
        return cart
    quote = quote_lines(cart.lines, get_customer(cart.customer_id), [*cart.coupon_codes, normalized])
    for rejected_code, reason in quote.rejected_coupons:
        if rejected_code == normalized and reason != "kind_already_applied":
            raise ValidationError(reason)
    cart.coupon_codes.append(normalized)
    cart.updated_at = clock.now()
    return cart


def remove_coupon(cart_id: str, code: str) -> Cart:
    cart = editable_cart(cart_id)
    normalized = normalize_code(code)
    if normalized in cart.coupon_codes:
        cart.coupon_codes.remove(normalized)
        cart.updated_at = clock.now()
    return cart
