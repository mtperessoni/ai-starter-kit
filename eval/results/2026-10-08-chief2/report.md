# Evaluation report

Candidate FLOW-FAST versus base SK.

## Six metrics

Totals sum the runs of the arm (n/a for ratios); medians are over its runs.

### Arm FLOW-FAST (2 runs)

| Metric | Field | Total | Median |
|---|---|---|---|
| M1 Token consumption | cost_per_accept | n/a | 0.74 |
| M1 Token consumption | tokens_total | 12080836 | 6040418 |
| M1 Token consumption | tokens_main | 1616438 | 808219 |
| M1 Token consumption | tokens_subagents | 9756378 | 4878189 |
| M1 Token consumption | context_peak | n/a | 59016 |
| M1 Token consumption | start_context | n/a | n/a |
| M1 Token consumption | main_calls | n/a | n/a |
| M1 Token consumption | main_tokens_post_exec | n/a | n/a |
| M1 Token consumption | main_cache_write | n/a | n/a |
| M1 Token consumption | cost_usd | 11.931 | 5.965 |
| M1 Token consumption | cost_main_usd | 2.322 | 1.161 |
| M1 Token consumption | cost_subagents_usd | 9.609 | 4.804 |
| M1 Token consumption | cache_hit_rate | n/a | 0.94 |
| M1 Token consumption | output_share | n/a | 0.013 |
| M1 Token consumption | tokens_per_task | n/a | 3505152.333 |
| M2 Tasks completed successfully | tasks_planned | 4 | 2 |
| M2 Tasks completed successfully | tasks_done | 4 | 2 |
| M2 Tasks completed successfully | hidden_passed | 16 | 8 |
| M2 Tasks completed successfully | hidden_total | 16 | 8 |
| M2 Tasks completed successfully | completed | 2 | 1 |
| M3 Total time | runner_wall_min | 39.72 | 19.86 |
| M3 Total time | wall_min | 39.615 | 19.807 |
| M4 Time per run | runner_wall_min | 39.72 | 19.86 |
| M4 Time per run | wall_min | 39.615 | 19.807 |
| M4 Time per run | main_min | 8.373 | 4.187 |
| M4 Time per run | agent_min | 31.242 | 15.621 |
| M4 Time per run | cold_starts | 14 | 7 |
| M4 Time per run | min_to_docs | n/a | 8.502 |
| M4 Time per run | min_to_code | n/a | 14.102 |
| M4 Time per run | min_per_task | n/a | 12.268 |
| M4 Time per run | main_only_min | n/a | n/a |
| M4 Time per run | parallel_factor | n/a | n/a |
| M5 Error rate | tool_calls | 460 | 230 |
| M5 Error rate | tool_errors | 17 | 8.5 |
| M5 Error rate | error_rate | n/a | 0.039 |
| M5 Error rate | gate_runs_main | 0 | 0 |
| M5 Error rate | gate_runs_sub | 18 | 9 |
| M5 Error rate | gate_fail_ratio | n/a | 0.212 |
| M5 Error rate | rereads | 6 | 3 |
| M5 Error rate | rework_actions | n/a | n/a |
| M5 Error rate | max_reruns_per_step | n/a | n/a |
| M5 Error rate | ceremony_ratio | n/a | n/a |
| M5 Error rate | error_kinds.gate_check | 5 | 2.5 |
| M5 Error rate | error_kinds.environment | 3 | 1.5 |
| M5 Error rate | error_kinds.missing_file | 9 | 4.5 |
| M5 Error rate | error_kinds.test_failure | 0 | 0 |
| M5 Error rate | error_kinds.other | 5 | 2.5 |
| M6 Implementation versus plan | plan_coverage | n/a | 1 |
| M6 Implementation versus plan | plan_drift | n/a | 0 |
| M6 Implementation versus plan | tasks_per_executor | n/a | 0.314 |
| M6 Implementation versus plan | first_pass_rate | n/a | 1 |
| M6 Implementation versus plan | first_pass | n/a | 1 |
| M6 Implementation versus plan | review_rounds | 2 | 1 |
| M6 Implementation versus plan | blind_findings_total | 2 | 1 |
| M6 Implementation versus plan | review_weighted | n/a | 2.128 |
| M6 Implementation versus plan | accept | n/a | 1 |
| M7 Output quality | prd_fidelity | n/a | 1 |
| M7 Output quality | conflict_found | n/a | 1 |
| M7 Output quality | contradiction_left | n/a | 0 |
| M7 Output quality | gap_recorded | n/a | 1 |
| M7 Output quality | traceability | n/a | 1 |
| M7 Output quality | single_source | n/a | 22 |
| M7 Output quality | conflict_recall | n/a | 1 |
| M8 Protocol compliance | docs_dispatched | n/a | 0 |
| M8 Protocol compliance | protocol_adherence | n/a | 1 |
| M8 Protocol compliance | docs_first | n/a | 1 |
| M8 Protocol compliance | dispatch_map | n/a | n/a |
| M8 Protocol compliance | main_violations | 0 | 0 |
| M8 Protocol compliance | chief_violations | 4 | 2 |
| M8 Protocol compliance | return_compliance | n/a | 1 |
| M8 Protocol compliance | surveyor_first | n/a | 1 |
| M8 Protocol compliance | inline_residency | n/a | n/a |
| M8 Protocol compliance | waves | n/a | n/a |

### Per run

| Run | tokens_total | tokens_per_task | tasks_done | tasks_planned | wall_min | main_min | agent_min | cold_starts | error_rate | plan_coverage | accept |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FLOW-FAST S5 r1 | 4475039 | 4475039 | 1 | 1 | 16.997 | 4.533 | 12.464 | 6 | 0.049 | 1 | 1 |
| FLOW-FAST S8 r1 | 7605797 | 2535265.667 | 3 | 3 | 22.618 | 3.84 | 18.777 | 8 | 0.029 | 1 | 1 |

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
- PASS: F1 prd_fidelity: FLOW-FAST at least SK minus 0.05 (FLOW-FAST 1.0, SK None)
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
| tokens_total | all | 6040418 #1 |
| tokens_total | M | 6040418 #1 |
| tokens_main | all | 808219 #1 |
| tokens_main | M | 808219 #1 |
| tokens_subagents | all | 4878189 #1 |
| tokens_subagents | M | 4878189 #1 |
| context_peak | all | 59016 #1 |
| context_peak | M | 59016 #1 |
| cost_usd | all | 5.965 #1 |
| cost_usd | M | 5.965 #1 |

### X2 Efficiency of the subagents

| Metric | Scope | FLOW-FAST |
|---|---|---|
| subagents | all | 7 |
| subagents | M | 7 |
| subagent_tokens_median | all | 748461 #1 |
| subagent_tokens_median | M | 748461 #1 |
| subagent_tool_calls_median | all | 37 #1 |
| subagent_tool_calls_median | M | 37 #1 |
| subagent_errors | all | 8.5 #1 |
| subagent_errors | M | 8.5 #1 |
| subagents_wasted | all | 0 #1 |
| subagents_wasted | M | 0 #1 |
| tasks_per_executor | all | 0.314 #1 |
| tasks_per_executor | M | 0.314 #1 |
| subagent_token_share | all | 0.847 |
| subagent_token_share | M | 0.847 |

### X3 Error rate during implementation

| Metric | Scope | FLOW-FAST |
|---|---|---|
| tool_calls | all | 230 |
| tool_calls | M | 230 |
| tool_errors | all | 8.5 #1 |
| tool_errors | M | 8.5 #1 |
| error_rate | all | 0.039 #1 |
| error_rate | M | 0.039 #1 |
| test_runs | all | 13 |
| test_runs | M | 13 |
| failed_test_runs | all | 2 #1 |
| failed_test_runs | M | 2 #1 |
| kit_self_fixes | all | 0 #1 |
| kit_self_fixes | M | 0 #1 |

### X4 Time to complete

| Metric | Scope | FLOW-FAST |
|---|---|---|
| wall_min | all | 19.807 #1 |
| wall_min | M | 19.807 #1 |
| min_to_code | all | 14.102 #1 |
| min_to_code | M | 14.102 #1 |
| min_per_task | all | 12.268 #1 |
| min_per_task | M | 12.268 #1 |

### X5 Reviews needed for good code

| Metric | Scope | FLOW-FAST |
|---|---|---|
| review_rounds | all | 1 #1 |
| review_rounds | M | 1 #1 |
| review_fix_commits | all | 1 #1 |
| review_fix_commits | M | 1 #1 |
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
| blind_medium | all | 0 #1 |
| blind_medium | M | 0 #1 |
| blind_low | all | 1 #1 |
| blind_low | M | 1 #1 |
| blind_approve | all | 1 #1 |
| blind_approve | M | 1 #1 |
