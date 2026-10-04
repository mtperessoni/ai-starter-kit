## 10. Tax

Tax adds a sales tax on top of the price, by the delivery region, line by line and on shipping.

A 100.00 electronics line shipped to SP with 10.00 shipping → tax is 8.00 on the line and 0.80 on shipping.

| ID | Rule | Source | Change via |
|---|---|---|---|
| TAX-01 | The tax rate follows the delivery region: 8% SP, 10% RJ, 9% MG, 7% elsewhere; without an address the customer's region is used. | src/market/features/tax/tax_rates.py::rate_for | code |
| TAX-02 | Exempt products (books, grocery, gift cards) pay no tax; a tax-exempt customer pays none at all. Spans: catalog, tax. | src/market/features/tax/tax_calculator.py::compute_tax | code |
| TAX-03 | Tax per line is the rate on the line total after discounts, rounded half up to cents, then summed. Spans: pricing, promotions, tax. | src/market/features/tax/tax_calculator.py::compute_tax | code |
| TAX-04 | Shipping is taxed at the same rate (rounded half up to cents); free shipping has no tax. | src/market/features/tax/tax_calculator.py::compute_tax | code |
| TAX-05 | Tax is added on top of the price, never included in it. | src/market/features/tax/tax_calculator.py::compute_tax | code |

Related rules in other sections: exempt categories in [CAT-03](02-catalog.md); the line total after the split in [PRC-04](03-pricing.md); the tax base against loyalty in [CHK-04](07-checkout.md); tax in a refund in [RET-03](12-returns.md).
