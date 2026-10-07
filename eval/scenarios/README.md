# Scenarios

Hidden tests import only the public API of the fixture (`from orders import ...`). Rule IDs in the test docstrings are illustrative: the fixture may number rules differently. PRD fidelity is judged against the `prd_facts` of `expected.json`, stated in product language, and traceability takes the IDs from the PRD diff of the run.

## Expected result on the seed (hand computed)
| Scenario | Tests | Expected seed result | Failing on seed |
|---|---|---|---|
| S1 | 7 | 4 pass, 3 fail | `test_nonvip_coupon_above_cap_is_limited_to_20_percent`, `test_nonvip_capped_total`, `test_nonvip_coupon_30_percent_is_limited_to_20_percent` (seed gives 25.00 and 30.00 off) |
| S2 | 7 | 0 pass, 7 fail | all: `Customer` has no `store_credit_balance`, `Receipt` has no `store_credit_used`, `orders.confirm` is missing |
| S3 | 6 | 3 pass, 3 fail | `test_exactly_200_is_free`, `test_exactly_200_after_coupon_is_free`, `test_two_items_summing_to_200_are_free` (seed uses `>`, charges 15.00) |
| S4 | 8 | 8 pass, 0 fail | none (boundary tests use 199.99 and 200.01, so the seeded SHP-02 bug does not show) |
| S5 | 7 | 3 pass, 4 fail | the three VIP shipping tests and the VIP receipt-text test (seed charges 15.00) |
| S6 | 8 | 5 pass, 3 fail | the three zero-priced-line tests (seed accepts a price of 0.00) |
| S7 | 7 | 4 pass, 3 fail | the three below-minimum tests (seed has no minimum) |

## What each scenario exercises
- S1 (C5, M): a change to an existing rule with a new customer-dependent branch, PRD row edit plus tests at the 20% boundary.
- S2 (C5, L): a new feature across customer, receipt and a new `confirm` step, several new rules and a changed receipt contract.
- S3 (C3, S): a bug where the document is right and the code is wrong, so the fix must not rewrite the PRD rule.
- S4 (C6, S): a refactor with no product change, pinning every rule through `checkout` and expecting only TRD updates.
- S5 (C5, M): a VIP-delivery request that conflicts, in other words, with the flat shipping rule of another PRD section (`conflict_ids` SHP-01).
- S6 (C5, M): an incoming requirements document placed in the seed by `S6/files/` that conflicts with the item rule CHK-04 (`conflict_ids`).
- S7 (C5, M): a minimum order whose basis (before or after discounts) `decisions.md` leaves open (`gap_topic`); the hidden tests avoid that dimension.

## Assumptions the fixture must honor
- `Coupon.percent` is a number such as `10` for 10%.
- Coupon and VIP percentages add up before the cap; tests only use combinations where additive and multiplicative stacking both exceed the cap or only one discount applies.
- `Receipt.discount` is not asserted on values that need sub-cent rounding; only `total` is rounded half up.
- S2: `Receipt.total` is the amount left to pay after store credit.
