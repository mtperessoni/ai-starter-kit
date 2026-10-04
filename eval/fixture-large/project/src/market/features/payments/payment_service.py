"""PAY-01 to PAY-08: charge, decline handling, retries, idempotency and refunds."""
from decimal import Decimal

from market.features.payments import gift_cards
from market.features.payments.gateway import TIMEOUT, authorize
from market.features.payments.installments import check_minimum_installment, installment_plan
from market.features.payments.payment_models import (METHODS, STATUS_CAPTURED, STATUS_FAILED,
                                                      STATUS_PARTIAL, STATUS_REFUNDED, GatewayResult,
                                                      Payment, PaymentRequest)
from market.infra import config, events, ids
from market.infra.errors import NotFoundError, PolicyError, ValidationError
from market.infra.money import q2
from market.infra.repositories import repo

_REPO = "payments"


def get_payment(payment_id: str) -> Payment:
    return repo(_REPO).get(payment_id)


def _find_by_key(key: str | None) -> Payment | None:
    if key is None:
        return None
    return next((p for p in repo(_REPO).all() if p.idempotency_key == key), None)


def _plan(amount: Decimal, request: PaymentRequest) -> tuple[Decimal, Decimal]:
    """Validate the method and installments and return (total to capture, each installment)."""
    if request.method not in METHODS:
        raise ValidationError(f"payment method {request.method} is not accepted")
    if request.method != "card":
        if request.installments != 1:
            raise ValidationError(f"{request.method} is paid in 1 installment")
        return q2(amount), q2(amount)
    total, each = installment_plan(amount, request.installments)
    check_minimum_installment(each, request.installments)
    return total, each


def _run_gateway(request: PaymentRequest, amount: Decimal) -> GatewayResult:
    """Try the gateway; a timeout is retried up to the configured attempts (PAY-04)."""
    result = authorize(request.method, request.token, amount, 1)
    attempt = 1
    while result.code == TIMEOUT and attempt < config.get("payments.max_attempts"):
        attempt += 1
        result = authorize(request.method, request.token, amount, attempt)
    return result


def _take_gift_card(request: PaymentRequest, amount: Decimal) -> GatewayResult:
    """Debit the card balance; a failure is a decline, never an exception (PAY-05)."""
    code = request.gift_card_code
    if code is None or not gift_cards.has_gift_card(code):
        return GatewayResult(False, "unknown_gift_card", None)
    if gift_cards.gift_card_balance(code) < amount:
        return GatewayResult(False, "insufficient_balance", None)
    gift_cards.debit_gift_card(code, amount)
    return GatewayResult(True, "approved", None)


def _record(order_id: str, customer_id: str, amount: Decimal, request: PaymentRequest,
            result: GatewayResult, captured: Decimal, each: Decimal) -> Payment:
    payment = Payment(
        payment_id=ids.next_id("PAY"), order_id=order_id, customer_id=customer_id,
        method=request.method, amount=amount,
        captured=captured if result.approved else Decimal("0.00"), refunded=Decimal("0.00"),
        status=STATUS_CAPTURED if result.approved else STATUS_FAILED,
        installments=request.installments, installment_amount=each,
        gateway_ref=result.reference, decline_code=None if result.approved else result.code,
        idempotency_key=request.idempotency_key, gift_card_code=request.gift_card_code,
    )
    repo(_REPO).add(payment.payment_id, payment)
    return payment


def charge(order_id: str, customer_id: str, amount: Decimal, request: PaymentRequest) -> Payment:
    """Charge an order amount; a decline is recorded and returned, never raised (PAY-03).

    Raises ValidationError for an unknown method, a bad number of installments or an installment
    below the minimum (PAY-01, PAY-02). The same idempotency key returns the first payment and
    never charges twice (PAY-06). A card pays interest on top: `captured` is the amount with
    interest, `amount` stays the order amount (PAY-08).
    """
    existing = _find_by_key(request.idempotency_key)
    if existing is not None:
        return existing
    if amount <= 0:
        raise ValidationError("amount must be positive")
    amount = q2(amount)
    total, each = _plan(amount, request)
    if request.method == "gift_card":
        result = _take_gift_card(request, amount)
    else:
        result = _run_gateway(request, total)
    payment = _record(order_id, customer_id, amount, request, result, total, each)
    if result.approved:
        events.publish("payment.captured", payment_id=payment.payment_id, order_id=order_id,
                       amount=payment.captured)
    else:
        events.publish("payment.failed", payment_id=payment.payment_id, order_id=order_id,
                       customer_id=customer_id, code=payment.decline_code)
    return payment


def refund(payment_id: str, amount: Decimal) -> Payment:
    """Refund part or all of a captured payment (PAY-07, PAY-08).

    The refunds of a payment never exceed the order amount, so interest is not returned. A
    gift-card payment is refunded to the card balance. The status becomes partially_refunded, then
    refunded when nothing is left.
    """
    payment = get_payment(payment_id)
    amount = q2(amount)
    if amount <= 0:
        raise ValidationError("refund amount must be positive")
    if payment.status not in (STATUS_CAPTURED, STATUS_PARTIAL):
        raise PolicyError(f"payment_{payment.status}")
    if amount > payment.refundable:
        raise PolicyError("refund_exceeds_captured")
    if payment.method == "gift_card" and payment.gift_card_code is not None:
        try:
            gift_cards.credit_gift_card(payment.gift_card_code, amount)
        except NotFoundError as error:
            raise PolicyError("unknown_gift_card") from error
    payment.refunded += amount
    payment.status = STATUS_REFUNDED if payment.refundable == 0 else STATUS_PARTIAL
    events.publish("payment.refunded", payment_id=payment_id, order_id=payment.order_id, amount=amount)
    return payment


def payments_for_order(order_id: str) -> list[Payment]:
    """Every payment attempt of an order in the order they were made, failed ones included."""
    return [p for p in repo(_REPO).all() if p.order_id == order_id]


def total_refunded(order_id: str) -> Decimal:
    """Money refunded so far across the payments of an order (PAY-07)."""
    return sum((p.refunded for p in payments_for_order(order_id)), Decimal("0.00"))


def describe(payment: Payment) -> str:
    """One line for logs and receipts.

        PAY-0001 card captured 100.00 in 3x of 34.66
        PAY-0002 card failed 100.00 (card_declined)
    """
    head = f"{payment.payment_id} {payment.method} {payment.status} {payment.amount}"
    if payment.status == STATUS_FAILED:
        return f"{head} ({payment.decline_code})"
    if payment.installments > 1:
        return f"{head} in {payment.installments}x of {payment.installment_amount}"
    return head
