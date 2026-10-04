"""CAT-03, PRC-05, INV-07, RET-02: category facts shared across features."""

CATEGORIES: tuple[str, ...] = ("books", "electronics", "fashion", "grocery", "home", "toys", "gift_card")
EXEMPT_CATEGORIES = ("books", "grocery", "gift_card")


def is_digital(category: str) -> bool:
    return category == "gift_card"


def is_returnable(category: str) -> bool:
    return category not in ("gift_card", "grocery")


def is_stock_tracked(category: str) -> bool:
    return category != "gift_card"
