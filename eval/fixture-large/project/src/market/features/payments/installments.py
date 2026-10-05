"""PAY-02: card installment plans with interest per extra installment."""
from decimal import Decimal

from market.infra import config
from market.infra.errors import ValidationError
from market.infra.money import pct, q2


def interest_for(amount: Decimal, installments: int) -> Decimal:
    """Interest on a card plan: 1.99% of the amount for each installment beyond the first.

    Rounded half up to cents once for the whole plan.

        100.00 in 3 installments -> 2 extra * 1.99% = 3.98
    """
    extra = installments - 1
    if extra <= 0:
        return Decimal("0.00")
    rate = config.get("payments.interest_percent_per_extra_installment")
    return q2(pct(amount, rate) * extra)


def installment_plan(amount: Decimal, installments: int) -> tuple[Decimal, Decimal]:
    """Return (total with interest, amount of each installment), each rounded half up.

    One installment has no interest, so the plan is (amount, amount).
    The number of installments must be between 1 and the configured maximum (6).

        installment_plan(Decimal("120.00"), 3) -> (Decimal("124.78"), Decimal("41.59"))
    """
    maximum = config.get("payments.max_installments")
    if not 1 <= installments <= maximum:
        raise ValidationError(f"installments must be between 1 and {maximum}")
    if amount <= 0:
        raise ValidationError("amount must be positive")
    total = q2(amount) + interest_for(amount, installments)
    each = q2(total / installments)
    return total, each


def check_minimum_installment(each: Decimal, installments: int) -> None:
    """Every installment of a multi-installment plan must reach the configured minimum (10.00)."""
    minimum = config.get("payments.min_installment")
    if installments > 1 and each < minimum:
        raise ValidationError(f"each installment must be at least {minimum}")


def installment_options(amount: Decimal) -> list[tuple[int, Decimal, Decimal]]:
    """Every card plan the customer may pick for an amount, as (count, total, each).

    Plans whose installments fall below the minimum (10.00) are left out, so a 15.00 purchase is
    offered one installment only (PAY-02).

        installment_options(Decimal("100.00"))[0] -> (1, Decimal("100.00"), Decimal("100.00"))
    """
    options: list[tuple[int, Decimal, Decimal]] = []
    for count in range(1, config.get("payments.max_installments") + 1):
        total, each = installment_plan(amount, count)
        if count > 1 and each < config.get("payments.min_installment"):
            break
        options.append((count, total, each))
    return options
