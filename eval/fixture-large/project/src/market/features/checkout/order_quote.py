"""CHK-03, CHK-04, SHP-03, TAX-01, LOY-04: the order quote, price then loyalty then shipping then tax."""
from decimal import Decimal

from market.features.cart.cart_pricing import price_cart
from market.features.checkout.order_models import OrderQuote
from market.features.checkout.ports import get_loyalty_port
from market.features.shipping.shipping_fee import ShippingRequest, quote_shipping
from market.features.tax.tax_calculator import compute_tax
from market.infra.errors import ValidationError
from market.infra.models import Address, Cart, Customer

ZERO = Decimal("0.00")


def delivery_region(address: Address | None, customer: Customer) -> str:
    """Tax and shipping follow the delivery address; without one, the customer's region (TAX-01)."""
    return address.region if address is not None else customer.region


def build_quote(cart: Cart, customer: Customer, address: Address | None, shipping_method: str,
                points_to_redeem: int) -> OrderQuote:
    """Quote an order from a cart without changing anything.

    Steps, in the order of CHK-04:
      1. price the cart (pricing and promotions);
      2. ask the loyalty port for the value of the points to redeem (LOY-04);
      3. shipping, judged on merchandise after discounts (SHP-03);
      4. tax on the lines after discounts and on shipping, not reduced by points (CHK-04);
      5. total = merchandise + shipping + tax - loyalty discount, never below 0.00 (CHK-03).

    Example, C-REG in SP with 200.00 of merchandise: shipping is free, tax is 16.00, redeeming
    500 points takes 5.00 off the amount to pay and gives a total of 211.00.
    """
    if points_to_redeem < 0:
        raise ValidationError("points to redeem cannot be negative")
    price = price_cart(cart.cart_id)
    merchandise = price.total
    loyalty_discount = get_loyalty_port().redemption_value(customer.customer_id, points_to_redeem, merchandise)
    region = delivery_region(address, customer)
    shipping = quote_shipping(ShippingRequest(
        region=region, lines=price.lines, merchandise_total=merchandise,
        customer_tier=customer.tier, method=shipping_method, free_shipping_coupon=price.free_shipping,
    ))
    tax = compute_tax(price.lines, shipping.fee, region, customer.tax_exempt)
    total = max(ZERO, merchandise + shipping.fee + tax.total - loyalty_discount)
    return OrderQuote(price, shipping, tax, loyalty_discount, points_to_redeem, total)


def explain_quote(quote: OrderQuote) -> list[str]:
    """One line per money component of an order quote, in the order of CHK-03.

        merchandise 200.00 / shipping 0.00 (threshold) / tax 16.00 / loyalty -5.00 / total 211.00
    """
    reason = f" ({quote.shipping.free_reason})" if quote.shipping.free_reason else ""
    rows = [
        f"merchandise {quote.price.total}",
        f"shipping {quote.shipping.fee}{reason}",
        f"tax {quote.tax.total}",
    ]
    if quote.loyalty_discount > 0:
        rows.append(f"loyalty -{quote.loyalty_discount}")
    rows.append(f"total {quote.total}")
    return rows
