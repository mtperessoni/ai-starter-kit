# <folder> · <layer or role of this folder>

<One line: what this folder is and which areas have files here.>

| Area | Files here | PRD IDs | TRD |
|---|---|---|---|
| orders | `order_controller.<ext>`, `order_view.<ext>` | ORD-01 to ORD-12 | `docs/trd/orders.md` |
| payment | `payment_controller.<ext>` | PAY-03, PAY-05 | `docs/trd/payment.md` |

Must not break:
- a controller here never holds a business rule; it calls the area's service (ORD-04).

Tests: `<beside the code or the stack's mirrored tree, AR10>`.
