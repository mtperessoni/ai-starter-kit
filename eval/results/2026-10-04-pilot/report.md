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
| LT.L1 | 0 | 2 | 2 |
| LT.L2 | 0 | 2 | 2 |
| LT.L3 | 0 | 2 | 2 |
| LT.L4 | 1 | 2 | 1 |
| LT.L5 | 0 | 2 | 2 |
| LT.L6 | 0 | 2 | 2 |
| LT.L7 | 0 | 2 | 2 |
| LT.L8 | 0 | 2 | 2 |

## Hard gates

- PASS: Q1 accept: LT mean at least SK (LT 1.0, SK None)
- PASS: Q2 suite_green: true in every LT run (1 of 1)
- PASS: Q3 gate_ok: true in every LT run (1 of 1)
- PASS: Q4 completed: true in every LT run (1 of 1)
- PASS: F1 prd_fidelity: LT at least SK minus 0.05 (LT 0.25, SK None)
- PASS: R4 protocol_adherence: 1.0 in every LT run (1 of 1)

## Scorecard L4

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

31 run(s) are missing; medians use only the runs present.


## Efficiency analysis

Median per arm over the runs of the scope; `#n` is the rank of the arm on that metric (1 is best, none for descriptive metrics).

### X1 Token consumption

| Metric | Scope | LT |
|---|---|---|
| tokens_total | all | 1748251 #1 |
| tokens_total | S | 1748251 #1 |
| tokens_main | all | 1124468 #1 |
| tokens_main | S | 1124468 #1 |
| tokens_subagents | all | 529253 #1 |
| tokens_subagents | S | 529253 #1 |
| context_peak | all | 84499 #1 |
| context_peak | S | 84499 #1 |
| cost_usd | all | 2.118 #1 |
| cost_usd | S | 2.118 #1 |

### X2 Efficiency of the subagents

| Metric | Scope | LT |
|---|---|---|
| subagents | all | 2 |
| subagents | S | 2 |
| subagent_tokens_median | all | 264626.5 #1 |
| subagent_tokens_median | S | 264626.5 #1 |
| subagent_tool_calls_median | all | 11.5 #1 |
| subagent_tool_calls_median | S | 11.5 #1 |
| subagent_errors | all | 0 #1 |
| subagent_errors | S | 0 #1 |
| subagents_wasted | all | 0 #1 |
| subagents_wasted | S | 0 #1 |
| tasks_per_executor | all | n/a |
| subagent_token_share | all | 0.32 |
| subagent_token_share | S | 0.32 |

### X3 Error rate during implementation

| Metric | Scope | LT |
|---|---|---|
| tool_calls | all | 45 |
| tool_calls | S | 45 |
| tool_errors | all | 0 #1 |
| tool_errors | S | 0 #1 |
| error_rate | all | 0 #1 |
| error_rate | S | 0 #1 |
| test_runs | all | 5 |
| test_runs | S | 5 |
| failed_test_runs | all | 1 #1 |
| failed_test_runs | S | 1 #1 |
| kit_self_fixes | all | 0 #1 |
| kit_self_fixes | S | 0 #1 |

### X4 Time to complete

| Metric | Scope | LT |
|---|---|---|
| wall_min | all | 5.15 #1 |
| wall_min | S | 5.15 #1 |
| min_to_code | all | 3.823 #1 |
| min_to_code | S | 3.823 #1 |
| min_per_task | all | n/a |

### X5 Reviews needed for good code

| Metric | Scope | LT |
|---|---|---|
| review_rounds | all | 1 #1 |
| review_rounds | S | 1 #1 |
| review_fix_commits | all | 0 #1 |
| review_fix_commits | S | 0 #1 |
| blind_findings_total | all | 0 #1 |
| blind_findings_total | S | 0 #1 |

### X6 Code with fewest problems

| Metric | Scope | LT |
|---|---|---|
| accept | all | 1 #1 |
| accept | S | 1 #1 |
| suite_green | all | 1 #1 |
| suite_green | S | 1 #1 |
| blind_bugs | all | 0 #1 |
| blind_bugs | S | 0 #1 |
| blind_critical | all | 0 #1 |
| blind_critical | S | 0 #1 |
| blind_high | all | 0 #1 |
| blind_high | S | 0 #1 |
| blind_medium | all | 0 #1 |
| blind_medium | S | 0 #1 |
| blind_low | all | 0 #1 |
| blind_low | S | 0 #1 |
| blind_approve | all | 1 #1 |
| blind_approve | S | 1 #1 |
