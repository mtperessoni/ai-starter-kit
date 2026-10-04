"""PRC-01, PRC-02, PRC-03, PRC-04, PRC-06, PRM-05: the price quote of a set of cart lines."""
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from market.features.catalog.product_store import get_product
from market.features.pricing.discount_allocation import line_discount_map
from market.features.pricing.quote_models import LineQuote, PriceQuote
from market.features.pricing.volume_breaks import volume_discount
from market.features.promotions.promotion_engine import evaluate
from market.features.promotions.promotion_models import AppliedDiscount, PromoLine
from market.infra import clock
from market.infra.models import CartLine, Customer

ZERO = Decimal("0.00")
VOLUME_CODE = "VOLUME"


def line_subtotal(unit_price: Decimal, qty: int) -> Decimal:
    return unit_price * qty


def quote_lines(lines: Sequence[CartLine], customer: Customer, coupon_codes: Sequence[str],
                today: date | None = None) -> PriceQuote:
    """Quote the lines at current catalog prices; nothing is stored (PRC-01)."""
    day = today if today is not None else clock.today()
    products = [get_product(line.sku) for line in lines]
    subtotals = [line_subtotal(p.price, line.qty) for p, line in zip(products, lines)]
    volume = [volume_discount(p.price, line.qty, p.category) for p, line in zip(products, lines)]

    volume_discounts = tuple(
        AppliedDiscount(VOLUME_CODE, "volume", amount, ((line.sku, amount),))
        for line, amount in zip(lines, volume) if amount > 0
    )
    promo_lines = [
        PromoLine(line.sku, p.category, line.qty, p.price, subtotal - vol)
        for p, line, subtotal, vol in zip(products, lines, subtotals, volume)
    ]
    promo = evaluate(promo_lines, customer, coupon_codes, day)

    discounts = volume_discounts + promo.discounts
    per_line = line_discount_map(discounts)
    quoted = tuple(
        LineQuote(
            sku=line.sku, category=p.category, qty=line.qty, unit_price=p.price,
            line_subtotal=subtotal, line_discount=per_line.get(line.sku, ZERO),
            line_total=subtotal - per_line.get(line.sku, ZERO),
            taxable_class=p.taxable_class, weight_grams=p.weight_grams,
        )
        for p, line, subtotal in zip(products, lines, subtotals)
    )
    subtotal = sum((q.line_subtotal for q in quoted), ZERO)
    discount_total = sum((d.amount for d in discounts), ZERO)
    return PriceQuote(
        lines=quoted,
        subtotal=subtotal,
        discounts=discounts,
        discount_total=discount_total,
        total=max(ZERO, subtotal - discount_total),
        free_shipping=promo.free_shipping,
        rejected_coupons=promo.rejected,
    )
