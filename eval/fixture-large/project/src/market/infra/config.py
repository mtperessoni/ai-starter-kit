"""Tunable numbers behind every rule whose change goes via config (SPEC 2.10)."""
from decimal import Decimal

DEFAULTS: dict[str, object] = {
    "catalog.max_price": Decimal("100000.00"),
    "catalog.max_price_change_percent": Decimal("50"),
    "pricing.volume_tier1_qty": 10,
    "pricing.volume_tier1_percent": Decimal("5"),
    "pricing.volume_tier2_qty": 50,
    "pricing.volume_tier2_percent": Decimal("10"),
    "promo.max_total_discount_percent": Decimal("40"),
    "inventory.reservation_minutes": 30,
    "inventory.low_stock_threshold": 5,
    "cart.max_lines": 20,
    "cart.max_qty": 99,
    "cart.ttl_days": 7,
    "checkout.min_order_total": Decimal("10.00"),
    "shipping.free_threshold": Decimal("200.00"),
    "shipping.free_threshold_vip": Decimal("100.00"),
    "shipping.max_weight_grams": 30000,
    "shipping.express_multiplier": Decimal("1.5"),
    "shipping.surcharge_per_500g": Decimal("3.00"),
    "payments.max_attempts": 3,
    "payments.max_installments": 6,
    "payments.min_installment": Decimal("10.00"),
    "payments.interest_percent_per_extra_installment": Decimal("1.99"),
    "loyalty.redeem_min_points": 500,
    "loyalty.redeem_step": 100,
    "loyalty.max_redeem_percent": Decimal("50"),
    "loyalty.expiry_days": 365,
    "loyalty.vip_multiplier": 2,
    "returns.window_days": 30,
}

_overrides: dict[str, object] = {}


def get(key: str):
    if key not in DEFAULTS:
        raise KeyError(key)
    return _overrides.get(key, DEFAULTS[key])


def set(key: str, value: object) -> None:  # noqa: A001
    if key not in DEFAULTS:
        raise KeyError(key)
    _overrides[key] = value


def reset() -> None:
    _overrides.clear()
