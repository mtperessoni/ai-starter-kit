# Orders

| ID | Rule | Source | Change via |
|---|---|---|---|
| ORD-01 | An order is created only from a cart with at least one item. | `src/orders.py::create_order` | code |
| ORD-02 | A paid order can be cancelled within 7 days. | `src/orders.py::cancel_order` | code |
| ORD-03 | Orders can be reopened. | planned | code |
| ORD-04 | An order keeps its history. | `src/orders.py::gone_fn` | code |

| ID | Question | Status |
|---|---|---|
| Q-01 | Should ORD-01 allow gift carts? | open |
