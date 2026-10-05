"""CAT-01, CAT-02, CAT-03, CAT-06: product and price validation."""
import re
from decimal import Decimal

from market.features.catalog.category_rules import CATEGORIES, EXEMPT_CATEGORIES, is_digital
from market.infra import config
from market.infra.errors import ValidationError
from market.infra.models import Product
from market.infra.money import q2

_SKU_PATTERN = re.compile(r"^[A-Z0-9-]{3,20}$")
_MAX_WEIGHT_GRAMS = 30000
_MAX_NAME_LENGTH = 80


def _validate_price(price: Decimal) -> None:
    if not isinstance(price, Decimal):
        raise ValidationError("price must be a Decimal")
    if price <= 0:
        raise ValidationError("price must be above 0.00")
    if price != q2(price):
        raise ValidationError("price has at most 2 decimals")
    if price > config.get("catalog.max_price"):
        raise ValidationError("price above the maximum")


def validate_product(product: Product) -> None:
    if not _SKU_PATTERN.match(product.sku):
        raise ValidationError("sku must be 3 to 20 chars of A-Z, 0-9 and hyphen")
    name = product.name.strip()
    if not 1 <= len(name) <= _MAX_NAME_LENGTH:
        raise ValidationError("name must be 1 to 80 characters")
    if product.category not in CATEGORIES:
        raise ValidationError(f"unknown category {product.category}")
    _validate_price(product.price)
    if is_digital(product.category):
        if product.weight_grams != 0:
            raise ValidationError("gift cards weigh 0")
    elif not 1 <= product.weight_grams <= _MAX_WEIGHT_GRAMS:
        raise ValidationError("weight must be 1 to 30000 g")


def validate_price_change(old: Decimal, new: Decimal) -> None:
    _validate_price(new)
    limit = config.get("catalog.max_price_change_percent")
    if abs(new - old) * 100 / old > limit:
        raise ValidationError(f"a price may not change by more than {limit}%")


def taxable_class_for(category: str) -> str:
    return "exempt" if category in EXEMPT_CATEGORIES else "standard"
