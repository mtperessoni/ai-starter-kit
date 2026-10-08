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
- PASS: F1 prd_fidelity: FLOW at least GATE minus 0.05 (FLOW 0.9166666666666666, GATE 0.8611111111111112)
- PASS: R4 protocol_adherence: 1.0 in every FLOW run (3 of 3)

## Scorecard S5

| Metric | Group | FLOW | GATE | Band | Verdict |
|---|---|---|---|---|---|
| tokens_total | tokens | 7725651 | 6150983 | 615098.3 | loss |
| context_peak | tokens | 108615 | 107116 | 10711.6 | tie |
| wall_min | speed | 22.733 | 19.059 | 1.906 | loss |
| min_to_code | speed | 14.259 | 11.35 | 1.135 | loss |
| turns | speed | 54 | 51 | 5.1 | tie |
| cost_usd | efficiency | 5.791 | 5.47 | 0.547 | tie |
| cost_per_accept | efficiency | 0.827 | 0.781 | 0.078 | tie |
| doc_bytes | efficiency | 9013 | 8996 | 899.6 | tie |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | 1 | 1 | 0.1 | tie |
| plan_drift | plan_fidelity | 0 | 0 | 0 | tie |
| traceability | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| docs_first | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| promoted | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| single_source | Source-of-truth fidelity | 9 | 14 | 1.4 | win |
| conflict_found | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| contradiction_left | Source-of-truth fidelity | 0 | 1 | 0.1 | win |
| gap_recorded | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| tool_errors | errors | 8 | 6 | 0.6 | loss |
| error_rate | errors | 0.04 | 0.035 | 0.003 | loss |
| subagent_tokens_median | subagents | 524563 | 523346.5 | 52334.65 | tie |
| subagent_errors | subagents | 7 | 6 | 0.6 | loss |
| subagents_wasted | subagents | 0 | 0 | 0 | tie |
| tasks_per_executor | subagents | 0.5 | 0.6 | 0.06 | loss |
| review_rounds | reviews | 0 | 1 | 0.1 | win |
| review_fix_commits | reviews | 0 | 2 | 0.2 | win |
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
| tokens_total | tokens | 7874549 | 3092668 | 309266.8 | loss |
| context_peak | tokens | 109662 | 87940 | 8794 | loss |
| wall_min | speed | 21.678 | 5.787 | 0.579 | loss |
| min_to_code | speed | 15.975 | 4.734 | 0.473 | loss |
| turns | speed | 52 | 44 | 4.4 | loss |
| cost_usd | efficiency | 5.95 | 3.256 | 0.326 | loss |
| cost_per_accept | efficiency | 0.744 | 0.407 | 0.041 | loss |
| doc_bytes | efficiency | 6230 | 2489 | 248.9 | loss |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | n/a | n/a | n/a | n/a |
| plan_drift | plan_fidelity | n/a | n/a | n/a | n/a |
| traceability | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| docs_first | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| promoted | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| single_source | Source-of-truth fidelity | 4 | 5 | 0.5 | win |
| conflict_found | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| contradiction_left | Source-of-truth fidelity | 0 | 0 | 0 | tie |
| gap_recorded | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| tool_errors | errors | 8 | 0 | 0 | loss |
| error_rate | errors | 0.044 | 0 | 0 | loss |
| subagent_tokens_median | subagents | 477740 | 254777 | 25477.7 | loss |
| subagent_errors | subagents | 8 | 0 | 0 | loss |
| subagents_wasted | subagents | 0 | 0 | 0 | tie |
| tasks_per_executor | subagents | n/a | n/a | n/a | n/a |
| review_rounds | reviews | 1 | 1 | 0.1 | tie |
| review_fix_commits | reviews | 2 | 0 | 0 | loss |
| blind_findings_total | reviews | 0 | 0 | 0 | tie |
| blind_approve | reviews | 1 | 1 | 0.1 | tie |
| accept | code_quality | 1 | 1 | 0.1 | tie |
| suite_green | code_quality | 1 | 1 | 0.1 | tie |
| blind_bugs | code_quality | 0 | 0 | 0 | tie |
| blind_critical | code_quality | 0 | 0 | 0 | tie |
| blind_high | code_quality | 0 | 0 | 0 | tie |

## Scorecard S7

| Metric | Group | FLOW | GATE | Band | Verdict |
|---|---|---|---|---|---|
| tokens_total | tokens | 7113326 | 2059942 | 205994.2 | loss |
| context_peak | tokens | 97237 | 99299 | 9929.9 | tie |
| wall_min | speed | 20.771 | 7.761 | 0.776 | loss |
| min_to_code | speed | n/a | n/a | n/a | n/a |
| turns | speed | 35 | 35 | 3.5 | tie |
| cost_usd | efficiency | 5.426 | 2.801 | 0.28 | loss |
| cost_per_accept | efficiency | 0.775 | 0.7 | 0.07 | loss |
| doc_bytes | efficiency | 11488 | 5338 | 533.8 | loss |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | n/a | n/a | n/a | n/a |
| plan_drift | plan_fidelity | n/a | n/a | n/a | n/a |
| traceability | Source-of-truth fidelity | 0.5 | 0 | 0 | win |
| docs_first | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| promoted | Source-of-truth fidelity | 0 | 0 | 0 | tie |
| single_source | Source-of-truth fidelity | 13 | 4 | 0.4 | loss |
| conflict_found | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| contradiction_left | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| gap_recorded | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| tool_errors | errors | 6 | 2 | 0.2 | loss |
| error_rate | errors | 0.032 | 0.061 | 0.006 | win |
| subagent_tokens_median | subagents | n/a | n/a | n/a | n/a |
| subagent_errors | subagents | 6 | 0 | 0 | loss |
| subagents_wasted | subagents | 0 | 0 | 0 | tie |
| tasks_per_executor | subagents | n/a | n/a | n/a | n/a |
| review_rounds | reviews | 0 | 0 | 0 | tie |
| review_fix_commits | reviews | 0 | 0 | 0 | tie |
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
| tokens | 0 | 2 | 4 |
| speed | 0 | 2 | 6 |
| efficiency | 0 | 3 | 6 |
| rework | 0 | 6 | 0 |
| plan_fidelity | 0 | 2 | 0 |
| Source-of-truth fidelity | 4 | 12 | 1 |
| errors | 1 | 0 | 5 |
| subagents | 0 | 4 | 5 |
| reviews | 4 | 6 | 2 |
| code_quality | 3 | 12 | 0 |

## Adoption

- PASS: hard gates
- FAIL: E1, E2, E3 win or tie on S1 and S2 ({"S1.tokens_total": null, "S1.cost_usd": null, "S1.wall_min": null, "S2.tokens_total": null, "S2.cost_usd": null, "S2.wall_min": null})
- FAIL: losses do not exceed wins in each group

Result: FLOW is not adopted.

## Work list

- S5 tokens_total (tokens): FLOW 7725651, GATE 6150983
- S5 wall_min (speed): FLOW 22.733, GATE 19.059
- S5 min_to_code (speed): FLOW 14.259, GATE 11.35
- S5 tool_errors (errors): FLOW 8, GATE 6
- S5 error_rate (errors): FLOW 0.04, GATE 0.035
- S5 subagent_errors (subagents): FLOW 7, GATE 6
- S5 tasks_per_executor (subagents): FLOW 0.5, GATE 0.6
- S6 tokens_total (tokens): FLOW 7874549, GATE 3092668
- S6 context_peak (tokens): FLOW 109662, GATE 87940
- S6 wall_min (speed): FLOW 21.678, GATE 5.787
- S6 min_to_code (speed): FLOW 15.975, GATE 4.734
- S6 turns (speed): FLOW 52, GATE 44
- S6 cost_usd (efficiency): FLOW 5.95, GATE 3.256
- S6 cost_per_accept (efficiency): FLOW 0.744, GATE 0.407
- S6 doc_bytes (efficiency): FLOW 6230, GATE 2489
- S6 tool_errors (errors): FLOW 8, GATE 0
- S6 error_rate (errors): FLOW 0.044, GATE 0
- S6 subagent_tokens_median (subagents): FLOW 477740, GATE 254777
- S6 subagent_errors (subagents): FLOW 8, GATE 0
- S6 review_fix_commits (reviews): FLOW 2, GATE 0
- S7 tokens_total (tokens): FLOW 7113326, GATE 2059942
- S7 wall_min (speed): FLOW 20.771, GATE 7.761
- S7 cost_usd (efficiency): FLOW 5.426, GATE 2.801
- S7 cost_per_accept (efficiency): FLOW 0.775, GATE 0.7
- S7 doc_bytes (efficiency): FLOW 11488, GATE 5338
- S7 single_source (source_fidelity): FLOW 13, GATE 4
- S7 tool_errors (errors): FLOW 6, GATE 2
- S7 subagent_errors (subagents): FLOW 6, GATE 0
- S7 blind_findings_total (reviews): FLOW 1, GATE 0


## Efficiency analysis

Median per arm over the runs of the scope; `#n` is the rank of the arm on that metric (1 is best, none for descriptive metrics).

### X1 Token consumption

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| tokens_total | all | 7725651 #2 | 3092668 #1 |
| tokens_total | M | 7725651 #2 | 3092668 #1 |
| tokens_main | all | 3216303 #2 | 2560166 #1 |
| tokens_main | M | 3216303 #2 | 2560166 #1 |
| tokens_subagents | all | 4182868 #2 | 254777 #1 |
| tokens_subagents | M | 4182868 #2 | 254777 #1 |
| context_peak | all | 108615 #2 | 99299 #1 |
| context_peak | M | 108615 #2 | 99299 #1 |
| cost_usd | all | 5.791 #2 | 3.256 #1 |
| cost_usd | M | 5.791 #2 | 3.256 #1 |

### X2 Efficiency of the subagents

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| subagents | all | 6 | 1 |
| subagents | M | 6 | 1 |
| subagent_tokens_median | all | 524563 #2 | 389061.75 #1 |
| subagent_tokens_median | M | 524563 #2 | 389061.75 #1 |
| subagent_tool_calls_median | all | 21 #2 | 14.75 #1 |
| subagent_tool_calls_median | M | 21 #2 | 14.75 #1 |
| subagent_errors | all | 7 #2 | 0 #1 |
| subagent_errors | M | 7 #2 | 0 #1 |
| subagents_wasted | all | 0 #1 | 0 #1 |
| subagents_wasted | M | 0 #1 | 0 #1 |
| tasks_per_executor | all | 0.417 #2 | 0.6 #1 |
| tasks_per_executor | M | 0.417 #2 | 0.6 #1 |
| subagent_token_share | all | 0.565 | 0.084 |
| subagent_token_share | M | 0.565 | 0.084 |

### X3 Error rate during implementation

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| tool_calls | all | 189 | 52 |
| tool_calls | M | 189 | 52 |
| tool_errors | all | 8 #2 | 2 #1 |
| tool_errors | M | 8 #2 | 2 #1 |
| error_rate | all | 0.04 #2 | 0.035 #1 |
| error_rate | M | 0.04 #2 | 0.035 #1 |
| test_runs | all | 14 | 9 |
| test_runs | M | 14 | 9 |
| failed_test_runs | all | 1 #2 | 0 #1 |
| failed_test_runs | M | 1 #2 | 0 #1 |
| kit_self_fixes | all | 0 #1 | 0 #1 |
| kit_self_fixes | M | 0 #1 | 0 #1 |

### X4 Time to complete

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| wall_min | all | 21.678 #2 | 7.761 #1 |
| wall_min | M | 21.678 #2 | 7.761 #1 |
| min_to_code | all | 15.975 #2 | 8.042 #1 |
| min_to_code | M | 15.975 #2 | 8.042 #1 |
| min_per_task | all | 10.386 #2 | 7.057 #1 |
| min_per_task | M | 10.386 #2 | 7.057 #1 |

### X5 Reviews needed for good code

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| review_rounds | all | 0 #1 | 1 #2 |
| review_rounds | M | 0 #1 | 1 #2 |
| review_fix_commits | all | 0 #1 | 0 #1 |
| review_fix_commits | M | 0 #1 | 0 #1 |
| blind_findings_total | all | 0 #1 | 0 #1 |
| blind_findings_total | M | 0 #1 | 0 #1 |

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
| blind_medium | all | 0 #1 | 0 #1 |
| blind_medium | M | 0 #1 | 0 #1 |
| blind_low | all | 0 #1 | 0 #1 |
| blind_low | M | 0 #1 | 0 #1 |
| blind_approve | all | 1 #1 | 1 #1 |
| blind_approve | M | 1 #1 | 1 #1 |
