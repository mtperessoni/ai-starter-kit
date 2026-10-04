"""LOY-04, CHK-04: the value of points a customer redeems, and the port checkout calls."""
from decimal import Decimal

from market.features.loyalty.points_ledger import balance
from market.infra import config
from market.infra.errors import PolicyError, ValidationError
from market.infra.money import pct, q2

POINTS_PER_UNIT = Decimal("100")


def redemption_value(customer_id: str, points: int, merchandise_total: Decimal) -> Decimal:
    """Money value of the points to redeem (100 points = 1.00), after the LOY-04 checks.

    Rules, in the order they are checked:
      - zero points is allowed and worth 0.00;
      - points are a multiple of 100 and at least 500 (ValidationError);
      - up to the balance (PolicyError insufficient_points);
      - the value is at most 50% of the merchandise after discounts (PolicyError redeem_limit).

        500 points on 200.00 -> 5.00      500 points on 8.00 -> redeem_limit (4.00 allowed)
    """
    if points == 0:
        return Decimal("0.00")
    if points < 0:
        raise ValidationError("points to redeem cannot be negative")
    step = config.get("loyalty.redeem_step")
    if points < config.get("loyalty.redeem_min_points") or points % step != 0:
        raise ValidationError(
            f"points must be a multiple of {step} and at least {config.get('loyalty.redeem_min_points')}"
        )
    if points > balance(customer_id):
        raise PolicyError("insufficient_points")
    value = q2(Decimal(points) / POINTS_PER_UNIT)
    allowed = q2(pct(merchandise_total, config.get("loyalty.max_redeem_percent")))
    if value > allowed:
        raise PolicyError("redeem_limit")
    return value


class LoyaltyRedemptionPort:
    """Implements checkout.ports.LoyaltyPort on top of the ledger."""

    def redemption_value(self, customer_id: str, points: int, merchandise_total: Decimal) -> Decimal:
        return redemption_value(customer_id, points, merchandise_total)


def max_redeemable_points(customer_id: str, merchandise_total: Decimal) -> int:
    """Largest redemption allowed now: within the balance, the step and 50% of the merchandise.

    Returns 0 when even the minimum of 500 points is out of reach (LOY-04).

        balance 2000, merchandise 200.00 -> 2000 points (limit 100.00)
        balance 2000, merchandise 12.00  -> 600 points  (limit 6.00)
    """
    step = config.get("loyalty.redeem_step")
    cap_value = q2(pct(merchandise_total, config.get("loyalty.max_redeem_percent")))
    cap_points = int(cap_value * POINTS_PER_UNIT)
    best = min(balance(customer_id), cap_points)
    best -= best % step
    return best if best >= config.get("loyalty.redeem_min_points") else 0
