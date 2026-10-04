## 02. Catalog

The catalog is the list of products the marketplace sells: SKU, name, category, price and weight. Everything else reads it; nothing else changes it.

A product `BK-100` "Python Basics" in books at 40.00 → the catalog accepts it, marks it tax exempt and lists it in a search for "python".

| ID | Rule | Source | Change via |
|---|---|---|---|
| CAT-01 | A SKU has 3 to 20 characters: uppercase letters, digits and hyphen. A product name has 1 to 80 characters after trimming. | src/market/features/catalog/product_validation.py::validate_product | code |
| CAT-02 | A price is above 0.00, has at most 2 decimals and is at most 100000.00. Setting: `catalog.max_price`. | src/market/features/catalog/product_validation.py::validate_product | config |
| CAT-03 | A category is one of books, electronics, fashion, grocery, home, toys, gift_card. Weight is 1 to 30000 g, except gift cards, which weigh 0. Books, grocery and gift cards are tax exempt, all others standard. Spans: catalog, tax. | src/market/features/catalog/product_validation.py::validate_product | code |
| CAT-04 | A SKU already in the catalog cannot be added again. | src/market/features/catalog/product_store.py::add_product | code |
| CAT-05 | A deactivated product cannot be put in a cart or bought, and it stays visible in past orders. Spans: catalog, cart, checkout. | src/market/features/catalog/product_store.py::require_sellable | code |
| CAT-06 | One price update may not change a price by more than 50%. Setting: `catalog.max_price_change_percent`. | src/market/features/catalog/product_validation.py::validate_price_change | config |
| CAT-07 | Search matches names or SKUs containing the text, ignoring case, only active products, sorted by name (or by price up or down), with an optional category and maximum price. | src/market/features/catalog/catalog_search.py::search_products | code |

Related rules in other sections: tax exemption in [TAX-02](10-tax.md); gift cards in [PRM-12](04-promotions.md), [PRC-05](03-pricing.md), [INV-07](05-inventory.md), [RET-02](12-returns.md); sellable products in [CRT-04](06-cart.md) and [CHK-01](07-checkout.md).
