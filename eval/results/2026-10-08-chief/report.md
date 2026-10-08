# Evaluation report

Candidate FLOW-FAST versus base SK.

## Six metrics

Totals sum the runs of the arm (n/a for ratios); medians are over its runs.

### Arm FLOW-FAST (2 runs)

| Metric | Field | Total | Median |
|---|---|---|---|
| M1 Token consumption | cost_per_accept | n/a | 0.839 |
| M1 Token consumption | tokens_total | 14017051 | 7008525.5 |
| M1 Token consumption | tokens_main | 2058179 | 1029089.5 |
| M1 Token consumption | tokens_subagents | 11052461 | 5526230.5 |
| M1 Token consumption | context_peak | n/a | 58146 |
| M1 Token consumption | start_context | n/a | n/a |
| M1 Token consumption | main_calls | n/a | n/a |
| M1 Token consumption | main_tokens_post_exec | n/a | n/a |
| M1 Token consumption | main_cache_write | n/a | n/a |
| M1 Token consumption | cost_usd | 13.486 | 6.743 |
| M1 Token consumption | cost_main_usd | 2.592 | 1.296 |
| M1 Token consumption | cost_subagents_usd | 10.894 | 5.447 |
| M1 Token consumption | cache_hit_rate | n/a | 0.94 |
| M1 Token consumption | output_share | n/a | 0.013 |
| M1 Token consumption | tokens_per_task | n/a | 2790116.333 |
| M2 Tasks completed successfully | tasks_planned | 5 | 2.5 |
| M2 Tasks completed successfully | tasks_done | 5 | 2.5 |
| M2 Tasks completed successfully | hidden_passed | 16 | 8 |
| M2 Tasks completed successfully | hidden_total | 16 | 8 |
| M2 Tasks completed successfully | completed | 2 | 1 |
| M3 Total time | wall_min | 47.303 | 23.651 |
| M4 Time per run | wall_min | 47.303 | 23.651 |
| M4 Time per run | main_min | 10.436 | 5.218 |
| M4 Time per run | agent_min | 36.866 | 18.433 |
| M4 Time per run | cold_starts | 21 | 10.5 |
| M4 Time per run | min_to_docs | n/a | 8.579 |
| M4 Time per run | min_to_code | n/a | 14.787 |
| M4 Time per run | min_per_task | n/a | 9.678 |
| M4 Time per run | main_only_min | n/a | n/a |
| M4 Time per run | parallel_factor | n/a | n/a |
| M5 Error rate | tool_calls | 577 | 288.5 |
| M5 Error rate | tool_errors | 30 | 15 |
| M5 Error rate | error_rate | n/a | 0.053 |
| M5 Error rate | gate_runs_main | 0 | 0 |
| M5 Error rate | gate_runs_sub | 23 | 11.5 |
| M5 Error rate | gate_fail_ratio | n/a | 0.254 |
| M5 Error rate | rereads | 8 | 4 |
| M5 Error rate | rework_actions | n/a | n/a |
| M5 Error rate | max_reruns_per_step | n/a | n/a |
| M5 Error rate | ceremony_ratio | n/a | n/a |
| M5 Error rate | error_kinds.gate_check | 7 | 3.5 |
| M5 Error rate | error_kinds.environment | 5 | 2.5 |
| M5 Error rate | error_kinds.missing_file | 11 | 5.5 |
| M5 Error rate | error_kinds.test_failure | 0 | 0 |
| M5 Error rate | error_kinds.other | 12 | 6 |
| M6 Implementation versus plan | plan_coverage | n/a | 1 |
| M6 Implementation versus plan | plan_drift | n/a | 0 |
| M6 Implementation versus plan | tasks_per_executor | n/a | 0.299 |
| M6 Implementation versus plan | first_pass_rate | n/a | 1 |
| M6 Implementation versus plan | first_pass | n/a | 0 |
| M6 Implementation versus plan | review_rounds | 4 | 2 |
| M6 Implementation versus plan | blind_findings_total | 2 | 1 |
| M6 Implementation versus plan | review_weighted | n/a | 4.545 |
| M6 Implementation versus plan | accept | n/a | 1 |
| M7 Output quality | prd_fidelity | n/a | 0.917 |
| M7 Output quality | conflict_found | n/a | 1 |
| M7 Output quality | contradiction_left | n/a | 0 |
| M7 Output quality | gap_recorded | n/a | 1 |
| M7 Output quality | traceability | n/a | 1 |
| M7 Output quality | single_source | n/a | 16.5 |
| M7 Output quality | conflict_recall | n/a | 1 |
| M8 Protocol compliance | docs_dispatched | n/a | 0 |
| M8 Protocol compliance | protocol_adherence | n/a | 1 |
| M8 Protocol compliance | docs_first | n/a | 1 |
| M8 Protocol compliance | dispatch_map | n/a | n/a |
| M8 Protocol compliance | main_violations | n/a | n/a |
| M8 Protocol compliance | inline_residency | n/a | n/a |
| M8 Protocol compliance | waves | n/a | n/a |

### Per run

| Run | tokens_total | tokens_per_task | tasks_done | tasks_planned | wall_min | main_min | agent_min | cold_starts | error_rate | plan_coverage | accept |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FLOW-FAST S5 r1 | 5447294 | 2723647 | 2 | 2 | 21.525 | 6.152 | 15.373 | 11 | 0.062 | 1 | 1 |
| FLOW-FAST S8 r1 | 8569757 | 2856585.667 | 3 | 3 | 25.778 | 4.285 | 21.493 | 10 | 0.045 | 1 | 1 |

## Runs

| Arm and scenario | Found | Expected | Missing |
|---|---|---|---|
| SK.S5 | 0 | 1 | 1 |
| SK.S8 | 0 | 1 | 1 |
| FLOW-FAST.S5 | 1 | 1 | 0 |
| FLOW-FAST.S8 | 1 | 1 | 0 |

## Hard gates

- PASS: Q1 accept: FLOW-FAST mean at least SK (FLOW-FAST 1.0, SK None)
- PASS: Q2 suite_green: true in every FLOW-FAST run (2 of 2)
- PASS: Q3 gate_ok: true in every FLOW-FAST run (2 of 2)
- PASS: Q4 completed: true in every FLOW-FAST run (2 of 2)
- PASS: F1 prd_fidelity: FLOW-FAST at least SK minus 0.05 (FLOW-FAST 0.9166666666666667, SK None)
- PASS: R4 protocol_adherence: 1.0 in every FLOW-FAST run (2 of 2)

## Scorecard S5

| Metric | Group | FLOW-FAST | SK | Band | Verdict |
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
| traceability | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| docs_first | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| promoted | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| single_source | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| conflict_found | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| contradiction_left | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| gap_recorded | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
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

## Scorecard S8

| Metric | Group | FLOW-FAST | SK | Band | Verdict |
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
| traceability | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| docs_first | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| promoted | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| single_source | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| conflict_found | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| contradiction_left | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
| gap_recorded | Source-of-truth fidelity | n/a | n/a | n/a | n/a |
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
| Source-of-truth fidelity | 0 | 0 | 0 |
| errors | 0 | 0 | 0 |
| subagents | 0 | 0 | 0 |
| reviews | 0 | 0 | 0 |
| code_quality | 0 | 0 | 0 |

## Adoption

- PASS: hard gates
- FAIL: E1, E2, E3 win or tie on S1 and S2 ({"S1.tokens_total": null, "S1.cost_usd": null, "S1.wall_min": null, "S2.tokens_total": null, "S2.cost_usd": null, "S2.wall_min": null})
- PASS: losses do not exceed wins in each group

Result: FLOW-FAST is not adopted.

2 run(s) are missing; medians use only the runs present.


## Efficiency analysis

Median per arm over the runs of the scope; `#n` is the rank of the arm on that metric (1 is best, none for descriptive metrics).

### X1 Token consumption

| Metric | Scope | FLOW-FAST |
|---|---|---|
| tokens_total | all | 7008525.5 #1 |
| tokens_total | M | 7008525.5 #1 |
| tokens_main | all | 1029089.5 #1 |
| tokens_main | M | 1029089.5 #1 |
| tokens_subagents | all | 5526230.5 #1 |
| tokens_subagents | M | 5526230.5 #1 |
| context_peak | all | 58146 #1 |
| context_peak | M | 58146 #1 |
| cost_usd | all | 6.743 #1 |
| cost_usd | M | 6.743 #1 |

### X2 Efficiency of the subagents

| Metric | Scope | FLOW-FAST |
|---|---|---|
| subagents | all | 10.5 |
| subagents | M | 10.5 |
| subagent_tokens_median | all | 670623.75 #1 |
| subagent_tokens_median | M | 670623.75 #1 |
| subagent_tool_calls_median | all | 29.5 #1 |
| subagent_tool_calls_median | M | 29.5 #1 |
| subagent_errors | all | 14.5 #1 |
| subagent_errors | M | 14.5 #1 |
| subagents_wasted | all | 1 #1 |
| subagents_wasted | M | 1 #1 |
| tasks_per_executor | all | 0.299 #1 |
| tasks_per_executor | M | 0.299 #1 |
| subagent_token_share | all | 0.834 |
| subagent_token_share | M | 0.834 |

### X3 Error rate during implementation

| Metric | Scope | FLOW-FAST |
|---|---|---|
| tool_calls | all | 288.5 |
| tool_calls | M | 288.5 |
| tool_errors | all | 15 #1 |
| tool_errors | M | 15 #1 |
| error_rate | all | 0.053 #1 |
| error_rate | M | 0.053 #1 |
| test_runs | all | 20.5 |
| test_runs | M | 20.5 |
| failed_test_runs | all | 3.5 #1 |
| failed_test_runs | M | 3.5 #1 |
| kit_self_fixes | all | 0 #1 |
| kit_self_fixes | M | 0 #1 |

### X4 Time to complete

| Metric | Scope | FLOW-FAST |
|---|---|---|
| wall_min | all | 23.651 #1 |
| wall_min | M | 23.651 #1 |
| min_to_code | all | 14.787 #1 |
| min_to_code | M | 14.787 #1 |
| min_per_task | all | 9.678 #1 |
| min_per_task | M | 9.678 #1 |

### X5 Reviews needed for good code

| Metric | Scope | FLOW-FAST |
|---|---|---|
| review_rounds | all | 2 #1 |
| review_rounds | M | 2 #1 |
| review_fix_commits | all | 1.5 #1 |
| review_fix_commits | M | 1.5 #1 |
| blind_findings_total | all | 1 #1 |
| blind_findings_total | M | 1 #1 |

### X6 Code with fewest problems

| Metric | Scope | FLOW-FAST |
|---|---|---|
| accept | all | 1 #1 |
| accept | M | 1 #1 |
| suite_green | all | 1 #1 |
| suite_green | M | 1 #1 |
| blind_bugs | all | 0 #1 |
| blind_bugs | M | 0 #1 |
| blind_critical | all | 0 #1 |
| blind_critical | M | 0 #1 |
| blind_high | all | 0 #1 |
| blind_high | M | 0 #1 |
| blind_medium | all | 1 #1 |
| blind_medium | M | 1 #1 |
| blind_low | all | 0 #1 |
| blind_low | M | 0 #1 |
| blind_approve | all | 1 #1 |
| blind_approve | M | 1 #1 |
