# Orders PRD

## Overview

The orders service prices a cart and closes it into a receipt. It is a small Python library called by the storefront; there is one PRD, [orders](orders/01-summary.md), with one section per step: pricing, shipping and checkout.

How to read: start at [INDEX.md](INDEX.md), open only the section a task touches. A rule is a row `| ID | Rule | Source | Change via |`; the ID is permanent.

How to change a rule: `/prd-gate`. The PRD changes first, then the TRD, then the code.

Principles that limit changes come from the constitution: documents are the source of truth, and money is exact.

## What weighs most today

No open problems are recorded.

## Open decisions

None.
