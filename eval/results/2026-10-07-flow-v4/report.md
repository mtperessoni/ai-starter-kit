# Evaluation report

Candidate FLOW versus base GATE.

## Six metrics

Totals sum the runs of the arm (n/a for ratios); medians are over its runs.

### Arm FLOW (4 runs)

| Metric | Field | Total | Median |
|---|---|---|---|
| M1 Token consumption | tokens_total | 31830094 | 8765993 |
| M1 Token consumption | tokens_main | 17391852 | 4901097 |
| M1 Token consumption | tokens_subagents | 13360697 | 3310246.5 |
| M1 Token consumption | context_peak | n/a | 124074 |
| M1 Token consumption | cost_usd | 27.014 | 6.881 |
| M1 Token consumption | cost_main_usd | 19.032 | 4.572 |
| M1 Token consumption | cost_subagents_usd | 7.982 | 2.032 |
| M1 Token consumption | cache_hit_rate | n/a | 0.957 |
| M1 Token consumption | output_share | n/a | 0.008 |
| M1 Token consumption | tokens_per_task | n/a | 8613977 |
| M2 Tasks completed successfully | tasks_planned | 5 | 1 |
| M2 Tasks completed successfully | tasks_done | 4 | 1 |
| M2 Tasks completed successfully | hidden_passed | 29 | 7 |
| M2 Tasks completed successfully | hidden_total | 29 | 7 |
| M2 Tasks completed successfully | completed | 4 | 1 |
| M3 Total time | wall_min | 75.015 | 19.352 |
| M4 Time per run | wall_min | 75.015 | 19.352 |
| M4 Time per run | main_min | 40.196 | 9.869 |
| M4 Time per run | agent_min | 34.819 | 8.054 |
| M4 Time per run | cold_starts | 20 | 5 |
| M4 Time per run | min_to_docs | n/a | 6.782 |
| M4 Time per run | min_to_code | n/a | 15.122 |
| M4 Time per run | min_per_task | n/a | 19.352 |
| M5 Error rate | tool_calls | 727 | 185.5 |
| M5 Error rate | tool_errors | 25 | 6.5 |
| M5 Error rate | error_rate | n/a | 0.031 |
| M5 Error rate | gate_runs_main | 22 | 5.5 |
| M5 Error rate | gate_runs_sub | 32 | 7.5 |
| M5 Error rate | gate_fail_ratio | n/a | 0.142 |
| M5 Error rate | rereads | 19 | 5 |
| M5 Error rate | error_kinds.gate_check | 9 | 2 |
| M5 Error rate | error_kinds.environment | 4 | 0.5 |
| M5 Error rate | error_kinds.missing_file | 7 | 1 |
| M5 Error rate | error_kinds.test_failure | 3 | 1 |
| M5 Error rate | error_kinds.other | 7 | 1.5 |
| M6 Implementation versus plan | plan_coverage | n/a | 1 |
| M6 Implementation versus plan | plan_drift | n/a | 0 |
| M6 Implementation versus plan | tasks_per_executor | n/a | 0.25 |
| M6 Implementation versus plan | first_pass_rate | n/a | 1 |
| M6 Implementation versus plan | review_rounds | 5 | 1.5 |
| M6 Implementation versus plan | blind_findings_total | 2 | 0.5 |
| M6 Implementation versus plan | accept | n/a | 1 |
| M7 Output quality | prd_fidelity | n/a | 0.792 |
| M7 Output quality | conflict_found | n/a | 1 |
| M7 Output quality | contradiction_left | n/a | 1 |
| M7 Output quality | gap_recorded | n/a | 1 |
| M7 Output quality | traceability | n/a | 0.417 |
| M7 Output quality | single_source | n/a | 13 |
| M8 Protocol compliance | docs_dispatched | n/a | 1 |
| M8 Protocol compliance | protocol_adherence | n/a | 1 |
| M8 Protocol compliance | docs_first | n/a | 1 |

### Arm GATE (3 runs)

| Metric | Field | Total | Median |
|---|---|---|---|
| M1 Token consumption | tokens_total | 11303593 | 3092668 |
| M1 Token consumption | tokens_main | 7374889 | 2560166 |
| M1 Token consumption | tokens_subagents | 3555384 | 254777 |
| M1 Token consumption | context_peak | n/a | 99299 |
| M1 Token consumption | cost_usd | 11.528 | 3.256 |
| M1 Token consumption | cost_main_usd | n/a | n/a |
| M1 Token consumption | cost_subagents_usd | n/a | n/a |
| M1 Token consumption | cache_hit_rate | n/a | n/a |
| M1 Token consumption | output_share | n/a | n/a |
| M1 Token consumption | tokens_per_task | n/a | 2050327.667 |
| M2 Tasks completed successfully | tasks_planned | 4 | 2 |
| M2 Tasks completed successfully | tasks_done | 3 | 1.5 |
| M2 Tasks completed successfully | hidden_passed | 19 | 7 |
| M2 Tasks completed successfully | hidden_total | 22 | 7 |
| M2 Tasks completed successfully | completed | 3 | 1 |
| M3 Total time | wall_min | 32.607 | 7.761 |
| M4 Time per run | wall_min | 32.607 | 7.761 |
| M4 Time per run | main_min | n/a | n/a |
| M4 Time per run | agent_min | n/a | n/a |
| M4 Time per run | cold_starts | 7 | 1 |
| M4 Time per run | min_to_docs | n/a | n/a |
| M4 Time per run | min_to_code | n/a | 8.042 |
| M4 Time per run | min_per_task | n/a | 7.057 |
| M5 Error rate | tool_calls | 258 | 52 |
| M5 Error rate | tool_errors | 8 | 2 |
| M5 Error rate | error_rate | n/a | 0.035 |
| M5 Error rate | gate_runs_main | n/a | n/a |
| M5 Error rate | gate_runs_sub | n/a | n/a |
| M5 Error rate | gate_fail_ratio | n/a | n/a |
| M5 Error rate | rereads | n/a | n/a |
| M5 Error rate | error_kinds.gate_check | n/a | n/a |
| M5 Error rate | error_kinds.environment | n/a | n/a |
| M5 Error rate | error_kinds.missing_file | n/a | n/a |
| M5 Error rate | error_kinds.test_failure | n/a | n/a |
| M5 Error rate | error_kinds.other | n/a | n/a |
| M6 Implementation versus plan | plan_coverage | n/a | 0.5 |
| M6 Implementation versus plan | plan_drift | n/a | 0 |
| M6 Implementation versus plan | tasks_per_executor | n/a | 0.6 |
| M6 Implementation versus plan | first_pass_rate | n/a | 1 |
| M6 Implementation versus plan | review_rounds | 2 | 1 |
| M6 Implementation versus plan | blind_findings_total | 1 | 0 |
| M6 Implementation versus plan | accept | n/a | 1 |
| M7 Output quality | prd_fidelity | n/a | 0.833 |
| M7 Output quality | conflict_found | n/a | 1 |
| M7 Output quality | contradiction_left | n/a | 0.5 |
| M7 Output quality | gap_recorded | n/a | 1 |
| M7 Output quality | traceability | n/a | 1 |
| M7 Output quality | single_source | n/a | 5 |
| M8 Protocol compliance | docs_dispatched | n/a | n/a |
| M8 Protocol compliance | protocol_adherence | n/a | 1 |
| M8 Protocol compliance | docs_first | n/a | 1 |

### Per run

| Run | tokens_total | tokens_per_task | tasks_done | tasks_planned | wall_min | main_min | agent_min | cold_starts | error_rate | plan_coverage | accept |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FLOW S5 r1 | 8918009 | n/a | 0 | 1 | 20.361 | 9.57 | 10.792 | 6 | 0.042 | n/a | 1 |
| FLOW S5 r2 | 9003631 | 9003631 | 1 | 1 | 18.343 | 10.168 | 8.175 | 5 | 0.02 | 1 | 1 |
| FLOW S6 r1 | 5294477 | 2647238.5 | 2 | 2 | 13.758 | 5.824 | 7.934 | 4 | 0.062 | 1 | 1 |
| FLOW S7 r1 | 8613977 | 8613977 | 1 | 1 | 22.553 | 14.634 | 7.918 | 5 | 0.018 | 1 | 1 |
| GATE S5 r1 | 6150983 | 2050327.667 | 3 | 3 | 19.059 | n/a | n/a | 6 | 0.035 | 1 | 1 |
| GATE S6 r1 | 3092668 | n/a | n/a | n/a | 5.787 | n/a | n/a | 1 | 0 | n/a | 1 |
| GATE S7 r1 | 2059942 | n/a | 0 | 1 | 7.761 | n/a | n/a | 0 | 0.061 | 0 | 0.571 |

## Runs

| Arm and scenario | Found | Expected | Missing |
|---|---|---|---|
| GATE.S5 | 1 | 2 | 1 |
| GATE.S6 | 1 | 1 | 0 |
| GATE.S7 | 1 | 1 | 0 |
| FLOW.S5 | 2 | 2 | 0 |
| FLOW.S6 | 1 | 1 | 0 |
| FLOW.S7 | 1 | 1 | 0 |

## Hard gates

- PASS: Q1 accept: FLOW mean at least GATE (FLOW 1.0, GATE 0.8571428571428571)
- PASS: Q2 suite_green: true in every FLOW run (4 of 4)
- PASS: Q3 gate_ok: true in every FLOW run (4 of 4)
- PASS: Q4 completed: true in every FLOW run (4 of 4)
- FAIL: F1 prd_fidelity: FLOW at least GATE minus 0.05 (FLOW 0.7708333333333334, GATE 0.8611111111111112)
- PASS: R4 protocol_adherence: 1.0 in every FLOW run (4 of 4)

## Scorecard S5

| Metric | Group | FLOW | GATE | Band | Verdict |
|---|---|---|---|---|---|
| tokens_total | tokens | 8960820 | 6150983 | 615098.3 | loss |
| context_peak | tokens | 124074 | 107116 | 12744 | loss |
| wall_min | speed | 19.352 | 19.059 | 2.018 | tie |
| min_to_code | speed | 15.239 | 11.35 | 1.135 | loss |
| turns | speed | 62.5 | 51 | 5.1 | loss |
| cost_usd | efficiency | 6.881 | 5.47 | 0.547 | loss |
| cost_per_accept | efficiency | 0.983 | 0.781 | 0.078 | loss |
| doc_bytes | efficiency | 9613 | 8996 | 1198 | tie |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | 1 | 1 | 0.1 | tie |
| plan_drift | plan_fidelity | 0.5 | 0 | 1 | tie |
| traceability | Source-of-truth fidelity | 0.5 | 1 | 0.1 | loss |
| docs_first | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| promoted | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| single_source | Source-of-truth fidelity | 15.5 | 14 | 5 | tie |
| conflict_found | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| contradiction_left | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| gap_recorded | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| tool_errors | errors | 6.5 | 6 | 5 | tie |
| error_rate | errors | 0.031 | 0.035 | 0.023 | tie |
| subagent_tokens_median | subagents | 628902.5 | 523346.5 | 52334.65 | loss |
| subagent_errors | subagents | 4.5 | 6 | 3 | tie |
| subagents_wasted | subagents | 0 | 0 | 0 | tie |
| tasks_per_executor | subagents | 0.25 | 0.6 | 0.06 | loss |
| review_rounds | reviews | 1.5 | 1 | 1 | tie |
| review_fix_commits | reviews | 1.5 | 2 | 1 | tie |
| blind_findings_total | reviews | 0.5 | 1 | 1 | tie |
| blind_approve | reviews | 1 | 0 | 0 | win |
| accept | code_quality | 1 | 1 | 0.1 | tie |
| suite_green | code_quality | 1 | 1 | 0.1 | tie |
| blind_bugs | code_quality | 0 | 1 | 0.1 | win |
| blind_critical | code_quality | 0 | 0 | 0 | tie |
| blind_high | code_quality | 0 | 1 | 0.1 | win |

## Scorecard S6

| Metric | Group | FLOW | GATE | Band | Verdict |
|---|---|---|---|---|---|
| tokens_total | tokens | 5294477 | 3092668 | 309266.8 | loss |
| context_peak | tokens | 98311 | 87940 | 8794 | loss |
| wall_min | speed | 13.758 | 5.787 | 0.579 | loss |
| min_to_code | speed | 10.713 | 4.734 | 0.473 | loss |
| turns | speed | 37 | 44 | 4.4 | win |
| cost_usd | efficiency | 4.898 | 3.256 | 0.326 | loss |
| cost_per_accept | efficiency | 0.612 | 0.407 | 0.041 | loss |
| doc_bytes | efficiency | 6981 | 2489 | 248.9 | loss |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | n/a | n/a | n/a | n/a |
| plan_drift | plan_fidelity | n/a | n/a | n/a | n/a |
| traceability | Source-of-truth fidelity | 0.333 | 1 | 0.1 | loss |
| docs_first | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| promoted | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| single_source | Source-of-truth fidelity | 13 | 5 | 0.5 | loss |
| conflict_found | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| contradiction_left | Source-of-truth fidelity | 0 | 0 | 0 | tie |
| gap_recorded | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| tool_errors | errors | 9 | 0 | 0 | loss |
| error_rate | errors | 0.062 | 0 | 0 | loss |
| subagent_tokens_median | subagents | 736747.5 | 254777 | 25477.7 | loss |
| subagent_errors | subagents | 9 | 0 | 0 | loss |
| subagents_wasted | subagents | 0 | 0 | 0 | tie |
| tasks_per_executor | subagents | n/a | n/a | n/a | n/a |
| review_rounds | reviews | 0 | 1 | 0.1 | win |
| review_fix_commits | reviews | 0 | 0 | 0 | tie |
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
| tokens_total | tokens | 8613977 | 2059942 | 205994.2 | loss |
| context_peak | tokens | 131502 | 99299 | 9929.9 | loss |
| wall_min | speed | 22.553 | 7.761 | 0.776 | loss |
| min_to_code | speed | n/a | n/a | n/a | n/a |
| turns | speed | 61 | 35 | 3.5 | loss |
| cost_usd | efficiency | 8.355 | 2.801 | 0.28 | loss |
| cost_per_accept | efficiency | 1.194 | 0.7 | 0.07 | loss |
| doc_bytes | efficiency | 11226 | 5338 | 533.8 | loss |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | 1 | 0 | 0 | win |
| plan_drift | plan_fidelity | n/a | n/a | n/a | n/a |
| traceability | Source-of-truth fidelity | 0.25 | 0 | 0 | win |
| docs_first | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| promoted | Source-of-truth fidelity | 0 | 0 | 0 | tie |
| single_source | Source-of-truth fidelity | 10 | 4 | 0.4 | loss |
| conflict_found | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| contradiction_left | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| gap_recorded | Source-of-truth fidelity | 1 | 1 | 0.1 | tie |
| tool_errors | errors | 3 | 2 | 0.2 | loss |
| error_rate | errors | 0.018 | 0.061 | 0.006 | win |
| subagent_tokens_median | subagents | n/a | n/a | n/a | n/a |
| subagent_errors | subagents | 3 | 0 | 0 | loss |
| subagents_wasted | subagents | 0 | 0 | 0 | tie |
| tasks_per_executor | subagents | n/a | n/a | n/a | n/a |
| review_rounds | reviews | 2 | 0 | 0 | loss |
| review_fix_commits | reviews | 3 | 0 | 0 | loss |
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
| speed | 1 | 1 | 6 |
| efficiency | 0 | 1 | 8 |
| rework | 0 | 6 | 0 |
| plan_fidelity | 1 | 2 | 0 |
| Source-of-truth fidelity | 1 | 12 | 4 |
| errors | 1 | 2 | 3 |
| subagents | 0 | 4 | 5 |
| reviews | 2 | 7 | 3 |
| code_quality | 3 | 12 | 0 |

## Adoption

- FAIL: hard gates
- FAIL: E1, E2, E3 win or tie on S1 and S2 ({"S1.tokens_total": null, "S1.cost_usd": null, "S1.wall_min": null, "S2.tokens_total": null, "S2.cost_usd": null, "S2.wall_min": null})
- FAIL: losses do not exceed wins in each group

Result: FLOW is not adopted.

## Work list

- S5 tokens_total (tokens): FLOW 8960820, GATE 6150983
- S5 context_peak (tokens): FLOW 124074, GATE 107116
- S5 min_to_code (speed): FLOW 15.239, GATE 11.35
- S5 turns (speed): FLOW 62.5, GATE 51
- S5 cost_usd (efficiency): FLOW 6.881, GATE 5.47
- S5 cost_per_accept (efficiency): FLOW 0.983, GATE 0.781
- S5 traceability (source_fidelity): FLOW 0.5, GATE 1
- S5 subagent_tokens_median (subagents): FLOW 628902.5, GATE 523346.5
- S5 tasks_per_executor (subagents): FLOW 0.25, GATE 0.6
- S6 tokens_total (tokens): FLOW 5294477, GATE 3092668
- S6 context_peak (tokens): FLOW 98311, GATE 87940
- S6 wall_min (speed): FLOW 13.758, GATE 5.787
- S6 min_to_code (speed): FLOW 10.713, GATE 4.734
- S6 cost_usd (efficiency): FLOW 4.898, GATE 3.256
- S6 cost_per_accept (efficiency): FLOW 0.612, GATE 0.407
- S6 doc_bytes (efficiency): FLOW 6981, GATE 2489
- S6 traceability (source_fidelity): FLOW 0.333, GATE 1
- S6 single_source (source_fidelity): FLOW 13, GATE 5
- S6 tool_errors (errors): FLOW 9, GATE 0
- S6 error_rate (errors): FLOW 0.062, GATE 0
- S6 subagent_tokens_median (subagents): FLOW 736747.5, GATE 254777
- S6 subagent_errors (subagents): FLOW 9, GATE 0
- S7 tokens_total (tokens): FLOW 8613977, GATE 2059942
- S7 context_peak (tokens): FLOW 131502, GATE 99299
- S7 wall_min (speed): FLOW 22.553, GATE 7.761
- S7 turns (speed): FLOW 61, GATE 35
- S7 cost_usd (efficiency): FLOW 8.355, GATE 2.801
- S7 cost_per_accept (efficiency): FLOW 1.194, GATE 0.7
- S7 doc_bytes (efficiency): FLOW 11226, GATE 5338
- S7 single_source (source_fidelity): FLOW 10, GATE 4
- S7 tool_errors (errors): FLOW 3, GATE 2
- S7 subagent_errors (subagents): FLOW 3, GATE 0
- S7 review_rounds (reviews): FLOW 2, GATE 0
- S7 review_fix_commits (reviews): FLOW 3, GATE 0
- S7 blind_findings_total (reviews): FLOW 1, GATE 0

1 run(s) are missing; medians use only the runs present.


## Efficiency analysis

Median per arm over the runs of the scope; `#n` is the rank of the arm on that metric (1 is best, none for descriptive metrics).

### X1 Token consumption

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| tokens_total | all | 8765993 #2 | 3092668 #1 |
| tokens_total | M | 8765993 #2 | 3092668 #1 |
| tokens_main | all | 4901097 #2 | 2560166 #1 |
| tokens_main | M | 4901097 #2 | 2560166 #1 |
| tokens_subagents | all | 3310246.5 #2 | 254777 #1 |
| tokens_subagents | M | 3310246.5 #2 | 254777 #1 |
| context_peak | all | 124074 #2 | 99299 #1 |
| context_peak | M | 124074 #2 | 99299 #1 |
| cost_usd | all | 6.881 #2 | 3.256 #1 |
| cost_usd | M | 6.881 #2 | 3.256 #1 |

### X2 Efficiency of the subagents

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| subagents | all | 5 | 1 |
| subagents | M | 5 | 1 |
| subagent_tokens_median | all | 628902.5 #2 | 389061.75 #1 |
| subagent_tokens_median | M | 628902.5 #2 | 389061.75 #1 |
| subagent_tool_calls_median | all | 27.25 #2 | 14.75 #1 |
| subagent_tool_calls_median | M | 27.25 #2 | 14.75 #1 |
| subagent_errors | all | 4.5 #2 | 0 #1 |
| subagent_errors | M | 4.5 #2 | 0 #1 |
| subagents_wasted | all | 0 #1 | 0 #1 |
| subagents_wasted | M | 0 #1 | 0 #1 |
| tasks_per_executor | all | 0.25 #2 | 0.6 #1 |
| tasks_per_executor | M | 0.25 #2 | 0.6 #1 |
| subagent_token_share | all | 0.433 | 0.084 |
| subagent_token_share | M | 0.433 | 0.084 |

### X3 Error rate during implementation

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| tool_calls | all | 185.5 | 52 |
| tool_calls | M | 185.5 | 52 |
| tool_errors | all | 6.5 #2 | 2 #1 |
| tool_errors | M | 6.5 #2 | 2 #1 |
| error_rate | all | 0.031 #1 | 0.035 #2 |
| error_rate | M | 0.031 #1 | 0.035 #2 |
| test_runs | all | 11.5 | 9 |
| test_runs | M | 11.5 | 9 |
| failed_test_runs | all | 1.5 #2 | 0 #1 |
| failed_test_runs | M | 1.5 #2 | 0 #1 |
| kit_self_fixes | all | 0 #1 | 0 #1 |
| kit_self_fixes | M | 0 #1 | 0 #1 |

### X4 Time to complete

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| wall_min | all | 19.352 #2 | 7.761 #1 |
| wall_min | M | 19.352 #2 | 7.761 #1 |
| min_to_code | all | 15.122 #2 | 8.042 #1 |
| min_to_code | M | 15.122 #2 | 8.042 #1 |
| min_per_task | all | 19.352 #2 | 7.057 #1 |
| min_per_task | M | 19.352 #2 | 7.057 #1 |

### X5 Reviews needed for good code

| Metric | Scope | FLOW | GATE |
|---|---|---|---|
| review_rounds | all | 1.5 #2 | 1 #1 |
| review_rounds | M | 1.5 #2 | 1 #1 |
| review_fix_commits | all | 1.5 #2 | 0 #1 |
| review_fix_commits | M | 1.5 #2 | 0 #1 |
| blind_findings_total | all | 0.5 #2 | 0 #1 |
| blind_findings_total | M | 0.5 #2 | 0 #1 |

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
