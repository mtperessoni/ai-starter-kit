"""LOY-01, LOY-02: points earned for a paid order."""
from decimal import ROUND_FLOOR, Decimal

from market.infra import config


def tier_multiplier(tier: str) -> int:
    """VIP customers earn double (the multiplier comes from config); everyone else earns 1x."""
    if tier == "vip":
        return config.get("loyalty.vip_multiplier")
    return 1


def points_for_order(points_base: Decimal, tier: str) -> int:
    """1 point per whole 1.00 of merchandise after discounts, times the tier multiplier (LOY-01).

    The base is merchandise only: shipping, tax and gift cards are already left out by the caller.

        120.00 standard -> 120      120.00 vip -> 240      108.99 standard -> 108
    """
    if points_base <= 0:
        return 0
    whole = int(points_base.to_integral_value(rounding=ROUND_FLOOR))
    return whole * tier_multiplier(tier)


def explain_earning(points_base: Decimal, tier: str) -> str:
    """Readable earning line for receipts.

        explain_earning(Decimal("120.00"), "vip") -> "120 x2 = 240 points"
    """
    base = points_for_order(points_base, "standard")
    return f"{base} x{tier_multiplier(tier)} = {points_for_order(points_base, tier)} points"
