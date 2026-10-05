## 11. Loyalty

Loyalty gives points for paid orders, lets customers spend them as a discount and takes them back when an order is cancelled or returned. It listens to events; the core never calls it directly, except through the redemption port.

A VIP customer pays an order with 120.00 of merchandise → the order earns 240 points; 500 points can later be redeemed for 5.00 off.

| ID | Rule | Source | Change via |
|---|---|---|---|
| LOY-01 | A customer earns 1 point for each whole 1.00 of merchandise after discounts, when the order is paid; shipping and tax earn nothing. Spans: checkout, loyalty. | src/market/features/loyalty/points_earning.py::points_for_order | code |
| LOY-02 | VIP customers earn double. Setting: `loyalty.vip_multiplier`. | src/market/features/loyalty/points_earning.py::tier_multiplier | config |
| LOY-03 | Gift cards earn no points. Spans: catalog, loyalty. | src/market/features/loyalty/loyalty_events.py::on_order_paid | code |
| LOY-04 | Points can be redeemed in multiples of 100 (100 points = 1.00), at least 500 at a time, up to the balance and up to 50% of the merchandise after discounts. Settings: `loyalty.redeem_step`, `loyalty.redeem_min_points`, `loyalty.max_redeem_percent`. Spans: checkout, loyalty. | src/market/features/loyalty/points_redemption.py::redemption_value | config |
| LOY-05 | Points expire 365 days after they were earned; the oldest are spent first. Setting: `loyalty.expiry_days`. | src/market/features/loyalty/points_ledger.py::expire_lots | config |
| LOY-06 | A cancelled order or a return takes back the points it earned (never below a zero balance); a cancelled order gives back the points redeemed on it. Spans: loyalty, checkout, returns. | src/market/features/loyalty/loyalty_events.py::on_order_cancelled | code |
| LOY-07 | *(approved 2026-03-10, pending code)* The first paid order of a customer earns double the points it would normally earn. | planned | code |

Related rules in other sections: redemption inside the order total in [CHK-03](07-checkout.md) and [CHK-04](07-checkout.md); cancellation in [CHK-09](07-checkout.md); points taken back on a return in [RET-07](12-returns.md).
