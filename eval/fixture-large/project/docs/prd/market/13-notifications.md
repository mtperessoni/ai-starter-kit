## 13. Notifications

Notifications sends the customer (and ops) an email when something happens in another feature. It only listens to events; it never changes an order.

A customer pays an order → one `order_confirmation` email goes to the customer's address, and a second paid event for the same order sends nothing.

| ID | Rule | Source | Change via |
|---|---|---|---|
| NTF-01 | A paid order sends the order_confirmation email to the customer. Spans: checkout, notifications. | src/market/features/notifications/notification_events.py::on_order_paid | code |
| NTF-02 | A failed payment sends payment_failed to the customer. Spans: payments, notifications. | src/market/features/notifications/notification_events.py::on_payment_failed | code |
| NTF-03 | A cancelled order sends order_cancelled; a completed return sends return_completed. | src/market/features/notifications/notification_events.py::on_order_cancelled | code |
| NTF-04 | A low-stock event sends low_stock to ops@market.test. Spans: inventory, notifications. | src/market/features/notifications/notification_events.py::on_low_stock | code |
| NTF-05 | The same template for the same order and recipient is sent only once. | src/market/features/notifications/dispatcher.py::send | code |

Related rules in other sections: the events come from [CHK-02](07-checkout.md) (paid), [PAY-03](08-payments.md) (failed), [CHK-09](07-checkout.md) (cancelled), [RET-07](12-returns.md) (return) and [INV-08](05-inventory.md) (low stock).
