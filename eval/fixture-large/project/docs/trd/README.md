# TRD

One TRD per feature (rule AR13, `docs/code-structure.md`): where the feature lives in the code, how it enters the flow, which tests cover it and what must not break. The rules are in the PRD ([index](../prd/INDEX.md)); the TRD never repeats them. Load only the file of the task's feature.

| Feature | TRD | Folder | PRD sections |
|---|---|---|---|
| Products, validation, search | [catalog.md](catalog.md) | `src/market/features/catalog/` | Market: [02](../prd/market/02-catalog.md) |
| Quote of a cart: volume breaks, totals | [pricing.md](pricing.md) | `src/market/features/pricing/` | Market: [03](../prd/market/03-pricing.md) |
| Coupons, sales, bundles, the engine (big file `promotion_engine.py`) | [promotions.md](promotions.md) | `src/market/features/promotions/` | Market: [04](../prd/market/04-promotions.md) |
| Stock, holds, stock events | [inventory.md](inventory.md) | `src/market/features/inventory/` | Market: [05](../prd/market/05-inventory.md) |
| Cart lines, coupons, expiry | [cart.md](cart.md) | `src/market/features/cart/` | Market: [06](../prd/market/06-cart.md) |
| Quote, placement, order lifecycle | [checkout.md](checkout.md) | `src/market/features/checkout/` | Market: [07](../prd/market/07-checkout.md) |
| Charges, refunds, installments, gift cards | [payments.md](payments.md) | `src/market/features/payments/` | Market: [08](../prd/market/08-payments.md) |
| Shipping fee, zones, methods | [shipping.md](shipping.md) | `src/market/features/shipping/` | Market: [09](../prd/market/09-shipping.md) |
| Tax per line and on shipping | [tax.md](tax.md) | `src/market/features/tax/` | Market: [10](../prd/market/10-tax.md) |
| Points earned, redeemed, expired | [loyalty.md](loyalty.md) | `src/market/features/loyalty/` | Market: [11](../prd/market/11-loyalty.md) |
| Eligibility and refunds of returns | [returns.md](returns.md) | `src/market/features/returns/` | Market: [12](../prd/market/12-returns.md) |
| Emails reacting to events | [notifications.md](notifications.md) | `src/market/features/notifications/` | Market: [13](../prd/market/13-notifications.md) |

Cross-cutting:

- [infra.md](infra.md): `src/market/infra/` (errors, money, clock, config, events, repositories, ids, models, customers).
- [invariants.md](invariants.md): repository rules by kind of change, each with the test or principle that proves it.
- [testing.md](testing.md): gates, how to run one file offline.
- [../flow.md](../flow.md): the one end-to-end diagram.
- `src/market/api.py`: the public facade, wires the loyalty port and registers the handlers at import.

Big file: `src/market/features/promotions/promotion_engine.py` (about 700 lines). Read it by symbol, using the table in [promotions.md](promotions.md).

Whoever moves a file, an entry point or a test of a feature updates its TRD in the same commit. Symbol names, never line numbers or default values: they live in the code and change without anyone touching the map.
