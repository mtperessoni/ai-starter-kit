## 01. Summary

This PRD covers the marketplace order service: customers (standard or VIP) browse a catalog, fill a cart, apply coupons, check out with shipping, tax and optional loyalty points, pay by card, pix or gift card, and may cancel or return. Everything is in memory, synchronous and deterministic; the clock and the ids can be injected.

The storefront calls `market.api`. Money is always a `Decimal` with exactly 2 decimals; rounding is half up to cents and only where a rule says so.

Out of scope: real payment gateways, persistence, accounts and a user interface.

### Journey

| Step | What happens | Section |
|---|---|---|
| 1 | The product exists in the catalog | [02](02-catalog.md) |
| 2 | The customer fills a cart and applies coupons | [06](06-cart.md) |
| 3 | The cart is priced with volume breaks, sales and coupons | [03](03-pricing.md), [04](04-promotions.md) |
| 4 | Checkout adds shipping, tax and loyalty redemption | [07](07-checkout.md), [09](09-shipping.md), [10](10-tax.md), [11](11-loyalty.md) |
| 5 | Stock and coupon uses are held, then the payment is charged | [05](05-inventory.md), [08](08-payments.md) |
| 6 | Paid: stock and uses committed, points earned, email sent | [11](11-loyalty.md), [13](13-notifications.md) |
| 7 | Failed: hold released, uses given back, cart stays open | [07](07-checkout.md) |
| 8 | Cancel or return: refund, stock, points and email | [07](07-checkout.md), [12](12-returns.md) |

### Glossary (with code names)

| Term | Meaning | Code name |
|---|---|---|
| Product | Something sold, with a SKU | `Product` (`infra/models.py`) |
| Customer | A buyer, standard or VIP, with a region | `Customer` |
| Cart | Lines and coupon codes, no prices | `Cart`, `CartLine` |
| Quote | Priced cart: lines, discounts, total | `PriceQuote`, `LineQuote` |
| Order quote | Quote plus shipping, tax and loyalty | `OrderQuote` |
| Order | A placed cart with prices frozen | `Order`, `OrderLine` |
| Coupon | A code giving a percent, fixed or free-shipping benefit | `Coupon` |
| Category sale | A dated percent off one category | `CategorySale` |
| Buy-x-get-y | A free unit for every set bought | `BogoRule` |
| Bundle | A fixed amount off per complete set of SKUs | `Bundle` |
| Eligible line | A line promotions may discount (not a gift card) | `_eligible` |
| Reservation | A timed hold of stock for an order | `Reservation` |
| Payment | One charge and its refunds | `Payment`, `PaymentRequest` |
| Points lot | Points earned at one time, spent oldest first | `PointsLot` |
| Return | A request to send goods back | `ReturnRequest`, `RefundBreakdown` |
| Event | A fact published for other features | `Event` (`infra/events.py`) |
| Loyalty port | The only way checkout reaches loyalty | `LoyaltyPort` (`checkout/ports.py`) |

### Cross-feature rules

Rules that act on more than one feature carry a "Spans" note. Read all sections of a pair before changing one rule.

| Features in play | Rules |
|---|---|
| catalog, tax | CAT-03, TAX-02 |
| catalog, cart, checkout | CAT-05, CRT-04, CHK-01 |
| catalog, pricing | PRC-05 |
| catalog, promotions | PRM-12 |
| catalog, inventory | INV-07 |
| catalog, loyalty | LOY-03 |
| catalog, returns | RET-02 |
| catalog, shipping, checkout | SHP-04, CHK-05 |
| pricing, cart, checkout | PRC-01 |
| pricing, promotions, tax, returns | PRC-04, TAX-03, RET-03 |
| promotions, checkout, cart | PRM-04, CRT-06, CHK-10 |
| promotions, shipping | PRM-13, SHP-06 |
| inventory, cart | CRT-05 |
| inventory, notifications | INV-08, NTF-04 |
| checkout, pricing, shipping, tax, loyalty | CHK-03, SHP-03 |
| checkout, loyalty, tax | CHK-04, LOY-04, LOY-01 |
| checkout, payments, inventory, promotions | CHK-02, CHK-06 |
| checkout, payments, inventory, promotions, loyalty | CHK-09, LOY-06 |
| checkout, notifications | NTF-01 |
| payments, notifications | NTF-02 |
| shipping, returns | RET-04 |
| returns, inventory | RET-06 |
| returns, payments, checkout, loyalty | RET-07 |
