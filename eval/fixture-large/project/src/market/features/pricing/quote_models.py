"""PRC-01, PRC-02, PRC-06: quote dataclasses."""
from dataclasses import dataclass
from decimal import Decimal

from market.features.promotions.promotion_models import AppliedDiscount


@dataclass(frozen=True)
class LineQuote:
    sku: str
    category: str
    qty: int
    unit_price: Decimal
    line_subtotal: Decimal
    line_discount: Decimal
    line_total: Decimal
    taxable_class: str
    weight_grams: int


@dataclass(frozen=True)
class PriceQuote:
    lines: tuple[LineQuote, ...]
    subtotal: Decimal
    discounts: tuple[AppliedDiscount, ...]
    discount_total: Decimal
    total: Decimal
    free_shipping: bool
    rejected_coupons: tuple[tuple[str, str], ...]
