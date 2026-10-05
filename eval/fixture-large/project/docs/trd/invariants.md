# Invariants · TRD

What a code change must not break, by kind of change. Sources: `AGENTS.md` "Critical constraints", the constitution and the structural tests, cited by file name. The full rule is in the source; here, one line. IDs are stable: a new rule goes at the end of its table with the next free number.

## Any change

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-01 | No em dash (U+2014) in code, docs, prompts or commits | AGENTS.md; prd-gate gate G4 |
| I-02 | Zero comments, except the non-obvious and critical why; no comment cites a ticket | AGENTS.md |
| I-03 | Failing test before the implementation | Constitution, test-first principle |
| I-04 | `python -m pytest -q` is green | CI |
| I-05 | The feature's `CLAUDE.md` and TRD change in the same commit as the code they map | `docs/code-structure.md` AR07, AR13 |

## Money

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-06 | Money is `Decimal` built from strings, never `float`; output money has exactly 2 decimals | Constitution, exact money principle; `src/market/infra/tests/test_money.py` |
| I-07 | `q2` rounds only where a rule says so (PRC-03, PRC-04, PRM-02, PRM-07..10, TAX-03, TAX-04, SHP-05, PAY-02, RET-03) and nowhere else | `src/market/infra/tests/test_money.py` |
| I-08 | `allocate` pieces sum exactly to the amount (PRC-04) | `src/market/infra/tests/test_money.py` |

## Structure

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-09 | Core (catalog, pricing, promotions, inventory, cart, checkout, payments, shipping, tax) never imports peripheral (loyalty, returns, notifications); checkout reaches loyalty only through `checkout/ports.py` | Review; `docs/code-structure.md` |
| I-10 | A feature imports another only through the package modules named in its TRD, never its tests; no cycles | Review; `docs/code-structure.md` |
| I-11 | Every `features/<f>/` and `infra/` `__init__.py` is at most 10 lines: re-exports only; only loyalty and notifications call `register()` | Review |
| I-12 | The big file `promotions/promotion_engine.py` is read by symbol; it is pure and writes to no repository | `src/market/features/promotions/tests/test_promotion_engine.py` |

## Flow

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-13 | `PIPELINE` order is category sale, buy-x-get-y, percent coupon, bundle, fixed coupon, free shipping (PRM-05) | `src/market/features/promotions/tests/test_promotion_engine.py` |
| I-14 | The placement sequence of CHK-02 is kept; a decline returns the order and releases both the stock hold and the coupon uses (CHK-06) | `src/market/features/checkout/tests/test_order_placement.py` |
| I-15 | Events keep their names and payload keys ([infra](infra.md)) | `src/market/infra/tests/test_events.py` |
| I-16 | A decline never raises; any other failure raises the `MarketError` subclass of its rule | `src/market/features/payments/tests/test_payment_service.py`, `src/market/tests/test_api.py` |

## Public API

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-17 | `from market import api` keeps working with the same function names and signatures; importing it registers the loyalty and notifications handlers and the loyalty port | `src/market/tests/test_api.py` |

## Tests

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-18 | Tests cite the PRD ID they prove; the mirror test of a module is `tests/test_<module>.py` | `docs/code-structure.md` AR06 |
| I-19 | The suite touches no network and no database; the clock and ids are injected | Nothing in the code uses either |
