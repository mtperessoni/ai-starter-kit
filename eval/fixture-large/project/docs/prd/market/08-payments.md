## 08. Payments

Payments charges an order by card, pix or gift card and refunds it. A decline is a normal outcome, not an error: the order records it and the customer can try again.

A customer pays 100.00 by card in 3 installments → the interest is 1.99% per extra installment, rounded half up to cents, and the card is charged once.

| ID | Rule | Source | Change via |
|---|---|---|---|
| PAY-01 | Accepted methods are card, pix and gift card; any other method is rejected. | src/market/features/payments/payment_service.py::charge | code |
| PAY-02 | Card can be paid in 1 to 6 installments with 1.99% interest per extra installment (rounded half up to cents), each installment at least 10.00; pix and gift card are 1 installment. Settings: `payments.max_installments`, `payments.min_installment`, `payments.interest_percent_per_extra_installment`. | src/market/features/payments/installments.py::installment_plan | config |
| PAY-03 | A declined payment records the decline code, is never captured, and raises a payment-failed event. | src/market/features/payments/payment_service.py::charge | code |
| PAY-04 | A payment that times out at the gateway is tried again, up to 3 attempts in all; if every attempt times out it is declined as `gateway_timeout`. Setting: `payments.max_attempts`. | src/market/features/payments/payment_service.py::charge | config |
| PAY-05 | Paying with a gift card takes the amount from its balance; not enough balance declines as `insufficient_balance`, an unknown code as `unknown_gift_card`. | src/market/features/payments/payment_service.py::charge | code |
| PAY-06 | The same idempotency key returns the first payment and never charges twice. | src/market/features/payments/payment_service.py::charge | code |
| PAY-07 | The sum of refunds of a payment never exceeds what was captured; refunds of a gift-card payment go back to the card balance. | src/market/features/payments/payment_service.py::refund | code |
| PAY-08 | Interest on installments is not refunded; a refund returns at most the order amount. | src/market/features/payments/payment_service.py::refund | code |

Related rules in other sections: the payment-failed email in [NTF-02](13-notifications.md); the rollback after a decline in [CHK-06](07-checkout.md); refunds of cancellations and returns in [CHK-09](07-checkout.md) and [RET-07](12-returns.md).
