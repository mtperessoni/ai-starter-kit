"""PAY-01, PAY-03, PAY-06, PAY-07: payment request, payment record and gateway result."""
from dataclasses import dataclass
from decimal import Decimal

METHODS = ("card", "pix", "gift_card")
STATUS_CAPTURED = "captured"
STATUS_FAILED = "failed"
STATUS_PARTIAL = "partially_refunded"
STATUS_REFUNDED = "refunded"


@dataclass(frozen=True)
class PaymentRequest:
    method: str
    token: str = ""
    installments: int = 1
    gift_card_code: str | None = None
    idempotency_key: str | None = None


@dataclass
class Payment:
    payment_id: str
    order_id: str
    customer_id: str
    method: str
    amount: Decimal
    captured: Decimal
    refunded: Decimal
    status: str
    installments: int
    installment_amount: Decimal
    gateway_ref: str | None
    decline_code: str | None
    idempotency_key: str | None
    gift_card_code: str | None

    @property
    def refundable(self) -> Decimal:
        """What can still be refunded: the order amount minus refunds so far (PAY-07, PAY-08)."""
        if self.status not in (STATUS_CAPTURED, STATUS_PARTIAL):
            return Decimal("0.00")
        return max(Decimal("0.00"), self.amount - self.refunded)


@dataclass(frozen=True)
class GatewayResult:
    approved: bool
    code: str
    reference: str | None
