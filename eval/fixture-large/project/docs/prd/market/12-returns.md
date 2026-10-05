## 12. Returns

Returns lets a customer send back goods from a delivered order and gets the money back, with stock and points adjusted.

A customer returns 1 of 2 units of a 60.00 line, reason `changed_mind`, 10 days after delivery → the refund is 30.00 plus the tax of that unit, and no shipping.

| ID | Rule | Source | Change via |
|---|---|---|---|
| RET-01 | A return must start within 30 days after delivery, on a delivered or partially refunded order. Setting: `returns.window_days`. | src/market/features/returns/return_policy.py::check_eligibility | config |
| RET-02 | Gift cards and grocery cannot be returned. Spans: catalog, returns. | src/market/features/returns/return_policy.py::check_eligibility | code |
| RET-03 | The refund is the line total after discounts, divided by the line quantity, times the units returned (rounded half up to cents), plus the tax of those units the same way. Spans: pricing, tax, returns. | src/market/features/returns/refund_calculator.py::compute_refund | code |
| RET-04 | Shipping is refunded only for reasons `defective` or `wrong_item`, and only when this return brings the returned units to every unit of the order. Spans: shipping, returns. | src/market/features/returns/refund_calculator.py::compute_refund | code |
| RET-05 | A customer cannot return more units than bought minus already returned; reasons are defective, wrong_item, changed_mind, other. | src/market/features/returns/return_policy.py::check_eligibility | code |
| RET-06 | Returned goods go back to stock, except when the reason is `defective`. Spans: returns, inventory. | src/market/features/returns/return_service.py::request_return | code |
| RET-07 | A completed return refunds the payment, lowers the order status and takes back the points earned on the returned merchandise. Spans: returns, payments, checkout, loyalty. | src/market/features/returns/return_service.py::request_return | code |

Related rules in other sections: not returnable categories in [CAT-03](02-catalog.md); status moves in [CHK-08](07-checkout.md); refund limits in [PAY-07](08-payments.md); points in [LOY-06](11-loyalty.md); the completed-return email in [NTF-03](13-notifications.md).
