## 03. Pricing

Pricing turns the lines of a cart into a quote: what each line costs, which discounts apply and what the customer owes for the goods. The storefront shows the quote before checkout.

A cart with 2 units of a 40.00 book → the quote has subtotal 80.00, no discount and total 80.00.

| ID | Rule | Source | Change via |
|---|---|---|---|
| PRC-01 | A line subtotal is the current catalog price times the quantity; the cart subtotal is the sum of line subtotals. A cart line never stores a price, and an order keeps the prices it was placed with. Spans: catalog, cart, checkout. | src/market/features/pricing/price_calculator.py::quote_lines | code |
| PRC-02 | An empty cart quotes zero everywhere. The total is the subtotal minus all discounts and never goes below 0.00. | src/market/features/pricing/price_calculator.py::quote_lines | code |
| PRC-03 | Volume break per line, before any promotion: 10 or more units of one SKU get 5% off that line, 50 or more get 10% (rounded half up to cents). Settings: `pricing.volume_tier1_qty`, `pricing.volume_tier1_percent`, `pricing.volume_tier2_qty`, `pricing.volume_tier2_percent`. | src/market/features/pricing/volume_breaks.py::volume_discount | config |
| PRC-04 | A discount shared by several lines is split in proportion to their value, rounded half up to cents, with the last line taking the remainder so the pieces add up exactly. Tax and refunds use the line total after this split. Spans: pricing, promotions, tax, returns. | src/market/infra/money.py::allocate | code |
| PRC-05 | Gift cards never get a volume break. Spans: catalog, pricing. | src/market/features/pricing/volume_breaks.py::volume_percent | code |
| PRC-06 | The quote lists every discount with its code, kind and amount, and the coupons it rejected with the reason. | src/market/features/pricing/price_calculator.py::quote_lines | code |

Related rules in other sections: the coupon and sale discounts are in [04-promotions](04-promotions.md) (PRM-02 to PRM-13); tax and refunds on the split line total in [TAX-03](10-tax.md) and [RET-03](12-returns.md).
