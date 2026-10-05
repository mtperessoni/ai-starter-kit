"""SHP-02, SHP-03, SHP-04: weight surcharge, free thresholds and the gift-card-only rule."""
from collections.abc import Sequence
from decimal import Decimal

from market.features.catalog.category_rules import is_digital
from market.features.pricing.quote_models import LineQuote
from market.infra import config

INCLUDED_GRAMS = 1000
STEP_GRAMS = 500


def is_digital_only(lines: Sequence[LineQuote]) -> bool:
    """True when the order has lines and every one is a gift card (SHP-04).

    An empty list is not digital: nothing was bought, so no waiver applies.

        gift card only        -> True
        gift card plus a book -> False
    """
    return bool(lines) and all(is_digital(line.category) for line in lines)


def total_weight(lines: Sequence[LineQuote]) -> int:
    """Grams of the physical lines: unit weight times quantity, gift cards skipped.

    Two units of a 400 g book and one gift card weigh 800 g.
    """
    grams = 0
    for line in lines:
        if is_digital(line.category):
            continue
        grams += line.weight_grams * line.qty
    return grams


def started_steps(grams: int) -> int:
    """How many started 500 g steps lie beyond the included 1000 g.

        1000 g -> 0     1001 g -> 1     1500 g -> 1     1501 g -> 2
    """
    if grams < 0:
        raise ValueError("weight cannot be negative")
    extra = grams - INCLUDED_GRAMS
    if extra <= 0:
        return 0
    return -(-extra // STEP_GRAMS)


def is_overweight(grams: int) -> bool:
    """True when the physical goods are over the configured limit and the order is refused (SHP-06)."""
    return grams > config.get("shipping.max_weight_grams")


def weight_surcharge(grams: int) -> Decimal:
    """Surcharge for weight: the first 1000 g are included, each further started 500 g adds 3.00.

        1000 g -> 0.00     1001 g -> 3.00     1500 g -> 3.00     1800 g -> 6.00
    """
    return config.get("shipping.surcharge_per_500g") * started_steps(grams)


def free_threshold(tier: str) -> Decimal:
    """Merchandise after discounts from which standard shipping is free (SHP-03).

    200.00 for standard customers, 100.00 for VIP; both come from config.
    """
    if tier == "vip":
        return config.get("shipping.free_threshold_vip")
    return config.get("shipping.free_threshold")
