## 01. Summary

This PRD covers how an order is priced and closed: the discount a customer gets, the shipping fee and the receipt that checkout returns. Shoppers and the storefront call `checkout` with a cart, a customer and an optional coupon.

It delivers one `Receipt` with the subtotal, the discount, the shipping fee and the total. Money is always a `Decimal`, rounded half up to cents.

Neighboring systems (catalog, payment, stock) are out of scope: the cart arrives with its prices already resolved.
