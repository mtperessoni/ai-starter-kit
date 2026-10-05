## 06. Cart

The cart holds what a customer intends to buy: SKUs, quantities and coupon codes. It stores no prices; it asks pricing for a quote.

A customer adds 2 units of BK-100, then 1 more → the cart has one line of 3 units; a coupon SAVE10 is accepted only if it is valid for that cart right now.

| ID | Rule | Source | Change via |
|---|---|---|---|
| CRT-01 | A line has 1 to 99 units; setting a quantity of 0 removes the line. Setting: `cart.max_qty`. | src/market/features/cart/cart_service.py::set_quantity | config |
| CRT-02 | Adding a SKU already in the cart adds to its quantity (the total still stays within 99). | src/market/features/cart/cart_service.py::add_item | code |
| CRT-03 | A cart has at most 20 different SKUs. Setting: `cart.max_lines`. | src/market/features/cart/cart_service.py::add_item | config |
| CRT-04 | Only known and active products can be added. Spans: catalog, cart. | src/market/features/cart/cart_service.py::add_item | code |
| CRT-05 | A quantity above the available stock cannot be added. Spans: inventory, cart. | src/market/features/cart/cart_service.py::add_item | code |
| CRT-06 | A coupon can be put on a cart only if it is valid for that cart right now; otherwise the reason is returned as an error. Reapplying the same code changes nothing. Spans: promotions, cart. | src/market/features/cart/cart_coupons.py::apply_coupon | code |
| CRT-07 | A cart untouched for 7 days is expired and cannot be changed or bought. Setting: `cart.ttl_days`. | src/market/features/cart/cart_expiry.py::is_expired | config |

Related rules in other sections: product rules in [CAT-05](02-catalog.md); coupon validity in [PRM-03](04-promotions.md) and [PRM-04](04-promotions.md); buying an unexpired cart in [CHK-01](07-checkout.md).
