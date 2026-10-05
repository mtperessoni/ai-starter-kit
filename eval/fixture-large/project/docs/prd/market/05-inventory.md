## 05. Inventory

Inventory tracks how many units of each product are on the shelf, holds units for an order in progress and raises events when stock runs low or returns.

Stock on hand 5, one order holds 2 → available is 3; if the hold is released, available is 5 again.

| ID | Rule | Source | Change via |
|---|---|---|---|
| INV-01 | Stock on hand is never negative. | src/market/features/inventory/stock_store.py::set_on_hand | code |
| INV-02 | Available stock is the stock on hand minus the quantities held by active reservations. | src/market/features/inventory/stock_store.py::available | code |
| INV-03 | A reservation is all or nothing: if any line is short, nothing is held and the error names every short SKU. | src/market/features/inventory/reservations.py::reserve | code |
| INV-04 | A reservation holds stock for 30 minutes; after that it expires and the stock is available again. Setting: `inventory.reservation_minutes`. | src/market/features/inventory/reservations.py::expire_due | config |
| INV-05 | Releasing an active reservation gives its stock back; releasing it again changes nothing. | src/market/features/inventory/reservations.py::release | code |
| INV-06 | Committing an active reservation removes the quantities from stock on hand and ends the hold; a released or expired reservation cannot be committed. | src/market/features/inventory/reservations.py::commit | code |
| INV-07 | Gift cards are not stock-tracked: always available, never reserved. Spans: catalog, inventory. | src/market/features/inventory/stock_store.py::available | code |
| INV-08 | When available stock falls to 5 or below from above 5, a low-stock event is raised once; when a SKU with nothing available gets stock, a restocked event is raised. Setting: `inventory.low_stock_threshold`. Spans: inventory, notifications. | src/market/features/inventory/low_stock.py::check_low_stock | config |

Related rules in other sections: the low-stock email in [NTF-04](13-notifications.md); stock checks on add to cart in [CRT-05](06-cart.md); the hold and release around a payment in [CHK-02](07-checkout.md) and [CHK-06](07-checkout.md); returned goods back to stock in [RET-06](12-returns.md).
