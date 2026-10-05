"""PRC-01, PRC-06: quote of a cart at current prices."""
from market.features.cart.cart_service import get_cart
from market.features.pricing.price_calculator import quote_lines
from market.features.pricing.quote_models import PriceQuote
from market.infra.customers import get_customer


def price_cart(cart_id: str) -> PriceQuote:
    cart = get_cart(cart_id)
    return quote_lines(cart.lines, get_customer(cart.customer_id), cart.coupon_codes)
