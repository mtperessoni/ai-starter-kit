# Large scenarios

Eight scenarios for the large fixture (`eval/fixture-large/`, design in `eval/fixture-large/SPEC.md`). Same layout as the small suite in `eval/scenarios/`: `request.md` (product language, no rule IDs), `decisions.md` (answers to the interview), `expected.json` (`case`, `size`, `prd_facts`, `dup_phrases`) and `hidden/test_lN_hidden.py`.

Hidden tests import only `from market import api`, start with `api.reset(); api.seed_demo()` and compare money with `Decimal`. The rule IDs in docstrings come from the SPEC rule catalog and the L2 and L3 contracts (REV-01 to 05, ALR-01 to 05). The fixture keeps two seeded defects (SPEC section 6): a declined payment does not release the coupon use, and `PIPELINE` runs the bundle before the percent coupon. Only L4 and L5 touch those combinations; every other test avoids a decline with a limited coupon and a bundle together with a percent coupon.

## Expected result on the seed (hand computed)
| Scenario | Tests | Expected seed result | Failing on seed |
|---|---|---|---|
| L1 | 8 | 4 pass, 4 fail | failing: quote fee, quote tax and quote total with points, and the placed order (seed gives fee 0.00, tax 16.00, total 211.00); passing: loyalty discount of 5.00, control without points, VIP free shipping, large cart free shipping |
| L2 | 10 | 0 pass, 10 fail | all, `AttributeError` (`submit_review`, `list_reviews`, `average_rating` do not exist) |
| L3 | 10 | 0 pass, 10 fail | all, `AttributeError` (`subscribe_stock_alert`, `list_stock_alerts` do not exist) |
| L4 | 6 | 4 pass, 2 fail | `test_retry_with_same_coupon_after_decline_is_paid` and `test_two_declines_then_success_is_paid` (`ValidationError`, CHK-10); decline state, no-coupon retry, cancel and used-up tests pass |
| L5 | 8 | 4 pass, 4 fail | failing: 25.00 discount, 75.00 total, the two-set cart (seed 47.00) and the SAVE20 cart (seed 32.00); passing: both discounts listed, the three controls (bundle alone 15.00, SAVE10 alone 20.00, bundle with FIX15 30.00) |
| L6 | 4 functions (15 cases) | 13 pass, 2 fail | characterization (12 carts) passes and the importability test passes; the two line-count tests fail (engine is about 700 lines) |
| L7 | 6 | 5 pass, 1 fail | `test_vip_return_at_45_days_completes` (seed refuses at 30 days) |
| L8 | 6 | 0 pass, 6 fail | seed earns 120 on a first order, so every balance assertion differs (240, 360, 480, 216, 1240, and the retry after a decline) |

Note: L6 has 4 test functions; the characterization one is parametrized over 12 carts (none with a bundle plus a percent coupon), so pytest reports 15 cases. L2 and L3 fail on the seed only because the new functions do not exist yet.

## What each scenario exercises
- L1 (C5, M): a cross-feature rule change (shipping threshold, checkout order of steps, loyalty redemption), PRD rows in three sections kept consistent.
- L2 (C5, L): a new feature `reviews` with data model, five new rules, a new PRD section, TRD file and feature CLAUDE.md, names fixed by the SPEC.
- L3 (C5, L): a new feature `stock_alerts` that listens to the restocked event and adds a notification template, so it crosses inventory and notifications.
- L4 (C3, S): a bug across checkout, promotions and payments where the document is right and the code is wrong.
- L5 (C3, S): a bug inside the 700-line promotion engine that must be found by symbol, with no rule edit.
- L6 (C6, M): a refactor of the big file, TRD only (map, invariants, folder CLAUDE.md, big-file lists), PRD untouched.
- L7 (C5, M): a rule gap in the return window, a new config key and a PRD row edit with a changelog entry.
- L8 (C2, S): implement the approved `planned` rule LOY-07 and move its Source from `planned` to real code.
