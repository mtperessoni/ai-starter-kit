## 07. Checkout

Checkout turns a cart into an order: it quotes, validates, holds stock and coupon uses, charges the payment and then commits or rolls back. The storefront calls it once per attempt.

A regular customer in SP buys one 120.00 item and pays by card → the order is paid, stock is committed, the coupon use is counted and the cart is closed.

| ID | Rule | Source | Change via |
|---|---|---|---|
| CHK-01 | An order is placed only from an open, unexpired cart with at least one line whose products are all still sellable. Spans: checkout, cart, catalog. | src/market/features/checkout/order_placement.py::place_order | code |
| CHK-02 | Placing an order runs in this order: quote, validate, reserve stock, hold coupon uses, create the order, charge, then commit or roll back. Spans: checkout, cart, pricing, promotions, inventory, payments. | src/market/features/checkout/order_placement.py::place_order | code |
| CHK-03 | Order total = merchandise after discounts + shipping + tax - loyalty discount, never below 0.00. Spans: checkout, pricing, shipping, tax, loyalty. | src/market/features/checkout/order_quote.py::build_quote | code |
| CHK-04 | Loyalty points are redeemed after tax: the loyalty discount reduces the amount to pay, not the tax base. Spans: checkout, loyalty, tax. | src/market/features/checkout/order_quote.py::build_quote | code |
| CHK-05 | An order with any physical item needs an address; a gift-card-only order does not. Spans: checkout, shipping, catalog. | src/market/features/checkout/order_validation.py::validate_checkout | code |
| CHK-06 | When a payment fails, the stock hold is released and the coupon uses are given back; the order becomes payment_failed and the cart stays open for another try. Spans: checkout, payments, inventory, promotions. | src/market/features/checkout/order_placement.py::_rollback | code |
| CHK-07 | Merchandise after discounts must be at least 10.00. Setting: `checkout.min_order_total`. | src/market/features/checkout/order_validation.py::validate_checkout | config |
| CHK-08 | An order moves pending, then paid or payment_failed; paid, then shipped, then delivered; a delivered order becomes partially_refunded or refunded through returns. | src/market/features/checkout/order_lifecycle.py::mark_shipped | code |
| CHK-09 | Only a paid order (not yet shipped) can be cancelled: full refund of what was captured, stock back, coupon uses given back, points earned reversed and redeemed points returned. Spans: checkout, payments, inventory, promotions, loyalty. | src/market/features/checkout/order_lifecycle.py::cancel_order | code |
| CHK-10 | An order is not placed if a coupon on the cart is no longer valid; the customer gets the reason. Spans: checkout, promotions. | src/market/features/checkout/order_validation.py::validate_checkout | code |

Related rules in other sections: the sequence is drawn in [flow.md](../../flow.md); points redeemed in [LOY-04](11-loyalty.md); shipping and tax amounts in [SHP-03](09-shipping.md) and [TAX-03](10-tax.md); refund of a delivered order in [RET-07](12-returns.md).
