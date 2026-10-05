# Market PRD

## Overview

The market service is a small in-memory Python library for a marketplace: catalog, cart, pricing and promotions, checkout with shipping and tax, payments, loyalty, returns and notifications. There is one PRD, [market](market/01-summary.md), with one section per feature (12 sections, 89 rules).

How to read: start at [INDEX.md](INDEX.md), open only the section a task touches. A rule is a row `| ID | Rule | Source | Change via |`; the ID is permanent. A rule that spans features says "Spans" in its text; the pairs are listed in [the summary](market/01-summary.md).

How to change a rule: `/prd-gate`. The PRD changes first, then the TRD, then the code.

Principles that limit changes come from the constitution: documents are the source of truth, and money is exact.

## What weighs most today

| Item | Note |
|---|---|
| Planned rule | LOY-07 is approved and not built (Source `planned`) |
| Big file | `promotions/promotion_engine.py` is read by symbol, see [the promotions TRD](../trd/promotions.md) |

## Open decisions

None.
