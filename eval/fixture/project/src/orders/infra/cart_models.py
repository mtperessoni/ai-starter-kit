"""CHK-02, CHK-03, CHK-04, CHK-05: the value types of the public API."""

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Customer:
    id: str
    vip: bool = False


@dataclass(frozen=True)
class CartItem:
    sku: str
    unit_price: Decimal
    qty: int


@dataclass
class Cart:
    items: list[CartItem] = field(default_factory=list)


@dataclass(frozen=True)
class Coupon:
    code: str
    percent: Decimal
