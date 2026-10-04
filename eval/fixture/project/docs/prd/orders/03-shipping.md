## 03. Step 2 · Shipping

Shipping adds a flat fee to every order, and waives it for larger orders so that customers are rewarded for bigger baskets.

A customer whose cart is worth 250.00 after discounts → shipping is 0.00. A customer whose cart is worth 80.00 after discounts → shipping is 15.00.

| ID | Rule | Source | Change via |
|---|---|---|---|
| SHP-01 | Shipping costs 15.00. | src/orders/features/shipping/shipping_fee.py::shipping_fee | code |
| SHP-02 | Shipping is free when the subtotal after discounts is 200.00 or more. | src/orders/features/shipping/shipping_fee.py::shipping_fee | code |
