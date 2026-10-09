## 01. Summary

This PRD covers the customer record of the storefront and the payload built from it. The orders service receives the payload with every checkout and prices the cart for that customer.

The storefront owns who a customer is and whether the customer is VIP. The orders service never decides either; it only reads what the payload says.

The orders service is a neighboring system, kept in its own repository: its rules are not restated here.
