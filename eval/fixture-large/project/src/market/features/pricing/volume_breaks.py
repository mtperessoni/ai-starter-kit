"""PRC-03, PRC-05: volume break per line, never on gift cards."""
from decimal import Decimal

from market.features.catalog.category_rules import is_digital
from market.infra import config
from market.infra.money import pct, q2


def volume_percent(qty: int, category: str | None = None) -> Decimal:
    if category is not None and is_digital(category):
        return Decimal("0")
    if qty >= config.get("pricing.volume_tier2_qty"):
        return config.get("pricing.volume_tier2_percent")
    if qty >= config.get("pricing.volume_tier1_qty"):
        return config.get("pricing.volume_tier1_percent")
    return Decimal("0")


def volume_discount(unit_price: Decimal, qty: int, category: str | None = None) -> Decimal:
    return q2(pct(unit_price * qty, volume_percent(qty, category)))
