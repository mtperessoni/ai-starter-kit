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
- FAIL: F1 prd_fidelity: FLOW at least GATE minus 0.05 (FLOW 0.8055555555555557, GATE 0.8611111111111112)
- PASS: R4 protocol_adherence: 1.0 in every FLOW run (3 of 3)

## Scorecard S5

| Metric | Group | FLOW | GATE | Band | Verdict |
|---|---|---|---|---|---|
| tokens_total | tokens | 7705651 | 6150983 | 615098.3 | loss |
| context_peak | tokens | 174404 | 107116 | 10711.6 | loss |
| wall_min | speed | 22.242 | 19.059 | 1.906 | loss |
| min_to_code | speed | 16.067 | 11.35 | 1.135 | loss |
| turns | speed | 88 | 51 | 5.1 | loss |
| cost_usd | efficiency | 7.801 | 5.47 | 0.547 | loss |
| cost_per_accept | efficiency | 1.114 | 0.781 | 0.078 | loss |
| doc_bytes | efficiency | 8993 | 8996 | 899.6 | tie |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | 1 | 1 | 0.1 | tie |
| plan_drift | plan_fidelity | 0 | 0 | 0 | tie |
| traceability | Source-of-truth fidelity | 0.6 | 1 | 0.1 | loss |
| docs_first | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| promoted | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| single_source | Source-of-truth fidelity | 21 | 14 | 1.4 | loss |
| conflict_found | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| contradiction_left | Source-of-truth fidelity | 0 | 1 | 0.1 | win |
| gap_recorded | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| tool_errors | errors | 0 | 6 | 0.6 | win |
| error_rate | errors | 0 | 0.035 | 0.003 | win |
| subagent_tokens_median | subagents | 631776 | 523346.5 | 52334.65 | loss |
| subagent_errors | subagents | 0 | 6 | 0.6 | win |
| subagents_wasted | subagents | 0 | 0 | 0 | tie |
| tasks_per_executor | subagents | 2 | 0.6 | 0.06 | win |
| review_rounds | reviews | 1 | 1 | 0.1 | tie |
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
| tokens_total | tokens | 5499760 | 3092668 | 309266.8 | loss |
| context_peak | tokens | 115710 | 87940 | 8794 | loss |
| wall_min | speed | 11.807 | 5.787 | 0.579 | loss |
| min_to_code | speed | 8.867 | 4.734 | 0.473 | loss |
| turns | speed | 61 | 44 | 4.4 | loss |
| cost_usd | efficiency | 4.712 | 3.256 | 0.326 | loss |
| cost_per_accept | efficiency | 0.589 | 0.407 | 0.041 | loss |
| doc_bytes | efficiency | 6973 | 2489 | 248.9 | loss |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | n/a | n/a | n/a | n/a |
| plan_drift | plan_fidelity | n/a | n/a | n/a | n/a |
| traceability | Source-of-truth fidelity | 0.25 | 1 | 0.1 | loss |
| docs_first | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| promoted | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| single_source | Source-of-truth fidelity | 10 | 5 | 0.5 | loss |
| conflict_found | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| contradiction_left | Source-of-truth fidelity | 0 | 0 | 0 | tie |
| gap_recorded | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| tool_errors | errors | 1 | 0 | 0 | loss |
| error_rate | errors | 0.012 | 0 | 0 | loss |
| subagent_tokens_median | subagents | 359967 | 254777 | 25477.7 | loss |
| subagent_errors | subagents | 0 | 0 | 0 | tie |
| subagents_wasted | subagents | 0 | 0 | 0 | tie |
| tasks_per_executor | subagents | n/a | n/a | n/a | n/a |
| review_rounds | reviews | 1 | 1 | 0.1 | tie |
| review_fix_commits | reviews | 1 | 0 | 0 | loss |
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
| tokens_total | tokens | 5737982 | 2059942 | 205994.2 | loss |
| context_peak | tokens | 127506 | 99299 | 9929.9 | loss |
| wall_min | speed | 18.637 | 7.761 | 0.776 | loss |
| min_to_code | speed | n/a | n/a | n/a | n/a |
| turns | speed | 62 | 35 | 3.5 | loss |
| cost_usd | efficiency | 5.866 | 2.801 | 0.28 | loss |
| cost_per_accept | efficiency | 0.838 | 0.7 | 0.07 | loss |
| doc_bytes | efficiency | 9314 | 5338 | 533.8 | loss |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | 1 | 0 | 0 | win |
| plan_drift | plan_fidelity | n/a | n/a | n/a | n/a |
| traceability | Source-of-truth fidelity | 1 | 0 | 0 | win |
| docs_first | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| promoted | Source-of-truth fidelity | 1 | 0 | 0 | win |
| single_source | Source-of-truth fidelity | 6 | 4 | 0.4 | loss |
| conflict_found | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| contradiction_left | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| gap_recorded | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| tool_errors | errors | 0 | 2 | 0.2 | win |
| error_rate | errors | 0 | 0.061 | 0.006 | win |
| subagent_tokens_median | subagents | n/a | n/a | n/a | n/a |
| subagent_errors | subagents | 0 | 0 | 0 | tie |
| subagents_wasted | subagents | 0 | 0 | 0 | tie |
| tasks_per_executor | subagents | n/a | n/a | n/a | n/a |
| review_rounds | reviews | 2 | 0 | 0 | loss |
| review_fix_commits | reviews | 2 | 0 | 0 | loss |
| blind_findings_total | reviews | 0 | 0 | 0 | tie |
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
| speed | 0 | 0 | 8 |
| efficiency | 0 | 1 | 8 |
| rework | 0 | 6 | 0 |
| plan_fidelity | 1 | 2 | 0 |
| Source-of-truth fidelity | 3 | 9 | 5 |
| errors | 4 | 0 | 2 |
| subagents | 2 | 5 | 2 |
| reviews | 2 | 7 | 3 |
| code_quality | 3 | 12 | 0 |

## Adoption

- FAIL: hard gates
- FAIL: E1, E2, E3 win or tie on S1 and S2 ({"S1.tokens_total": null, "S1.cost_usd": null, "S1.wall_min": null, "S2.tokens_total": null, "S2.cost_usd": null, "S2.wall_min": null})
- FAIL: losses do not exceed wins in each group

Result: FLOW is not adopted.

## Work list

- S5 tokens_total (tokens): FLOW 7705651, GATE 6150983
- S5 context_peak (tokens): FLOW 174404, GATE 107116
- S5 wall_min (speed): FLOW 22.242, GATE 19.059
- S5 min_to_code (speed): FLOW 16.067, GATE 11.35
- S5 turns (speed): FLOW 88, GATE 51
- S5 cost_usd (efficiency): FLOW 7.801, GATE 5.47
- S5 cost_per_accept (efficiency): FLOW 1.114, GATE 0.781
- S5 traceability (source_fidelity): FLOW 0.6, GATE 1
- S5 single_source (source_fidelity): FLOW 21, GATE 14
- S5 subagent_tokens_median (subagents): FLOW 631776, GATE 523346.5
- S6 tokens_total (tokens): FLOW 5499760, GATE 3092668
- S6 context_peak (tokens): FLOW 115710, GATE 87940
- S6 wall_min (speed): FLOW 11.807, GATE 5.787
- S6 min_to_code (speed): FLOW 8.867, GATE 4.734
- S6 turns (speed): FLOW 61, GATE 44
- S6 cost_usd (efficiency): FLOW 4.712, GATE 3.256
- S6 cost_per_accept (efficiency): FLOW 0.589, GATE 0.407
- S6 doc_bytes (efficiency): FLOW 6973, GATE 2489
- S6 traceability (source_fidelity): FLOW 0.25, GATE 1
- S6 single_source (source_fidelity): FLOW 10, GATE 5
- S6 tool_errors (errors): FLOW 1, GATE 0
- S6 error_rate (errors): FLOW 0.012, GATE 0
- S6 subagent_tokens_median (subagents): FLOW 359967, GATE 254777
- S6 review_fix_commits (reviews): FLOW 1, GATE 0
- S7 tokens_total (tokens): FLOW 5737982, GATE 2059942
- S7 context_peak (tokens): FLOW 127506, GATE 99299
- S7 wall_min (speed): FLOW 18.637, GATE 7.761
- S7 turns (speed): FLOW 62, GATE 35
- S7 cost_usd (efficiency): FLOW 5.866, GATE 2.801
- S7 cost_per_accept (efficiency): FLOW 0.838, GATE 0.7
- S7 doc_bytes (efficiency): FLOW 9314, GATE 5338
- S7 single_source (source_fidelity): FLOW 6, GATE 4
- S7 review_rounds (reviews): FLOW 2, GATE 0
- S7 review_fix_commits (reviews): FLOW 2, GATE 0


## Efficiency analysis

Median per arm over the runs of the scope; `#n` is the rank of the arm on that metric (1 is best, none for descriptive metrics).

### X1 Token consumption

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| tokens_total | all | 5737982 #2 | 3092668 #1 |
| tokens_total | M | 5737982 #2 | 3092668 #1 |
| tokens_main | all | 4699605 #2 | 2560166 #1 |
| tokens_main | M | 4699605 #2 | 2560166 #1 |
| tokens_subagents | all | 907162 #2 | 254777 #1 |
| tokens_subagents | M | 907162 #2 | 254777 #1 |
| context_peak | all | 127506 #2 | 99299 #1 |
| context_peak | M | 127506 #2 | 99299 #1 |
| cost_usd | all | 5.866 #2 | 3.256 #1 |
| cost_usd | M | 5.866 #2 | 3.256 #1 |

### X2 Efficiency of the subagents

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| subagents | all | 2 | 1 |
| subagents | M | 2 | 1 |
| subagent_tokens_median | all | 453581 #2 | 389061.75 #1 |
| subagent_tokens_median | M | 453581 #2 | 389061.75 #1 |
| subagent_tool_calls_median | all | 15.5 #2 | 14.75 #1 |
| subagent_tool_calls_median | M | 15.5 #2 | 14.75 #1 |
| subagent_errors | all | 0 #1 | 0 #1 |
| subagent_errors | M | 0 #1 | 0 #1 |
| subagents_wasted | all | 0 #1 | 0 #1 |
| subagents_wasted | M | 0 #1 | 0 #1 |
| tasks_per_executor | all | 2 #1 | 0.6 #2 |
| tasks_per_executor | M | 2 #1 | 0.6 #2 |
| subagent_token_share | all | 0.162 | 0.084 |
| subagent_token_share | M | 0.162 | 0.084 |

### X3 Error rate during implementation

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| tool_calls | all | 91 | 52 |
| tool_calls | M | 91 | 52 |
| tool_errors | all | 0 #1 | 2 #2 |
| tool_errors | M | 0 #1 | 2 #2 |
| error_rate | all | 0 #1 | 0.035 #2 |
| error_rate | M | 0 #1 | 0.035 #2 |
| test_runs | all | 14 | 9 |
| test_runs | M | 14 | 9 |
| failed_test_runs | all | 1 #2 | 0 #1 |
| failed_test_runs | M | 1 #2 | 0 #1 |
| kit_self_fixes | all | 0 #1 | 0 #1 |
| kit_self_fixes | M | 0 #1 | 0 #1 |

### X4 Time to complete

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| wall_min | all | 18.637 #2 | 7.761 #1 |
| wall_min | M | 18.637 #2 | 7.761 #1 |
| min_to_code | all | 12.75 #2 | 8.042 #1 |
| min_to_code | M | 12.75 #2 | 8.042 #1 |
| min_per_task | all | 9.318 #2 | 7.057 #1 |
| min_per_task | M | 9.318 #2 | 7.057 #1 |

### X5 Reviews needed for good code

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| review_rounds | all | 1 #1 | 1 #1 |
| review_rounds | M | 1 #1 | 1 #1 |
| review_fix_commits | all | 2 #2 | 0 #1 |
| review_fix_commits | M | 2 #2 | 0 #1 |
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
