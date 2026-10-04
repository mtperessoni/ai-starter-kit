## 04. Promotions

Promotions decide which discounts a cart earns: category sales, buy-x-get-y, coupons and bundles. The discount engine is one big file, `promotion_engine.py`, read by symbol.

A cart with a bundle of two books (100.00) and the coupon SAVE10 → the coupon takes 10.00 first, then the bundle takes 15.00, and the discount is 25.00.

| ID | Rule | Source | Change via |
|---|---|---|---|
| PRM-01 | Coupon codes ignore case and surrounding spaces. A code that is not found is rejected as `unknown`; a rejected coupon never fails the quote, it is listed with its reason. | src/market/features/promotions/coupon_store.py::normalize_code | code |
| PRM-02 | A percent coupon takes its percent off the current value of the eligible lines (rounded half up to cents once for the coupon), only if the eligible list subtotal reaches its minimum, otherwise `below_minimum`. A coupon may be limited to some categories. | src/market/features/promotions/promotion_engine.py::stage_percent_coupons | code |
| PRM-03 | A coupon is valid from its start date to its expiry date, both days included. | src/market/features/promotions/coupon_validation.py::check_coupon | code |
| PRM-04 | A coupon has an optional limit per customer and an optional global limit. A use is held when the order is placed, counts for good when the payment is captured, and is given back when the payment fails or the order is cancelled. Spans: promotions, checkout, cart. | src/market/features/promotions/promotion_usage.py::hold_uses | code |
| PRM-05 | Discounts apply in this order: category sale, buy-x-get-y, percent coupon, bundle, fixed coupon, free-shipping flag. Each step works on what the previous steps left. | src/market/features/promotions/promotion_engine.py::PIPELINE | code |
| PRM-06 | At most one coupon of each kind (percent, fixed, free shipping) applies to an order; the first one in the cart wins, the others are rejected as `kind_already_applied`. | src/market/features/promotions/promotion_engine.py::_resolve_coupons | code |
| PRM-07 | A category sale takes its percent off every eligible line of its category from its start date to its end date, both days included. | src/market/features/promotions/promotion_engine.py::stage_category_sales | code |
| PRM-08 | Buy 2 get 1 free: for every 3 units of the rule's SKU one unit is free, valued at that line's current value per unit (rounded half up to cents). | src/market/features/promotions/promotion_engine.py::stage_bogo | code |
| PRM-09 | A bundle gives its fixed amount off for every complete set of its SKUs in the cart (sets = the smallest quantity among its SKUs), never more than the current value of the bundle lines. | src/market/features/promotions/promotion_engine.py::stage_bundles | code |
| PRM-10 | A fixed coupon takes its amount off the current total of the eligible lines, only if the minimum is reached, never more than that total. | src/market/features/promotions/promotion_engine.py::stage_fixed_coupons | code |
| PRM-11 | All promotion discounts together never exceed 40% of the eligible list subtotal; a step that would pass the limit is cut to what is left. Setting: `promo.max_total_discount_percent`. | src/market/features/promotions/promotion_engine.py::_headroom | config |
| PRM-12 | Gift cards are never discounted by any promotion and do not count toward coupon minimums. Spans: catalog, promotions. | src/market/features/promotions/promotion_engine.py::_eligible | code |
| PRM-13 | A free-shipping coupon follows the same validity checks and gives no money discount; it only sets the free-shipping flag the checkout passes to shipping. Spans: promotions, shipping. | src/market/features/promotions/promotion_engine.py::stage_free_shipping | code |

Related rules in other sections: uses are held, committed and released by checkout in [CHK-02](07-checkout.md), [CHK-06](07-checkout.md) and [CHK-09](07-checkout.md); the flag reaches shipping in [SHP-06](09-shipping.md); a coupon on a cart in [CRT-06](06-cart.md).
