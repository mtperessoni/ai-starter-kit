"""PRM-04: coupon use accounting (held at placement, committed on capture, released on failure)."""
from collections.abc import Sequence
from dataclasses import dataclass

from market.features.promotions.coupon_store import normalize_code
from market.infra.repositories import repo

_REPO = "promo_uses"
_COUNTED = ("held", "committed")


@dataclass
class _Use:
    order_id: str
    customer_id: str
    codes: tuple[str, ...]
    status: str


def hold_uses(order_id: str, customer_id: str, codes: Sequence[str]) -> None:
    unique = tuple(dict.fromkeys(normalize_code(c) for c in codes))
    repo(_REPO).save(order_id, _Use(order_id, customer_id, unique, "held"))


def commit_uses(order_id: str) -> None:
    use = repo(_REPO).find(order_id)
    if use is not None and use.status == "held":
        use.status = "committed"


def release_uses(order_id: str) -> None:
    use = repo(_REPO).find(order_id)
    if use is not None and use.status == "held":
        use.status = "released"


def usage_count(code: str, customer_id: str | None = None) -> int:
    wanted = normalize_code(code)
    return sum(
        1
        for use in repo(_REPO).all()
        if use.status in _COUNTED
        and wanted in use.codes
        and (customer_id is None or use.customer_id == customer_id)
    )
