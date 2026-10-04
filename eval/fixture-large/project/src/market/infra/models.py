"""Shared dataclasses: products, customers, carts, addresses (CAT-03, CRT-*, TAX-01)."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Product:
    sku: str
    name: str
    category: str
    price: Decimal
    weight_grams: int
    active: bool = True
    taxable_class: str = "standard"


@dataclass
class Customer:
    customer_id: str
    email: str
    tier: str = "standard"
    region: str = "SP"
    tax_exempt: bool = False


@dataclass
class CartLine:
    sku: str
    qty: int


@dataclass
class Cart:
    cart_id: str
    customer_id: str
    lines: list[CartLine]
    coupon_codes: list[str]
    updated_at: datetime
    status: str = "open"


@dataclass
class Address:
    country: str = "BR"
    region: str = "SP"
    postal_code: str = ""
