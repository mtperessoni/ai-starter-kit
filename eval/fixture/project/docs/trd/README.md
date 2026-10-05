# TRD

One TRD per feature (rule AR13, `docs/code-structure.md`): where the feature lives in the code, how it enters the flow, which tests cover it and what must not break. The rules are in the PRD ([index](../prd/INDEX.md)); the TRD never repeats them. Load only the file of the task's feature.

| Feature | TRD | Folder | PRD sections |
|---|---|---|---|
| Discount of a cart: VIP, coupon, cap | [pricing.md](pricing.md) | `src/orders/features/pricing/` | Orders: [02](../prd/orders/02-pricing.md) |
| Shipping fee and free-shipping threshold | [shipping.md](shipping.md) | `src/orders/features/shipping/` | Orders: [03](../prd/orders/03-shipping.md) |
| Validation, totals, rounding and the receipt | [checkout.md](checkout.md) | `src/orders/features/checkout/` | Orders: [04](../prd/orders/04-checkout.md) |

Cross-cutting:

- [infra.md](infra.md): `src/orders/infra/` (the cart value types).
- [invariants.md](invariants.md): repository rules by kind of change, each with the test or principle that proves it.
- [testing.md](testing.md): gates, how to run one file offline.
- [../flow.md](../flow.md): the one end-to-end diagram.

Whoever moves a file, an entry point or a test of a feature updates its TRD in the same commit. Symbol names, never line numbers or default values: they live in the code and change without anyone touching the map.
