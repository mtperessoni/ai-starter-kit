# TRD · infra

Shared code. Map of `src/orders/infra/`.

## Where it lives

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `cart_models.py` | The value types of the public API | `Customer`, `CartItem`, `Cart`, `Coupon` | CHK-02..06 |

## Must not break
- The fields and defaults of the types are the public API of `orders`.

## History
- 2026-01-05: created by trd-create from the seed commit.
