## 02. Step 1 · Pricing

Pricing decides how much a customer saves on the subtotal of a cart. Two things give a discount: being a VIP customer and presenting a coupon. The storefront shows the result before the customer pays.

A VIP customer with a 10% coupon on a 100.00 cart → the system adds 15% and 10%, and the discount is 25.00.

| ID | Rule | Source | Change via |
|---|---|---|---|
| PRC-01 | VIP customers get 15% off the subtotal. | src/orders/features/pricing/discount_calculator.py::compute_discount | code |
| PRC-02 | A coupon gives its percentage off the subtotal. | src/orders/features/pricing/discount_calculator.py::compute_discount | code |
| PRC-03 | The total discount never exceeds 30% of the subtotal. | src/orders/features/pricing/discount_calculator.py::compute_discount | code |
| PRC-04 | The VIP and coupon percentages are added together before the cap applies. | src/orders/features/pricing/discount_calculator.py::compute_discount | code |
