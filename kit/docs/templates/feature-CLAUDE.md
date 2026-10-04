# features/<f> · <Feature name>

<One sentence: what this feature does.>

- Rules: ORD-01 to ORD-12 in `docs/prd/product/05-orders.md`; PAY-03 in `06-payment.md`; index in `docs/prd/INDEX.md`.
- Entry: `OrderService` (`order_service.py`), facade that composes the collaborators; stable public interface.
- Collaborators: `order_creation` (validates and stores), `order_cancellation` (timeout and manual), `order_events` (publishes).
- Domain: `domain/order.py` (states and transitions), `domain/order_total.py`.

Must not break:
- an order is never charged twice for the same cart (ORD-04);
- cancellation after payment always refunds (ORD-09).

Tests: `tests/` in this folder. Outside it: `tests/integration/test_order_flow.py`.

TRD: `docs/trd/orders.md`
