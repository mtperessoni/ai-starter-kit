"""Hidden tests for L6: split of the promotion engine, behavior unchanged.

Characterization tests (12 carts, no bundle together with a percent coupon) pin PRM-01 to
PRM-13 through quote_cart. Structure tests read the promotions folder.
The import of the engine module in the last test is done by name, not as a feature import.
"""
import importlib
from decimal import Decimal as D
from pathlib import Path

import pytest

from market import api

PROMO_DIR = Path(api.__file__).resolve().parent / "features" / "promotions"

# (id, items, coupons, discount_total, total, free_shipping, rejected)
CARTS = [
    ("sale", [("TY-100", 1)], [], "6.00", "24.00", False, ()),
    ("bogo", [("FS-100", 3)], [], "25.00", "50.00", False, ()),
    ("bogo_percent", [("FS-100", 3)], ["SAVE10"], "30.00", "45.00", False, ()),
    ("sale_percent", [("TY-100", 2)], ["SAVE10"], "16.80", "43.20", False, ()),
    ("percent", [("EL-200", 1), ("HM-100", 1)], ["SAVE20"], "40.00", "160.00", False, ()),
    ("two_percent", [("EL-200", 1), ("HM-100", 1)], ["SAVE10", "SAVE20"], "20.00", "180.00",
     False, (("SAVE20", "kind_already_applied"),)),
    ("fixed", [("EL-200", 1), ("HM-100", 1)], ["FIX15"], "15.00", "185.00", False, ()),
    ("percent_fixed", [("EL-200", 1), ("HM-100", 1)], ["SAVE10", "FIX15"], "35.00", "165.00",
     False, ()),
    ("percent_fixed_min", [("HM-100", 1)], ["SAVE10", "FIX15"], "23.00", "57.00", False, ()),
    ("gift_card_excluded", [("EL-200", 1), ("GC-050", 1)], ["SAVE10"], "12.00", "158.00",
     False, ()),
    ("cap", [("FS-100", 6)], ["SAVE20"], "60.00", "90.00", False, ()),
    ("free_shipping", [("EL-200", 1)], ["FREESHIP"], "0.00", "120.00", True, ()),
]


@pytest.mark.parametrize("case", CARTS, ids=[c[0] for c in CARTS])
def test_quote_is_unchanged(case):
    """PRM-01 to PRM-13: the quote of each characterization cart keeps its numbers."""
    _, items, coupons, discount, total, free_shipping, rejected = case
    api.reset()
    api.seed_demo()
    cart = api.create_cart("C-REG")
    for sku, qty in items:
        api.add_to_cart(cart, sku, qty)
    for code in coupons:
        api.apply_coupon(cart, code)
    q = api.quote_cart(cart)
    assert q.discount_total == D(discount)
    assert q.total == D(total)
    assert q.free_shipping is free_shipping
    assert q.rejected_coupons == rejected


def _lines(path):
    return len(path.read_text(encoding="utf-8").splitlines())


def test_engine_file_is_at_most_350_lines():
    """Refactor goal: promotion_engine.py is split down to 350 lines or fewer."""
    assert _lines(PROMO_DIR / "promotion_engine.py") <= 350


def test_every_promotions_module_is_at_most_300_lines():
    """Refactor goal: no Python file directly in the promotions folder passes 300 lines."""
    too_long = {p.name: _lines(p) for p in PROMO_DIR.glob("*.py") if _lines(p) > 300}
    assert too_long == {}


def test_evaluate_is_still_importable_from_the_engine():
    """Refactor goal: evaluate and explain stay importable from promotion_engine."""
    engine = importlib.import_module("market.features.promotions.promotion_engine")
    assert callable(engine.evaluate)
    assert callable(engine.explain)
