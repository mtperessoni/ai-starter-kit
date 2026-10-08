# Evaluation report

Candidate FLOW versus base GATE.

## Runs

| Arm and scenario | Found | Expected | Missing |
|---|---|---|---|
| GATE.S5 | 1 | 1 | 0 |
| GATE.S6 | 1 | 1 | 0 |
| GATE.S7 | 1 | 1 | 0 |
| FLOW.S5 | 1 | 1 | 0 |
| FLOW.S6 | 1 | 1 | 0 |
| FLOW.S7 | 1 | 1 | 0 |

## Hard gates

- PASS: Q1 accept: FLOW mean at least GATE (FLOW 1.0, GATE 0.8571428571428571)
- PASS: Q2 suite_green: true in every FLOW run (3 of 3)
- PASS: Q3 gate_ok: true in every FLOW run (3 of 3)
- PASS: Q4 completed: true in every FLOW run (3 of 3)
- FAIL: F1 prd_fidelity: FLOW at least GATE minus 0.05 (FLOW 0.75, GATE 0.8611111111111112)
- PASS: R4 protocol_adherence: 1.0 in every FLOW run (3 of 3)

## Scorecard S5

| Metric | Group | FLOW | GATE | Band | Verdict |
|---|---|---|---|---|---|
| tokens_total | tokens | 10170899 | 6150983 | 615098.3 | loss |
| context_peak | tokens | 154894 | 107116 | 10711.6 | loss |
| wall_min | speed | 25.052 | 19.059 | 1.906 | loss |
| min_to_code | speed | 19.763 | 11.35 | 1.135 | loss |
| turns | speed | 82 | 51 | 5.1 | loss |
| cost_usd | efficiency | 8.104 | 5.47 | 0.547 | loss |
| cost_per_accept | efficiency | 1.158 | 0.781 | 0.078 | loss |
| doc_bytes | efficiency | 6856 | 8996 | 899.6 | win |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | 1 | 1 | 0.1 | tie |
| plan_drift | plan_fidelity | 0 | 0 | 0 | tie |
| traceability | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| docs_first | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| promoted | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| single_source | Source-of-truth fidelity | 13 | 14 | 1.4 | tie |
| conflict_found | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| contradiction_left | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| gap_recorded | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| tool_errors | errors | 2 | 6 | 0.6 | win |
| error_rate | errors | 0.022 | 0.035 | 0.003 | win |
| subagent_tokens_median | subagents | 23291 | 523346.5 | 52334.65 | win |
| subagent_errors | subagents | 0 | 6 | 0.6 | win |
| subagents_wasted | subagents | 2 | 0 | 0 | loss |
| tasks_per_executor | subagents | 0.5 | 0.6 | 0.06 | loss |
| review_rounds | reviews | 2 | 1 | 0.1 | loss |
| review_fix_commits | reviews | 2 | 2 | 0.2 | tie |
| blind_findings_total | reviews | 0 | 1 | 0.1 | win |
| blind_approve | reviews | 1 | 0 | 0 | win |
| accept | code_quality | 1 | 1 | 0.1 | tie |
| suite_green | code_quality | 1 | 1 | 0.1 | tie |
| blind_bugs | code_quality | 0 | 1 | 0.1 | win |
| blind_critical | code_quality | 0 | 0 | 0 | tie |
| blind_high | code_quality | 0 | 1 | 0.1 | win |

## Scorecard S6

| Metric | Group | FLOW | GATE | Band | Verdict |
|---|---|---|---|---|---|
| tokens_total | tokens | 5256061 | 3092668 | 309266.8 | loss |
| context_peak | tokens | 108947 | 87940 | 8794 | loss |
| wall_min | speed | 14.108 | 5.787 | 0.579 | loss |
| min_to_code | speed | 12.197 | 4.734 | 0.473 | loss |
| turns | speed | 48 | 44 | 4.4 | tie |
| cost_usd | efficiency | 4.419 | 3.256 | 0.326 | loss |
| cost_per_accept | efficiency | 0.552 | 0.407 | 0.041 | loss |
| doc_bytes | efficiency | 6523 | 2489 | 248.9 | loss |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | n/a | n/a | n/a | n/a |
| plan_drift | plan_fidelity | n/a | n/a | n/a | n/a |
| traceability | Source-of-truth fidelity | 0.25 | 1 | 0.1 | loss |
| docs_first | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| promoted | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| single_source | Source-of-truth fidelity | 12 | 5 | 0.5 | loss |
| conflict_found | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| contradiction_left | Source-of-truth fidelity | 0 | 0 | 0 | tie |
| gap_recorded | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| tool_errors | errors | 4 | 0 | 0 | loss |
| error_rate | errors | 0.035 | 0 | 0 | loss |
| subagent_tokens_median | subagents | 669948 | 254777 | 25477.7 | loss |
| subagent_errors | subagents | 3 | 0 | 0 | loss |
| subagents_wasted | subagents | 0 | 0 | 0 | tie |
| tasks_per_executor | subagents | n/a | n/a | n/a | n/a |
| review_rounds | reviews | 0 | 1 | 0.1 | win |
| review_fix_commits | reviews | 0 | 0 | 0 | tie |
| blind_findings_total | reviews | 1 | 0 | 0 | loss |
| blind_approve | reviews | 1 | 1 | 0.1 | tie |
| accept | code_quality | 1 | 1 | 0.1 | tie |
| suite_green | code_quality | 1 | 1 | 0.1 | tie |
| blind_bugs | code_quality | 0 | 0 | 0 | tie |
| blind_critical | code_quality | 0 | 0 | 0 | tie |
| blind_high | code_quality | 0 | 0 | 0 | tie |

## Scorecard S7

| Metric | Group | FLOW | GATE | Band | Verdict |
|---|---|---|---|---|---|
| tokens_total | tokens | 8004137 | 2059942 | 205994.2 | loss |
| context_peak | tokens | 145016 | 99299 | 9929.9 | loss |
| wall_min | speed | 17.676 | 7.761 | 0.776 | loss |
| min_to_code | speed | n/a | n/a | n/a | n/a |
| turns | speed | 74 | 35 | 3.5 | loss |
| cost_usd | efficiency | 7.108 | 2.801 | 0.28 | loss |
| cost_per_accept | efficiency | 1.015 | 0.7 | 0.07 | loss |
| doc_bytes | efficiency | 9584 | 5338 | 533.8 | loss |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | 1 | 0 | 0 | win |
| plan_drift | plan_fidelity | n/a | n/a | n/a | n/a |
| traceability | Source-of-truth fidelity | 1 | 0 | 0 | win |
| docs_first | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| promoted | Source-of-truth fidelity | 1 | 0 | 0 | win |
| single_source | Source-of-truth fidelity | 8 | 4 | 0.4 | loss |
| conflict_found | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| contradiction_left | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| gap_recorded | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| tool_errors | errors | 1 | 2 | 0.2 | win |
| error_rate | errors | 0.009 | 0.061 | 0.006 | win |
| subagent_tokens_median | subagents | n/a | n/a | n/a | n/a |
| subagent_errors | subagents | 1 | 0 | 0 | loss |
| subagents_wasted | subagents | 0 | 0 | 0 | tie |
| tasks_per_executor | subagents | n/a | n/a | n/a | n/a |
| review_rounds | reviews | 2 | 0 | 0 | loss |
| review_fix_commits | reviews | 2 | 0 | 0 | loss |
| blind_findings_total | reviews | 1 | 0 | 0 | loss |
| blind_approve | reviews | 1 | 1 | 0.1 | tie |
| accept | code_quality | 1 | 0.571 | 0.057 | win |
| suite_green | code_quality | 1 | 1 | 0.1 | tie |
| blind_bugs | code_quality | 0 | 0 | 0 | tie |
| blind_critical | code_quality | 0 | 0 | 0 | tie |
| blind_high | code_quality | 0 | 0 | 0 | tie |

## Tally

| Group | Win | Tie | Loss |
|---|---|---|---|
| tokens | 0 | 0 | 6 |
| speed | 0 | 1 | 7 |
| efficiency | 1 | 0 | 8 |
| rework | 0 | 6 | 0 |
| plan_fidelity | 1 | 2 | 0 |
| Source-of-truth fidelity | 2 | 12 | 3 |
| errors | 4 | 0 | 2 |
| subagents | 2 | 2 | 5 |
| reviews | 3 | 4 | 5 |
| code_quality | 3 | 12 | 0 |

## Adoption

- FAIL: hard gates
- FAIL: E1, E2, E3 win or tie on S1 and S2 ({"S1.tokens_total": null, "S1.cost_usd": null, "S1.wall_min": null, "S2.tokens_total": null, "S2.cost_usd": null, "S2.wall_min": null})
- FAIL: losses do not exceed wins in each group

Result: FLOW is not adopted.

## Work list

- S5 tokens_total (tokens): FLOW 10170899, GATE 6150983
- S5 context_peak (tokens): FLOW 154894, GATE 107116
- S5 wall_min (speed): FLOW 25.052, GATE 19.059
- S5 min_to_code (speed): FLOW 19.763, GATE 11.35
- S5 turns (speed): FLOW 82, GATE 51
- S5 cost_usd (efficiency): FLOW 8.104, GATE 5.47
- S5 cost_per_accept (efficiency): FLOW 1.158, GATE 0.781
- S5 subagents_wasted (subagents): FLOW 2, GATE 0
- S5 tasks_per_executor (subagents): FLOW 0.5, GATE 0.6
- S5 review_rounds (reviews): FLOW 2, GATE 1
- S6 tokens_total (tokens): FLOW 5256061, GATE 3092668
- S6 context_peak (tokens): FLOW 108947, GATE 87940
- S6 wall_min (speed): FLOW 14.108, GATE 5.787
- S6 min_to_code (speed): FLOW 12.197, GATE 4.734
- S6 cost_usd (efficiency): FLOW 4.419, GATE 3.256
- S6 cost_per_accept (efficiency): FLOW 0.552, GATE 0.407
- S6 doc_bytes (efficiency): FLOW 6523, GATE 2489
- S6 traceability (source_fidelity): FLOW 0.25, GATE 1
- S6 single_source (source_fidelity): FLOW 12, GATE 5
- S6 tool_errors (errors): FLOW 4, GATE 0
- S6 error_rate (errors): FLOW 0.035, GATE 0
- S6 subagent_tokens_median (subagents): FLOW 669948, GATE 254777
- S6 subagent_errors (subagents): FLOW 3, GATE 0
- S6 blind_findings_total (reviews): FLOW 1, GATE 0
- S7 tokens_total (tokens): FLOW 8004137, GATE 2059942
- S7 context_peak (tokens): FLOW 145016, GATE 99299
- S7 wall_min (speed): FLOW 17.676, GATE 7.761
- S7 turns (speed): FLOW 74, GATE 35
- S7 cost_usd (efficiency): FLOW 7.108, GATE 2.801
- S7 cost_per_accept (efficiency): FLOW 1.015, GATE 0.7
- S7 doc_bytes (efficiency): FLOW 9584, GATE 5338
- S7 single_source (source_fidelity): FLOW 8, GATE 4
- S7 subagent_errors (subagents): FLOW 1, GATE 0
- S7 review_rounds (reviews): FLOW 2, GATE 0
- S7 review_fix_commits (reviews): FLOW 2, GATE 0
- S7 blind_findings_total (reviews): FLOW 1, GATE 0


## Efficiency analysis

Median per arm over the runs of the scope; `#n` is the rank of the arm on that metric (1 is best, none for descriptive metrics).

### X1 Token consumption

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| tokens_total | all | 8004137 #2 | 3092668 #1 |
| tokens_total | M | 8004137 #2 | 3092668 #1 |
| tokens_main | all | 6759062 #2 | 2560166 #1 |
| tokens_main | M | 6759062 #2 | 2560166 #1 |
| tokens_subagents | all | 1065376 #2 | 254777 #1 |
| tokens_subagents | M | 1065376 #2 | 254777 #1 |
| context_peak | all | 145016 #2 | 99299 #1 |
| context_peak | M | 145016 #2 | 99299 #1 |
| cost_usd | all | 7.108 #2 | 3.256 #1 |
| cost_usd | M | 7.108 #2 | 3.256 #1 |

### X2 Efficiency of the subagents

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| subagents | all | 3 | 1 |
| subagents | M | 3 | 1 |
| subagent_tokens_median | all | 196429 #1 | 389061.75 #2 |
| subagent_tokens_median | M | 196429 #1 | 389061.75 #2 |
| subagent_tool_calls_median | all | 12 #1 | 14.75 #2 |
| subagent_tool_calls_median | M | 12 #1 | 14.75 #2 |
| subagent_errors | all | 1 #2 | 0 #1 |
| subagent_errors | M | 1 #2 | 0 #1 |
| subagents_wasted | all | 0 #1 | 0 #1 |
| subagents_wasted | M | 0 #1 | 0 #1 |
| tasks_per_executor | all | 0.5 #2 | 0.6 #1 |
| tasks_per_executor | M | 0.5 #2 | 0.6 #1 |
| subagent_token_share | all | 0.136 | 0.084 |
| subagent_token_share | M | 0.136 | 0.084 |

### X3 Error rate during implementation

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| tool_calls | all | 113 | 52 |
| tool_calls | M | 113 | 52 |
| tool_errors | all | 2 #1 | 2 #1 |
| tool_errors | M | 2 #1 | 2 #1 |
| error_rate | all | 0.022 #1 | 0.035 #2 |
| error_rate | M | 0.022 #1 | 0.035 #2 |
| test_runs | all | 11 | 9 |
| test_runs | M | 11 | 9 |
| failed_test_runs | all | 1 #2 | 0 #1 |
| failed_test_runs | M | 1 #2 | 0 #1 |
| kit_self_fixes | all | 0 #1 | 0 #1 |
| kit_self_fixes | M | 0 #1 | 0 #1 |

### X4 Time to complete

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| wall_min | all | 17.676 #2 | 7.761 #1 |
| wall_min | M | 17.676 #2 | 7.761 #1 |
| min_to_code | all | 12.313 #2 | 8.042 #1 |
| min_to_code | M | 12.313 #2 | 8.042 #1 |
| min_per_task | all | 14.108 #2 | 7.057 #1 |
| min_per_task | M | 14.108 #2 | 7.057 #1 |

### X5 Reviews needed for good code

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| review_rounds | all | 2 #2 | 1 #1 |
| review_rounds | M | 2 #2 | 1 #1 |
| review_fix_commits | all | 2 #2 | 0 #1 |
| review_fix_commits | M | 2 #2 | 0 #1 |
| blind_findings_total | all | 1 #2 | 0 #1 |
| blind_findings_total | M | 1 #2 | 0 #1 |

### X6 Code with fewest problems

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| accept | all | 1 #1 | 1 #1 |
| accept | M | 1 #1 | 1 #1 |
| suite_green | all | 1 #1 | 1 #1 |
| suite_green | M | 1 #1 | 1 #1 |
| blind_bugs | all | 0 #1 | 0 #1 |
| blind_bugs | M | 0 #1 | 0 #1 |
| blind_critical | all | 0 #1 | 0 #1 |
| blind_critical | M | 0 #1 | 0 #1 |
| blind_high | all | 0 #1 | 0 #1 |
| blind_high | M | 0 #1 | 0 #1 |
| blind_medium | all | 1 #2 | 0 #1 |
| blind_medium | M | 1 #2 | 0 #1 |
| blind_low | all | 0 #1 | 0 #1 |
| blind_low | M | 0 #1 | 0 #1 |
| blind_approve | all | 1 #1 | 1 #1 |
| blind_approve | M | 1 #1 | 1 #1 |
