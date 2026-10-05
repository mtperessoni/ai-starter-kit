"""CAT-03, CAT-04, CAT-05, CAT-06: product persistence and sellability."""
from decimal import Decimal

from market.features.catalog.product_validation import (taxable_class_for, validate_price_change,
                                                        validate_product)
from market.infra.errors import NotFoundError, ValidationError
from market.infra.models import Product
from market.infra.money import q2
from market.infra.repositories import repo

_REPO = "products"


def add_product(product: Product) -> Product:
    validate_product(product)
    if repo(_REPO).find(product.sku) is not None:
        raise ValidationError(f"sku {product.sku} already in the catalog")
    product.price = q2(product.price)
    product.taxable_class = taxable_class_for(product.category)
    repo(_REPO).add(product.sku, product)
    return product


def find_product(sku: str) -> Product | None:
    return repo(_REPO).find(sku)


def get_product(sku: str) -> Product:
    product = find_product(sku)
    if product is None:
        raise NotFoundError(f"product {sku} not found")
    return product


def list_products() -> list[Product]:
    return sorted(repo(_REPO).all(), key=lambda p: p.sku)


def require_sellable(sku: str) -> Product:
    product = get_product(sku)
    if not product.active:
        raise ValidationError(f"product {sku} is not for sale")
    return product


def deactivate_product(sku: str) -> Product:
    product = get_product(sku)
    product.active = False
    return product


def update_price(sku: str, new_price: Decimal) -> Product:
    product = get_product(sku)
    validate_price_change(product.price, new_price)
    product.price = q2(new_price)
    return product
