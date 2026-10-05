# Evaluation report

Candidate LT versus base SK.

## Runs

| Arm and scenario | Found | Expected | Missing |
|---|---|---|---|
| SK.L1 | 0 | 2 | 2 |
| SK.L2 | 0 | 2 | 2 |
| SK.L3 | 0 | 2 | 2 |
| SK.L4 | 0 | 2 | 2 |
| SK.L5 | 0 | 2 | 2 |
| SK.L6 | 0 | 2 | 2 |
| SK.L7 | 0 | 2 | 2 |
| SK.L8 | 0 | 2 | 2 |
| LT.L1 | 2 | 2 | 0 |
| LT.L2 | 1 | 2 | 1 |
| LT.L3 | 0 | 2 | 2 |
| LT.L4 | 0 | 2 | 2 |
| LT.L5 | 0 | 2 | 2 |
| LT.L6 | 0 | 2 | 2 |
| LT.L7 | 0 | 2 | 2 |
| LT.L8 | 0 | 2 | 2 |

## Hard gates

- PASS: Q1 accept: LT mean at least SK (LT 1.0, SK None)
- PASS: Q2 suite_green: true in every LT run (3 of 3)
- PASS: Q3 gate_ok: true in every LT run (3 of 3)
- PASS: Q4 completed: true in every LT run (3 of 3)
- PASS: F1 prd_fidelity: LT at least SK minus 0.05 (LT 0.9523809523809524, SK None)
- PASS: R4 protocol_adherence: 1.0 in every LT run (3 of 3)

## Scorecard L1

| Metric | Group | LT | SK | Band | Verdict |
|---|---|---|---|---|---|
| tokens_total | tokens | n/a | n/a | n/a | n/a |
| context_peak | tokens | n/a | n/a | n/a | n/a |
| wall_min | speed | n/a | n/a | n/a | n/a |
| min_to_code | speed | n/a | n/a | n/a | n/a |
| turns | speed | n/a | n/a | n/a | n/a |
| cost_usd | efficiency | n/a | n/a | n/a | n/a |
| cost_per_accept | efficiency | n/a | n/a | n/a | n/a |
| doc_bytes | efficiency | n/a | n/a | n/a | n/a |
| rework_commits | rework | n/a | n/a | n/a | n/a |
| kit_self_fixes | rework | n/a | n/a | n/a | n/a |
| plan_coverage | plan_fidelity | n/a | n/a | n/a | n/a |
| plan_drift | plan_fidelity | n/a | n/a | n/a | n/a |
| traceability | source_fidelity | n/a | n/a | n/a | n/a |
| docs_first | source_fidelity | n/a | n/a | n/a | n/a |
| promoted | source_fidelity | n/a | n/a | n/a | n/a |
| single_source | source_fidelity | n/a | n/a | n/a | n/a |
| tool_errors | errors | n/a | n/a | n/a | n/a |
| error_rate | errors | n/a | n/a | n/a | n/a |
| subagent_tokens_median | subagents | n/a | n/a | n/a | n/a |
| subagent_errors | subagents | n/a | n/a | n/a | n/a |
| subagents_wasted | subagents | n/a | n/a | n/a | n/a |
| tasks_per_executor | subagents | n/a | n/a | n/a | n/a |
| review_rounds | reviews | n/a | n/a | n/a | n/a |
| review_fix_commits | reviews | n/a | n/a | n/a | n/a |
| blind_findings_total | reviews | n/a | n/a | n/a | n/a |
| blind_approve | reviews | n/a | n/a | n/a | n/a |
| accept | code_quality | n/a | n/a | n/a | n/a |
| suite_green | code_quality | n/a | n/a | n/a | n/a |
| blind_bugs | code_quality | n/a | n/a | n/a | n/a |
| blind_critical | code_quality | n/a | n/a | n/a | n/a |
| blind_high | code_quality | n/a | n/a | n/a | n/a |

## Scorecard L2

| Metric | Group | LT | SK | Band | Verdict |
|---|---|---|---|---|---|
| tokens_total | tokens | n/a | n/a | n/a | n/a |
| context_peak | tokens | n/a | n/a | n/a | n/a |
| wall_min | speed | n/a | n/a | n/a | n/a |
| min_to_code | speed | n/a | n/a | n/a | n/a |
| turns | speed | n/a | n/a | n/a | n/a |
| cost_usd | efficiency | n/a | n/a | n/a | n/a |
| cost_per_accept | efficiency | n/a | n/a | n/a | n/a |
| doc_bytes | efficiency | n/a | n/a | n/a | n/a |
| rework_commits | rework | n/a | n/a | n/a | n/a |
| kit_self_fixes | rework | n/a | n/a | n/a | n/a |
| plan_coverage | plan_fidelity | n/a | n/a | n/a | n/a |
| plan_drift | plan_fidelity | n/a | n/a | n/a | n/a |
| traceability | source_fidelity | n/a | n/a | n/a | n/a |
| docs_first | source_fidelity | n/a | n/a | n/a | n/a |
| promoted | source_fidelity | n/a | n/a | n/a | n/a |
| single_source | source_fidelity | n/a | n/a | n/a | n/a |
| tool_errors | errors | n/a | n/a | n/a | n/a |
| error_rate | errors | n/a | n/a | n/a | n/a |
| subagent_tokens_median | subagents | n/a | n/a | n/a | n/a |
| subagent_errors | subagents | n/a | n/a | n/a | n/a |
| subagents_wasted | subagents | n/a | n/a | n/a | n/a |
| tasks_per_executor | subagents | n/a | n/a | n/a | n/a |
| review_rounds | reviews | n/a | n/a | n/a | n/a |
| review_fix_commits | reviews | n/a | n/a | n/a | n/a |
| blind_findings_total | reviews | n/a | n/a | n/a | n/a |
| blind_approve | reviews | n/a | n/a | n/a | n/a |
| accept | code_quality | n/a | n/a | n/a | n/a |
| suite_green | code_quality | n/a | n/a | n/a | n/a |
| blind_bugs | code_quality | n/a | n/a | n/a | n/a |
| blind_critical | code_quality | n/a | n/a | n/a | n/a |
| blind_high | code_quality | n/a | n/a | n/a | n/a |

## Tally

| Group | Win | Tie | Loss |
|---|---|---|---|
| tokens | 0 | 0 | 0 |
| speed | 0 | 0 | 0 |
| efficiency | 0 | 0 | 0 |
| rework | 0 | 0 | 0 |
| plan_fidelity | 0 | 0 | 0 |
| source_fidelity | 0 | 0 | 0 |
| errors | 0 | 0 | 0 |
| subagents | 0 | 0 | 0 |
| reviews | 0 | 0 | 0 |
| code_quality | 0 | 0 | 0 |

## Adoption

- PASS: hard gates
- FAIL: E1, E2, E3 win or tie on S1 and S2 ({"S1.tokens_total": null, "S1.cost_usd": null, "S1.wall_min": null, "S2.tokens_total": null, "S2.cost_usd": null, "S2.wall_min": null})
- PASS: losses do not exceed wins in each group

Result: LT is not adopted.

29 run(s) are missing; medians use only the runs present.


## Efficiency analysis

Median per arm over the runs of the scope; `#n` is the rank of the arm on that metric (1 is best, none for descriptive metrics).

### X1 Token consumption

| Metric | Scope | LT | SKF | SKU |
|---|---|---|---|---|
| tokens_total | all | 9539759 #1 | 12097257 #2 | 12367459 #3 |
| tokens_total | M | 8586256.5 #1 | 11327723.5 #3 | 9987135 #2 |
| tokens_total | L | 9539759 #1 | 13920401 #2 | 22921585 #3 |
| tokens_main | all | 5703463 #1 | 10384658 #2 | 12302155 #3 |
| tokens_main | M | 6781586 #1 | 9738215.5 #2 | 9914454 #3 |
| tokens_main | L | 5703463 #1 | 12118332 #2 | 17525618 #3 |
| tokens_subagents | all | 1871450 #3 | 1435860 #2 | 0 #1 |
| tokens_subagents | M | 1585190 #3 | 1370243 #2 | 0 #1 |
| tokens_subagents | L | 3603000 #2 | 1565377 #1 | 4931190 #3 |
| context_peak | all | 165356 #1 | 198802 #3 | 191991 #2 |
| context_peak | M | 161117 #1 | 190105 #3 | 186929.5 #2 |
| context_peak | L | 165356 #1 | 211526 #2 | 248775 #3 |
| cost_usd | all | 7.98 #1 | 9.977 #2 | 10.059 #3 |
| cost_usd | M | 7.327 #1 | 9.546 #3 | 9.325 #2 |
| cost_usd | L | 7.98 #1 | 11.747 #2 | 17.481 #3 |

### X2 Efficiency of the subagents

| Metric | Scope | LT | SKF | SKU |
|---|---|---|---|---|
| subagents | all | 3 | 4 | 0 |
| subagents | M | 3.5 | 3.5 | 0 |
| subagents | L | 3 | 4 | 8 |
| subagent_tokens_median | all | 649465 #2 | 406523 #1 | 663219.5 #3 |
| subagent_tokens_median | M | 515017.5 #2 | 458209 #1 | n/a |
| subagent_tokens_median | L | 1196286 #3 | 406523 #1 | 663219.5 #2 |
| subagent_tool_calls_median | all | 20 #2 | 17 #1 | 25 #3 |
| subagent_tool_calls_median | M | 17.5 #2 | 15.25 #1 | n/a |
| subagent_tool_calls_median | L | 35 #3 | 17 #1 | 25 #2 |
| subagent_errors | all | 0 #1 | 1 #3 | 0 #1 |
| subagent_errors | M | 0 #1 | 1 #3 | 0 #1 |
| subagent_errors | L | 5 #2 | 1 #1 | 9 #3 |
| subagents_wasted | all | 0 #1 | 0 #1 | 0 #1 |
| subagents_wasted | M | 0 #1 | 0 #1 | 0 #1 |
| subagents_wasted | L | 0 #1 | 0 #1 | 0 #1 |
| tasks_per_executor | all | 1.75 #2 | 1.5 #3 | 3.5 #1 |
| tasks_per_executor | M | 1.75 #1 | 0.875 #2 | n/a |
| tasks_per_executor | L | n/a | 7 #1 | 3.5 #2 |
| subagent_token_share | all | 0.19 | 0.121 | 0 |
| subagent_token_share | M | 0.189 | 0.123 | 0 |
| subagent_token_share | L | 0.387 | 0.114 | 0.22 |

### X3 Error rate during implementation

| Metric | Scope | LT | SKF | SKU |
|---|---|---|---|---|
| tool_calls | all | 155 | 153 | 106 |
| tool_calls | M | 135 | 146 | 93.5 |
| tool_calls | L | 177 | 165 | 309 |
| tool_errors | all | 3 #1 | 4 #2 | 5 #3 |
| tool_errors | M | 3 #1 | 3.5 #2 | 4.5 #3 |
| tool_errors | L | 7 #2 | 4 #1 | 15 #3 |
| error_rate | all | 0.026 #2 | 0.024 #1 | 0.049 #3 |
| error_rate | M | 0.023 #1 | 0.024 #2 | 0.05 #3 |
| error_rate | L | 0.04 #2 | 0.024 #1 | 0.049 #3 |
| test_runs | all | 12 | 11 | 9 |
| test_runs | M | 15 | 10 | 8 |
| test_runs | L | 9 | 24 | 10 |
| failed_test_runs | all | 4 #3 | 1 #1 | 1 #1 |
| failed_test_runs | M | 4.5 #3 | 1 #1 | 1.5 #2 |
| failed_test_runs | L | 2 #2 | 3 #3 | 1 #1 |
| kit_self_fixes | all | 0 #1 | 0 #1 | 0 #1 |
| kit_self_fixes | M | 0 #1 | 0 #1 | 0 #1 |
| kit_self_fixes | L | 0 #1 | 0 #1 | 0 #1 |

### X4 Time to complete

| Metric | Scope | LT | SKF | SKU |
|---|---|---|---|---|
| wall_min | all | 18.475 #1 | 20.663 #3 | 18.65 #2 |
| wall_min | M | 16.931 #1 | 18.959 #3 | 17.379 #2 |
| wall_min | L | 18.475 #1 | 21.027 #2 | 33.591 #3 |
| min_to_code | all | 11.319 #1 | 11.605 #2 | 16.105 #3 |
| min_to_code | M | 10.438 #1 | 14.136 #2 | 14.143 #3 |
| min_to_code | L | 14.273 #2 | 11.328 #1 | 18.34 #3 |
| min_per_task | all | 6.613 #3 | 3.444 #2 | 3.442 #1 |
| min_per_task | M | 6.812 #3 | 4.598 #2 | 2.685 #1 |
| min_per_task | L | 6.158 #3 | 3.004 #1 | 4.199 #2 |

### X5 Reviews needed for good code

| Metric | Scope | LT | SKF | SKU |
|---|---|---|---|---|
| review_rounds | all | 2 #3 | 1 #2 | 0 #1 |
| review_rounds | M | 2 #3 | 1 #2 | 0 #1 |
| review_rounds | L | 2 #1 | 3 #3 | 2 #1 |
| review_fix_commits | all | 3 #3 | 1 #2 | 0 #1 |
| review_fix_commits | M | 3 #3 | 0.5 #2 | 0 #1 |
| review_fix_commits | L | 3 #1 | 4 #2 | 9 #3 |
| blind_findings_total | all | 1 #1 | 1 #1 | 1 #1 |
| blind_findings_total | M | 0.5 #1 | 1 #3 | 0.5 #1 |
| blind_findings_total | L | 3 #2 | 2 #1 | 3 #2 |

### X6 Code with fewest problems

| Metric | Scope | LT | SKF | SKU |
|---|---|---|---|---|
| accept | all | 1 #1 | 1 #1 | 1 #1 |
| accept | M | 1 #1 | 1 #1 | 1 #1 |
| accept | L | 1 #1 | 1 #1 | 1 #1 |
| suite_green | all | 1 #1 | 1 #1 | 1 #1 |
| suite_green | M | 1 #1 | 1 #1 | 1 #1 |
| suite_green | L | 1 #1 | 1 #1 | 1 #1 |
| blind_bugs | all | 0 #1 | 0 #1 | 0 #1 |
| blind_bugs | M | 0 #1 | 0 #1 | 0 #1 |
| blind_bugs | L | 0 #1 | 0 #1 | 0 #1 |
| blind_critical | all | 0 #1 | 0 #1 | 0 #1 |
| blind_critical | M | 0 #1 | 0 #1 | 0 #1 |
| blind_critical | L | 0 #1 | 0 #1 | 0 #1 |
| blind_high | all | 0 #1 | 0 #1 | 0 #1 |
| blind_high | M | 0 #1 | 0 #1 | 0 #1 |
| blind_high | L | 0 #1 | 0 #1 | 0 #1 |
| blind_medium | all | 1 #3 | 0 #1 | 0 #1 |
| blind_medium | M | 0.5 #3 | 0 #1 | 0 #1 |
| blind_medium | L | 2 #2 | 2 #2 | 1 #1 |
| blind_low | all | 0 #1 | 1 #2 | 1 #2 |
| blind_low | M | 0 #1 | 1 #3 | 0.5 #2 |
| blind_low | L | 1 #2 | 0 #1 | 2 #3 |
| blind_approve | all | 1 #1 | 1 #1 | 1 #1 |
| blind_approve | M | 1 #1 | 1 #1 | 1 #1 |
| blind_approve | L | 1 #1 | 1 #1 | 1 #1 |
