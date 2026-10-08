# Evaluation report

Candidate LT versus base SK.

## Six metrics

Totals sum the runs of the arm (n/a for ratios); medians are over its runs.

### Arm FLOW-FAST (5 runs)

| Metric | Field | Total | Median |
|---|---|---|---|
| M1 Token consumption | cost_per_accept | n/a | 0.644 |
| M1 Token consumption | tokens_total | 24139676 | 4490362 |
| M1 Token consumption | tokens_main | 9589413 | 2007328 |
| M1 Token consumption | tokens_subagents | 13435419 | 2333431 |
| M1 Token consumption | context_peak | n/a | 71435 |
| M1 Token consumption | start_context | n/a | n/a |
| M1 Token consumption | main_calls | n/a | n/a |
| M1 Token consumption | main_tokens_post_exec | n/a | n/a |
| M1 Token consumption | main_cache_write | n/a | n/a |
| M1 Token consumption | cost_usd | 25.056 | 4.51 |
| M1 Token consumption | cost_main_usd | 10.721 | 1.967 |
| M1 Token consumption | cost_subagents_usd | 14.48 | 2.592 |
| M1 Token consumption | cache_hit_rate | n/a | 0.935 |
| M1 Token consumption | output_share | n/a | 0.014 |
| M1 Token consumption | tokens_per_task | n/a | 3954757 |
| M2 Tasks completed successfully | tasks_planned | 8 | 1 |
| M2 Tasks completed successfully | tasks_done | 8 | 1 |
| M2 Tasks completed successfully | hidden_passed | 34 | 7 |
| M2 Tasks completed successfully | hidden_total | 37 | 7 |
| M2 Tasks completed successfully | completed | 5 | 1 |
| M3 Total time | wall_min | 72.2 | 14.727 |
| M4 Time per run | wall_min | 72.2 | 14.727 |
| M4 Time per run | main_min | 28.779 | 4.716 |
| M4 Time per run | agent_min | 47.185 | 7.993 |
| M4 Time per run | cold_starts | 32 | 6 |
| M4 Time per run | min_to_docs | n/a | 5.215 |
| M4 Time per run | min_to_code | n/a | 12.032 |
| M4 Time per run | min_per_task | n/a | 10.151 |
| M4 Time per run | main_only_min | n/a | n/a |
| M4 Time per run | parallel_factor | n/a | n/a |
| M5 Error rate | tool_calls | 925 | 165 |
| M5 Error rate | tool_errors | 26 | 5 |
| M5 Error rate | error_rate | n/a | 0.031 |
| M5 Error rate | gate_runs_main | 12 | 2 |
| M5 Error rate | gate_runs_sub | 27 | 5 |
| M5 Error rate | gate_fail_ratio | n/a | 0.143 |
| M5 Error rate | rereads | 16 | 2 |
| M5 Error rate | rework_actions | n/a | n/a |
| M5 Error rate | max_reruns_per_step | n/a | n/a |
| M5 Error rate | ceremony_ratio | n/a | n/a |
| M5 Error rate | error_kinds.gate_check | 7 | 1 |
| M5 Error rate | error_kinds.environment | 8 | 2 |
| M5 Error rate | error_kinds.missing_file | 5 | 1 |
| M5 Error rate | error_kinds.test_failure | 3 | 0 |
| M5 Error rate | error_kinds.other | 9 | 2 |
| M6 Implementation versus plan | plan_coverage | n/a | 1 |
| M6 Implementation versus plan | plan_drift | n/a | 0 |
| M6 Implementation versus plan | tasks_per_executor | n/a | 0.25 |
| M6 Implementation versus plan | first_pass_rate | n/a | 1 |
| M6 Implementation versus plan | first_pass | n/a | 1 |
| M6 Implementation versus plan | review_rounds | 8 | 1 |
| M6 Implementation versus plan | blind_findings_total | 6 | 2 |
| M6 Implementation versus plan | review_weighted | n/a | 2.198 |
| M6 Implementation versus plan | accept | n/a | 1 |
| M7 Output quality | prd_fidelity | n/a | 1 |
| M7 Output quality | conflict_found | n/a | 1 |
| M7 Output quality | contradiction_left | n/a | 0 |
| M7 Output quality | gap_recorded | n/a | 1 |
| M7 Output quality | traceability | n/a | 1 |
| M7 Output quality | single_source | n/a | 11 |
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
| FLOW-FAST S5 r1 | 4570676 | 4570676 | 1 | 1 | 10.151 | 2.896 | 7.993 | 6 | 0.012 | 1 | 1 |
| FLOW-FAST S5 r2 | 3954757 | 3954757 | 1 | 1 | 11.431 | 4.049 | 7.982 | 5 | 0.031 | 1 | 1 |
| FLOW-FAST S5 r3 | 4003767 | 2001883.5 | 2 | 2 | 14.727 | 6.676 | 8.051 | 6 | 0.024 | 1 | 1 |
| FLOW-FAST S7 r1 | 4490362 | 4490362 | 1 | 1 | 18.125 | 10.442 | 7.683 | 6 | 0.038 | 1 | 1 |
| FLOW-FAST S8 r1 | 7120114 | 2373371.333 | 3 | 3 | 17.765 | 4.716 | 15.475 | 9 | 0.033 | 1 | 0.667 |

## Runs

| Arm and scenario | Found | Expected | Missing |
|---|---|---|---|
| SK.S5 | 0 | 3 | 3 |
| SK.S7 | 0 | 1 | 1 |
| SK.S8 | 0 | 1 | 1 |
| LT.S5 | 0 | 3 | 3 |
| LT.S7 | 0 | 1 | 1 |
| LT.S8 | 0 | 1 | 1 |

## Hard gates

- FAIL: Q1 accept: LT mean at least SK (LT None, SK None)
- FAIL: Q2 suite_green: true in every LT run (0 of 0)
- FAIL: Q3 gate_ok: true in every LT run (0 of 0)
- FAIL: Q4 completed: true in every LT run (0 of 0)
- FAIL: F1 prd_fidelity: LT at least SK minus 0.05 (LT None, SK None)
- FAIL: R4 protocol_adherence: 1.0 in every LT run (0 of 0)

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

- FAIL: hard gates
- FAIL: E1, E2, E3 win or tie on S1 and S2 ({"S1.tokens_total": null, "S1.cost_usd": null, "S1.wall_min": null, "S2.tokens_total": null, "S2.cost_usd": null, "S2.wall_min": null})
- PASS: losses do not exceed wins in each group

Result: LT is not adopted.

10 run(s) are missing; medians use only the runs present.


## Efficiency analysis

Median per arm over the runs of the scope; `#n` is the rank of the arm on that metric (1 is best, none for descriptive metrics).

### X1 Token consumption

| Metric | Scope | FLOW-FAST |
|---|---|---|
| tokens_total | all | 4490362 #1 |
| tokens_total | M | 4490362 #1 |
| tokens_main | all | 2007328 #1 |
| tokens_main | M | 2007328 #1 |
| tokens_subagents | all | 2333431 #1 |
| tokens_subagents | M | 2333431 #1 |
| context_peak | all | 71435 #1 |
| context_peak | M | 71435 #1 |
| cost_usd | all | 4.51 #1 |
| cost_usd | M | 4.51 #1 |

### X2 Efficiency of the subagents

| Metric | Scope | FLOW-FAST |
|---|---|---|
| subagents | all | 6 |
| subagents | M | 6 |
| subagent_tokens_median | all | 550341 #1 |
| subagent_tokens_median | M | 550341 #1 |
| subagent_tool_calls_median | all | 31.5 #1 |
| subagent_tool_calls_median | M | 31.5 #1 |
| subagent_errors | all | 4 #1 |
| subagent_errors | M | 4 #1 |
| subagents_wasted | all | 0 #1 |
| subagents_wasted | M | 0 #1 |
| tasks_per_executor | all | 0.25 #1 |
| tasks_per_executor | M | 0.25 #1 |
| subagent_token_share | all | 0.565 |
| subagent_token_share | M | 0.565 |

### X3 Error rate during implementation

| Metric | Scope | FLOW-FAST |
|---|---|---|
| tool_calls | all | 165 |
| tool_calls | M | 165 |
| tool_errors | all | 5 #1 |
| tool_errors | M | 5 #1 |
| error_rate | all | 0.031 #1 |
| error_rate | M | 0.031 #1 |
| test_runs | all | 12 |
| test_runs | M | 12 |
| failed_test_runs | all | 2 #1 |
| failed_test_runs | M | 2 #1 |
| kit_self_fixes | all | 0 #1 |
| kit_self_fixes | M | 0 #1 |

### X4 Time to complete

| Metric | Scope | FLOW-FAST |
|---|---|---|
| wall_min | all | 14.727 #1 |
| wall_min | M | 14.727 #1 |
| min_to_code | all | 12.032 #1 |
| min_to_code | M | 12.032 #1 |
| min_per_task | all | 10.151 #1 |
| min_per_task | M | 10.151 #1 |

### X5 Reviews needed for good code

| Metric | Scope | FLOW-FAST |
|---|---|---|
| review_rounds | all | 1 #1 |
| review_rounds | M | 1 #1 |
| review_fix_commits | all | 2 #1 |
| review_fix_commits | M | 2 #1 |
| blind_findings_total | all | 2 #1 |
| blind_findings_total | M | 2 #1 |

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
| blind_low | all | 0 #1 |
| blind_low | M | 0 #1 |
| blind_approve | all | 1 #1 |
| blind_approve | M | 1 #1 |
