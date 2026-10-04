## 04. Step 3 · Checkout

Checkout validates the request, asks pricing for the discount and shipping for the fee, and closes the order into a receipt. The storefront shows the receipt and charges the total.

A regular customer checks out two items of 40.00 → the receipt has subtotal 80.00, discount 0.00, shipping 15.00 and total 95.00.

| ID | Rule | Source | Change via |
|---|---|---|---|
| CHK-01 | The total is the subtotal minus the discount plus shipping; every amount is rounded half up to cents. | src/orders/features/checkout/checkout_flow.py::compute_totals | code |
| CHK-02 | Checkout returns a Receipt with subtotal, discount, shipping and total, all Decimal. | src/orders/features/checkout/checkout_flow.py::Receipt | code |
| CHK-03 | A cart with no items is rejected with a ValueError. | src/orders/features/checkout/checkout_flow.py::validate_cart | code |
| CHK-04 | Every item needs a quantity of at least 1 and a price of zero or more, otherwise a ValueError. | src/orders/features/checkout/checkout_flow.py::validate_item | code |
| CHK-05 | A coupon percent must be above 0 and at most 100, otherwise a ValueError. | src/orders/features/checkout/checkout_flow.py::validate_coupon | code |
| CHK-06 | A customer needs a non-empty id, otherwise a ValueError. | src/orders/features/checkout/checkout_flow.py::validate_customer | code |
| CHK-07 | The receipt text lists Subtotal, Discount, Shipping and Total, in that order. | src/orders/features/checkout/checkout_flow.py::render_receipt_text | code |
