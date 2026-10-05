"""PRM-01 to PRM-13: promotion dataclasses shared by the store, the engine and pricing."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Coupon:
    code: str
    kind: str
    value: Decimal
    min_subtotal: Decimal = Decimal("0")
    starts_on: date | None = None
    expires_on: date | None = None
    per_customer_limit: int | None = None
    global_limit: int | None = None
    categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class CategorySale:
    sale_id: str
    category: str
    percent: Decimal
    starts_on: date
    ends_on: date


@dataclass(frozen=True)
class BogoRule:
    rule_id: str
    sku: str
    buy: int = 2
    free: int = 1


@dataclass(frozen=True)
class Bundle:
    bundle_id: str
    skus: tuple[str, ...]
    amount_off: Decimal


@dataclass(frozen=True)
class PromoLine:
    sku: str
    category: str
    qty: int
    unit_price: Decimal
    value: Decimal


@dataclass(frozen=True)
class AppliedDiscount:
    code: str
    kind: str
    amount: Decimal
    line_amounts: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True)
class PromoResult:
    discounts: tuple[AppliedDiscount, ...]
    total: Decimal
    free_shipping: bool
    rejected: tuple[tuple[str, str], ...]
    applied_codes: tuple[str, ...]
