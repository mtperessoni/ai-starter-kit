# Storefront PRD

## Overview

The storefront library keeps the customer record and builds the customer payload that the orders service receives with every checkout. There is one PRD, [storefront](storefront/01-summary.md), with one section: customers.

How to read: start at [INDEX.md](INDEX.md), open only the section a task touches. A rule is a row `| ID | Rule | Source | Change via |`; the ID is permanent.

How to change a rule: `/prd-gate`. The PRD changes first, then the TRD, then the code.

Principles that limit changes come from the constitution: documents are the source of truth, and the payload carries only what a rule names.

## What weighs most today

No open problems are recorded.

## Open decisions

None.
