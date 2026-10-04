"""PRM-01, PRM-02, PRM-07, PRM-08, PRM-09: coupon, sale, bogo and bundle definitions."""
from dataclasses import replace
from datetime import date
from decimal import Decimal

from market.features.promotions.promotion_models import BogoRule, Bundle, CategorySale, Coupon
from market.infra.errors import NotFoundError, ValidationError
from market.infra.repositories import repo

COUPON_KINDS = ("percent", "fixed", "free_shipping")


def normalize_code(code: str) -> str:
    return code.strip().upper()


def add_coupon(coupon: Coupon) -> Coupon:
    code = normalize_code(coupon.code)
    if not code:
        raise ValidationError("coupon code is empty")
    if coupon.kind not in COUPON_KINDS:
        raise ValidationError(f"unknown coupon kind {coupon.kind}")
    if coupon.kind == "percent" and not Decimal("0") < coupon.value <= Decimal("100"):
        raise ValidationError("percent must be above 0 and at most 100")
    if coupon.kind == "fixed" and coupon.value <= 0:
        raise ValidationError("fixed amount must be above 0")
    if coupon.starts_on and coupon.expires_on and coupon.expires_on < coupon.starts_on:
        raise ValidationError("coupon expires before it starts")
    if repo("coupons").find(code) is not None:
        raise ValidationError(f"coupon {code} already exists")
    stored = replace(coupon, code=code)
    repo("coupons").add(code, stored)
    return stored


def get_coupon(code: str) -> Coupon:
    coupon = find_coupon(code)
    if coupon is None:
        raise NotFoundError(f"coupon {normalize_code(code)} not found")
    return coupon


def find_coupon(code: str) -> Coupon | None:
    return repo("coupons").find(normalize_code(code))


def add_category_sale(sale: CategorySale) -> CategorySale:
    if not Decimal("0") < sale.percent <= Decimal("100"):
        raise ValidationError("sale percent must be above 0 and at most 100")
    if sale.ends_on < sale.starts_on:
        raise ValidationError("sale ends before it starts")
    repo("category_sales").add(sale.sale_id, sale)
    return sale


def add_bogo(rule: BogoRule) -> BogoRule:
    if rule.buy < 1 or rule.free < 1:
        raise ValidationError("bogo needs buy and free of at least 1")
    repo("bogo_rules").add(rule.rule_id, rule)
    return rule


def add_bundle(bundle: Bundle) -> Bundle:
    if len(set(bundle.skus)) < 2 or bundle.amount_off <= 0:
        raise ValidationError("a bundle needs 2 distinct skus and a positive amount")
    repo("bundles").add(bundle.bundle_id, bundle)
    return bundle


def active_sales(today: date) -> list[CategorySale]:
    return [s for s in repo("category_sales").all() if s.starts_on <= today <= s.ends_on]


def bogo_rules() -> list[BogoRule]:
    return repo("bogo_rules").all()


def bundles() -> list[Bundle]:
    return repo("bundles").all()
