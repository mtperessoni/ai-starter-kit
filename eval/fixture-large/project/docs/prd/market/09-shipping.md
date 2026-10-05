## 09. Shipping

Shipping prices the delivery of an order by region, weight and method, and decides when it is free. An order of only gift cards has no shipping.

A regular customer in SP orders 1800 g of goods worth 200.00 → shipping is free because the merchandise reaches the threshold.

| ID | Rule | Source | Change via |
|---|---|---|---|
| SHP-01 | Standard shipping starts at 10.00 to SP, 18.00 to RJ, MG and ES, and 30.00 to any other region. | src/market/features/shipping/shipping_zones.py::zone_for | code |
| SHP-02 | The first 1000 g are included; each further started 500 g adds 3.00. Setting: `shipping.surcharge_per_500g`. | src/market/features/shipping/shipping_rules.py::weight_surcharge | config |
| SHP-03 | Standard shipping is free when merchandise after discounts is 200.00 or more, 100.00 or more for VIP customers. Settings: `shipping.free_threshold`, `shipping.free_threshold_vip`. Spans: shipping, pricing, customers. | src/market/features/shipping/shipping_rules.py::free_threshold | config |
| SHP-04 | An order of only gift cards has no shipping: fee 0.00, no delivery days. Spans: catalog, shipping, checkout. | src/market/features/shipping/shipping_rules.py::is_digital_only | code |
| SHP-05 | Express costs 1.5 times the standard fee before any waiver (rounded half up to cents) and is never free; it is not offered for gift-card-only orders. Setting: `shipping.express_multiplier`. | src/market/features/shipping/shipping_fee.py::quote_shipping | config |
| SHP-06 | Delivery takes 3, 5 or 8 days (standard) and 1, 2 or 4 (express) by zone; an order over 30000 g of physical goods is refused. A free-shipping coupon waives the standard fee (free reason `coupon`); threshold and coupon waivers apply to standard only. Setting: `shipping.max_weight_grams`. Spans: shipping, promotions (coupon waiver). | src/market/features/shipping/shipping_fee.py::quote_shipping | config |

Related rules in other sections: the free-shipping flag from [PRM-13](04-promotions.md); the address requirement in [CHK-05](07-checkout.md); tax on shipping in [TAX-04](10-tax.md); shipping refund in [RET-04](12-returns.md).
