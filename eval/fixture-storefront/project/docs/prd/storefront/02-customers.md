## 02. Step 1 · Customers

A customer record holds an id, a full name and a VIP flag. The storefront builds a payload from the record and sends it to the orders service when the shopper checks out.

A VIP customer with id c1 → the payload is id c1 and vip true.

| ID | Rule | Source | Change via |
|---|---|---|---|
| CUS-01 | The payload sent to the orders service holds the customer id and the vip flag, and no other field. | src/storefront/features/customers/customer_payload.py::build_customer_payload | code |
| CUS-02 | The vip flag is true when the record is flagged VIP in the storefront and false otherwise. | src/storefront/features/customers/customer_payload.py::build_customer_payload | code |
| CUS-03 | A record with an empty id is not sent: building its payload raises a ValueError. | src/storefront/features/customers/customer_payload.py::build_customer_payload | code |
