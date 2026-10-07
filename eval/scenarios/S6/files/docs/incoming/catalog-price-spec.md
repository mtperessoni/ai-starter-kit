# Catalog price integrity: requirements from the catalog team

Status: approved by the catalog team, waiting for the order service.

## Why

Items with no price keep reaching checkout when a catalog import fails halfway. The storefront then shows a receipt for goods that were never meant to be sold, and support has to refund them.

## Requirements

1. A line whose unit price is nothing at all (0.00) is not a sellable line. Checkout must refuse the whole order with a ValueError, the same kind of error it raises today for an invalid line.
2. A line priced at any amount above zero, down to 0.01, is accepted exactly as today.
3. A negative price, a quantity below 1 and an empty cart keep being refused as today. Nothing else about validation changes.
4. The order is refused as a whole: a cart that mixes valid lines with one unpriced line is refused, with no partial receipt.

## Out of scope

Shipping, discounts, rounding and the receipt layout do not change.
