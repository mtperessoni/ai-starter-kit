# Evaluation report

## Scenario S1

| Metric | A | B | Delta |
|---|---|---|---|
| status | ok | ok |  |
| completed | yes | yes |  |
| hidden_pass | 1 | 1 | 0 |
| suite_green | yes | yes |  |
| gate_ok | yes | yes |  |
| prd_ok | no | no |  |
| ids_in_tests | 1 | 1 | 0 |
| docs_first | yes | yes |  |
| planned_left | 0 | 0 | 0 |
| dup_count | 0 | 0 | 0 |
| fr_lines | 0 | 0 | 0 |
| cost_usd | 3.077 | 2.661 | -0.416 |
| duration_min | 6.789 | 6.027 | -0.762 |
| turns | 52 | 43 | -9 |
| tokens_total | 2653619 | 2520685 | -132934 |
| doc_bytes | 556 | 724 | 168 |

## Scenario S2

| Metric | A | B | Delta |
|---|---|---|---|
| status | ok | grade_failed |  |
| completed | yes | n/a |  |
| hidden_pass | 1 | n/a |  |
| suite_green | yes | n/a |  |
| gate_ok | yes | n/a |  |
| prd_ok | yes | n/a |  |
| ids_in_tests | 0.4 | n/a |  |
| docs_first | no | n/a |  |
| planned_left | 0 | n/a |  |
| dup_count | 0 | n/a |  |
| fr_lines | 0 | n/a |  |
| cost_usd | 6.877 | n/a |  |
| duration_min | 10.905 | n/a |  |
| turns | 79 | n/a |  |
| tokens_total | 7020333 | n/a |  |
| doc_bytes | 7843 | n/a |  |

## Scenario S3

| Metric | A | B | Delta |
|---|---|---|---|
| status | ok | ok |  |
| completed | yes | yes |  |
| hidden_pass | 1 | 1 | 0 |
| suite_green | yes | yes |  |
| gate_ok | yes | yes |  |
| prd_ok | yes | yes |  |
| ids_in_tests | 1 | 1 | 0 |
| docs_first | n/a | n/a |  |
| planned_left | 0 | 0 | 0 |
| dup_count | 0 | 0 | 0 |
| fr_lines | 0 | 0 | 0 |
| cost_usd | 1.174 | 1.117 | -0.057 |
| duration_min | 1.766 | 1.796 | 0.03 |
| turns | 24 | 23 | -1 |
| tokens_total | 961980 | 842141 | -119839 |
| doc_bytes | 0 | 0 | 0 |

## Scenario S4

| Metric | A | B | Delta |
|---|---|---|---|
| status | ok | ok |  |
| completed | yes | yes |  |
| hidden_pass | 1 | 1 | 0 |
| suite_green | yes | yes |  |
| gate_ok | yes | yes |  |
| prd_ok | yes | yes |  |
| ids_in_tests | 1 | 1 | 0 |
| docs_first | n/a | n/a |  |
| planned_left | 0 | 0 | 0 |
| dup_count | 0 | 0 | 0 |
| fr_lines | 0 | 0 | 0 |
| cost_usd | 2.811 | 2.537 | -0.274 |
| duration_min | 6.315 | 6.119 | -0.196 |
| turns | 41 | 37 | -4 |
| tokens_total | 2377576 | 2168862 | -208714 |
| doc_bytes | 681 | 4302 | 3621 |

## Totals

| Metric | A | B | Delta |
|---|---|---|---|
| runs | 4 | 4 | 0 |
| completed | 4 | 3 | -1 |
| hidden_pass | 1 | 1 | 0 |
| prd_ok | 3 | 2 | -1 |
| gate_ok | 4 | 3 | -1 |
| planned_left | 0 | 0 | 0 |
| dup_count | 0 | 0 | 0 |
| fr_lines | 0 | 0 | 0 |
| cost_usd | 13.94 | 6.315 | -7.625 |
| duration_min | 25.775 | 13.942 | -11.833 |
| turns | 196 | 103 | -93 |
| tokens_total | 13013508 | 5531688 | -7481820 |
| doc_bytes | 9080 | 5026 | -4054 |

## Decision rule

- PASS: hidden_pass of B is not lower than A (A 1.000, B 1.000)
- FAIL: prd_ok of B is not lower than A (A 3, B 2)
- FAIL: gate_ok holds in every B run (3 of 4)
- PASS: dup_count of B is not higher than A (A 0, B 0)
- PASS: cost_usd of B is at most 10% above A (A 13.94, B 6.31)
- PASS: duration_min of B is at most 10% above A (A 25.8, B 13.9)

Result: B is not adopted on this run.

Within 10% of each other, rerun before deciding: S3 (cost_usd), S3 (duration_min), S4 (cost_usd), S4 (duration_min).

Caveat: one repetition per pair gives the direction only, not a verdict.
