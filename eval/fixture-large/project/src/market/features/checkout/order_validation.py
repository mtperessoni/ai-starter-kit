"""CHK-05, CHK-07, CHK-10: checks that run after the quote and before anything is held."""
from market.features.catalog.category_rules import is_digital
from market.features.pricing.quote_models import PriceQuote
from market.infra import config
from market.infra.errors import ValidationError
from market.infra.models import Address, Cart


def _needs_address(price: PriceQuote) -> bool:
    return any(not is_digital(line.category) for line in price.lines)


def validate_checkout(cart: Cart, address: Address | None, price: PriceQuote) -> None:
    """Refuse an order that cannot be placed, with the reason in the error message.

    Checks, in this order:
      CHK-05  a physical item needs an address; a gift-card-only order does not;
      CHK-10  every coupon on the cart must still be valid: the first rejected one is named
              with its reason (for example `SAVE20: customer_limit_reached`);
      CHK-07  merchandise after discounts must reach the configured minimum (10.00).
    """
    if not cart.lines:
        raise ValidationError("the cart is empty")
    if _needs_address(price) and (address is None or not address.region.strip()):
        raise ValidationError("an address is required for physical items")
    for code, reason in price.rejected_coupons:
        raise ValidationError(f"coupon {code} is not valid: {reason}")
    minimum = config.get("checkout.min_order_total")
    if price.total < minimum:
        raise ValidationError(f"merchandise after discounts must be at least {minimum}")


def describe_blockers(cart: Cart, address: Address | None, price: PriceQuote) -> list[str]:
    """Every reason the order cannot be placed, instead of only the first one.

    Useful for a checkout screen that shows all problems at once. The messages are the same as
    the ValidationError of `validate_checkout`; an empty list means the order can go ahead.
    """
    blockers: list[str] = []
    if not cart.lines:
        blockers.append("the cart is empty")
    if _needs_address(price) and (address is None or not address.region.strip()):
        blockers.append("an address is required for physical items")
    blockers.extend(f"coupon {code} is not valid: {reason}" for code, reason in price.rejected_coupons)
    minimum = config.get("checkout.min_order_total")
    if cart.lines and price.total < minimum:
        blockers.append(f"merchandise after discounts must be at least {minimum}")
    return blockers
