"""PAY-05, PAY-07: gift card balances, debited on payment and credited back on refund."""
from decimal import Decimal

from market.infra.errors import NotFoundError, PolicyError, ValidationError
from market.infra.money import q2
from market.infra.repositories import repo

_REPO = "gift_cards"


def _normalize(code: str) -> str:
    return code.strip().upper()


def _require_positive(amount: Decimal) -> Decimal:
    if amount <= 0:
        raise ValidationError("amount must be positive")
    return q2(amount)


def has_gift_card(code: str) -> bool:
    """True when a card with this code was issued."""
    return repo(_REPO).find(_normalize(code)) is not None


def issue_gift_card(code: str, balance: Decimal) -> None:
    """Create a gift card with an opening balance; a code can be issued once only."""
    normalized = _normalize(code)
    if not normalized:
        raise ValidationError("gift card code is empty")
    if balance < 0:
        raise ValidationError("gift card balance cannot be negative")
    if repo(_REPO).find(normalized) is not None:
        raise ValidationError(f"gift card {normalized} already exists")
    repo(_REPO).add(normalized, q2(balance))


def gift_card_balance(code: str) -> Decimal:
    """Current balance of a card; an unknown code raises NotFoundError."""
    balance = repo(_REPO).find(_normalize(code))
    if balance is None:
        raise NotFoundError(f"gift card {_normalize(code)} not found")
    return balance


def debit_gift_card(code: str, amount: Decimal) -> None:
    """Take money from the balance; refuses to go below zero.

    A balance of 100.00 debited by 30.00 becomes 70.00; debiting 100.01 raises
    PolicyError("insufficient_balance") and changes nothing.
    """
    amount = _require_positive(amount)
    balance = gift_card_balance(code)
    if balance < amount:
        raise PolicyError("insufficient_balance")
    repo(_REPO).save(_normalize(code), balance - amount)


def credit_gift_card(code: str, amount: Decimal) -> None:
    """Give money back to the balance (PAY-07: refunds of a gift-card payment return here)."""
    amount = _require_positive(amount)
    balance = gift_card_balance(code)
    repo(_REPO).save(_normalize(code), balance + amount)


def outstanding_balance() -> Decimal:
    """Money still held on all gift cards, the amount the market owes its customers."""
    return sum(repo(_REPO).all(), Decimal("0.00"))
