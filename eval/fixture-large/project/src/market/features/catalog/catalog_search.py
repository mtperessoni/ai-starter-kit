"""CAT-07: search over active products."""
from decimal import Decimal

from market.features.catalog.product_store import list_products
from market.infra.errors import ValidationError
from market.infra.models import Product

_SORTS = ("name", "price_asc", "price_desc")


def search_products(query: str = "", category: str | None = None,
                    max_price: Decimal | None = None, sort: str = "name") -> list[Product]:
    if sort not in _SORTS:
        raise ValidationError(f"unknown sort {sort}")
    needle = query.strip().lower()
    found = [
        p for p in list_products()
        if p.active
        and (not needle or needle in p.name.lower() or needle in p.sku.lower())
        and (category is None or p.category == category)
        and (max_price is None or p.price <= max_price)
    ]
    if sort == "price_asc":
        return sorted(found, key=lambda p: (p.price, p.name.lower()))
    if sort == "price_desc":
        return sorted(found, key=lambda p: (-p.price, p.name.lower()))
    return sorted(found, key=lambda p: p.name.lower())
