## 01. Summary

This PRD covers how an order is priced and closed: the discount a customer gets, the shipping fee and the receipt that checkout returns. Shoppers and the storefront call `checkout` with a cart, a customer and an optional coupon.

It delivers one `Receipt` with the subtotal, the discount, the shipping fee and the total. Money is always a `Decimal`, rounded half up to cents.

Neighboring systems (catalog, payment, stock) are out of scope: the cart arrives with its prices already resolved.

### Glossary

| Term | Meaning | Code name |
|---|---|---|
| Checkout | One pure call that prices exactly one cart and closes it into a receipt. It is stateless: it keeps no order history, reads no clock and touches no storage. | `checkout` |
| Customer | The shopper of the call, known only by the id and the flag the storefront sends with it. The storefront owns the customer record and everything that happens between calls. | `Customer` |
| VIP | A flag on the customer that the storefront sets and sends with each call. Checkout only reads it; it never decides who is VIP and cannot know how the flag was earned. | `Customer.vip` |
| Subtotal | The sum of unit price times quantity of the lines of one cart, before any discount. | `Receipt.subtotal` |
| Order history | The orders a customer placed before this call. It lives in the storefront; this service never sees it. | none |
