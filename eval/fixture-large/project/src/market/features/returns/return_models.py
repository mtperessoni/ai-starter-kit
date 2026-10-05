"""RET-03, RET-04, RET-07: refund breakdown and return request records."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

STATUS_COMPLETED = "completed"


@dataclass(frozen=True)
class RefundBreakdown:
    merchandise: Decimal
    tax: Decimal
    shipping: Decimal
    total: Decimal


@dataclass(frozen=True)
class ReturnRequest:
    return_id: str
    order_id: str
    customer_id: str
    items: tuple[tuple[str, int], ...]
    reason: str
    status: str
    refund: RefundBreakdown
    created_at: datetime
