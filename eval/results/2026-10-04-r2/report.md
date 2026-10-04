# Evaluation report

Candidate LT versus base SKF.

## Runs

| Arm and scenario | Found | Expected | Missing |
|---|---|---|---|
| SKF.S1 | 2 | 2 | 0 |
| SKF.S2 | 1 | 2 | 1 |
| SKF.S3 | 0 | 1 | 1 |
| SKF.S4 | 0 | 1 | 1 |
| LT.S1 | 2 | 2 | 0 |
| LT.S2 | 1 | 2 | 1 |
| LT.S3 | 0 | 1 | 1 |
| LT.S4 | 0 | 1 | 1 |

## Hard gates

- PASS: Q1 accept: LT mean at least SKF (LT 1.0, SKF 1.0)
- PASS: Q2 suite_green: true in every LT run (3 of 3)
- PASS: Q3 gate_ok: true in every LT run (3 of 3)
- PASS: Q4 completed: true in every LT run (3 of 3)
- FAIL: F1 prd_fidelity: LT at least SKF minus 0.05 (LT 0.7301587301587301, SKF 0.8412698412698413)
- PASS: R4 protocol_adherence: 1.0 in every LT run (3 of 3)

## Scorecard S1

| Metric | Group | LT | SKF | Band | Verdict |
|---|---|---|---|---|---|
| tokens_total | tokens | 1975775 | 4311930 | 526716 | win |
| context_peak | tokens | 76953.5 | 119414.5 | 11941.45 | win |
| wall_min | speed | 4.065 | 7.153 | 0.983 | win |
| min_to_code | speed | 3.869 | 6.428 | 0.643 | win |
| turns | speed | 42 | 64.5 | 6.45 | win |
| cost_usd | efficiency | 2.384 | 4.389 | 0.439 | win |
| cost_per_accept | efficiency | 0.341 | 0.627 | 0.063 | win |
| doc_bytes | efficiency | 1343.5 | 21307 | 2130.7 | win |
| rework_commits | rework | 0 | 0 | 0 | tie |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | n/a | n/a | n/a | n/a |
| plan_drift | plan_fidelity | n/a | n/a | n/a | n/a |
| traceability | source_fidelity | 1 | 1 | 0.1 | tie |
| docs_first | source_fidelity | 1 | 1 | 0.1 | tie |
| promoted | source_fidelity | 1 | 1 | 0.1 | tie |
| single_source | source_fidelity | 5 | 43.5 | 7 | win |
| tool_errors | errors | 1 | 1.5 | 1 | tie |
| error_rate | errors | n/a | n/a | n/a | n/a |
| subagent_tokens_median | subagents | n/a | n/a | n/a | n/a |
| subagent_errors | subagents | n/a | n/a | n/a | n/a |
| subagents_wasted | subagents | n/a | n/a | n/a | n/a |
| tasks_per_executor | subagents | n/a | n/a | n/a | n/a |
| review_rounds | reviews | n/a | n/a | n/a | n/a |
| review_fix_commits | reviews | n/a | n/a | n/a | n/a |
| blind_findings_total | reviews | n/a | n/a | n/a | n/a |
| blind_approve | reviews | n/a | n/a | n/a | n/a |
| accept | code_quality | 1 | 1 | 0.1 | tie |
| suite_green | code_quality | 1 | 1 | 0.1 | tie |
| blind_bugs | code_quality | n/a | n/a | n/a | n/a |
| blind_critical | code_quality | n/a | n/a | n/a | n/a |
| blind_high | code_quality | n/a | n/a | n/a | n/a |

## Scorecard S2

| Metric | Group | LT | SKF | Band | Verdict |
|---|---|---|---|---|---|
| tokens_total | tokens | 10066897 | 12524063 | 1252406.3 | win |
| context_peak | tokens | 164201 | 184306 | 18430.6 | win |
| wall_min | speed | 16.904 | 15.888 | 1.589 | tie |
| min_to_code | speed | 11.96 | 10.504 | 1.05 | loss |
| turns | speed | 92 | 117 | 11.7 | win |
| cost_usd | efficiency | 8.302 | 10.906 | 1.091 | win |
| cost_per_accept | efficiency | 1.038 | 1.363 | 0.136 | win |
| doc_bytes | efficiency | 16975 | 34465 | 3446.5 | win |
| rework_commits | rework | 0 | 1 | 0.1 | win |
| kit_self_fixes | rework | 0 | 0 | 0 | tie |
| plan_coverage | plan_fidelity | 1 | 0.636 | 0.064 | win |
| plan_drift | plan_fidelity | 0 | 0 | 0 | tie |
| traceability | source_fidelity | 1 | 1 | 0.1 | tie |
| docs_first | source_fidelity | 1 | 1 | 0.1 | tie |
| promoted | source_fidelity | 1 | 1 | 0.1 | tie |
| single_source | source_fidelity | 12 | 15 | 1.5 | win |
| tool_errors | errors | 1 | 1 | 0.1 | tie |
| error_rate | errors | n/a | n/a | n/a | n/a |
| subagent_tokens_median | subagents | n/a | n/a | n/a | n/a |
| subagent_errors | subagents | n/a | n/a | n/a | n/a |
| subagents_wasted | subagents | n/a | n/a | n/a | n/a |
| tasks_per_executor | subagents | n/a | n/a | n/a | n/a |
| review_rounds | reviews | n/a | n/a | n/a | n/a |
| review_fix_commits | reviews | n/a | n/a | n/a | n/a |
| blind_findings_total | reviews | n/a | n/a | n/a | n/a |
| blind_approve | reviews | n/a | n/a | n/a | n/a |
| accept | code_quality | 1 | 1 | 0.1 | tie |
| suite_green | code_quality | 1 | 1 | 0.1 | tie |
| blind_bugs | code_quality | n/a | n/a | n/a | n/a |
| blind_critical | code_quality | n/a | n/a | n/a | n/a |
| blind_high | code_quality | n/a | n/a | n/a | n/a |

## Tally

| Group | Win | Tie | Loss |
|---|---|---|---|
| tokens | 4 | 0 | 0 |
| speed | 4 | 1 | 1 |
| efficiency | 6 | 0 | 0 |
| rework | 1 | 3 | 0 |
| plan_fidelity | 1 | 1 | 0 |
| source_fidelity | 2 | 6 | 0 |
| errors | 0 | 2 | 0 |
| subagents | 0 | 0 | 0 |
| reviews | 0 | 0 | 0 |
| code_quality | 0 | 4 | 0 |

## Adoption

- FAIL: hard gates
- PASS: E1, E2, E3 win or tie on S1 and S2 ({"S1.tokens_total": "win", "S1.cost_usd": "win", "S1.wall_min": "win", "S2.tokens_total": "win", "S2.cost_usd": "win", "S2.wall_min": "tie"})
- PASS: losses do not exceed wins in each group

Result: LT is not adopted.

## Work list

- S2 min_to_code (speed): LT 11.96, SKF 10.504

6 run(s) are missing; medians use only the runs present.


## Efficiency analysis

Median per arm over the runs of the scope; `#n` is the rank of the arm on that metric (1 is best, none for descriptive metrics).

### X1 Token consumption

| Metric | Scope | LT | SKF | SKU |
|---|---|---|---|---|
| tokens_total | all | 2123791 #1 | 4575288 #3 | 2254677 #2 |
| tokens_main | all | n/a | n/a | n/a |
| tokens_subagents | all | n/a | n/a | n/a |
| context_peak | all | 77445 #1 | 120176 #3 | 80116 #2 |
| cost_usd | all | 2.405 #1 | 4.588 #3 | 3.128 #2 |

### X2 Efficiency of the subagents

| Metric | Scope | LT | SKF | SKU |
|---|---|---|---|---|
| subagents | all | 0 | 0 | 0 |
| subagent_tokens_median | all | n/a | n/a | n/a |
| subagent_tool_calls_median | all | n/a | n/a | n/a |
| subagent_errors | all | n/a | n/a | n/a |
| subagents_wasted | all | n/a | n/a | n/a |
| tasks_per_executor | all | n/a | n/a | n/a |
| subagent_token_share | all | 0 | 0 | 0 |

### X3 Error rate during implementation

| Metric | Scope | LT | SKF | SKU |
|---|---|---|---|---|
| tool_calls | all | n/a | n/a | n/a |
| tool_errors | all | 1 #1 | 1 #1 | 1 #1 |
| error_rate | all | n/a | n/a | n/a |
| test_runs | all | n/a | n/a | n/a |
| failed_test_runs | all | n/a | n/a | n/a |
| kit_self_fixes | all | 0 #1 | 0 #1 | 0 #1 |

### X4 Time to complete

| Metric | Scope | LT | SKF | SKU |
|---|---|---|---|---|
| wall_min | all | 4.229 #1 | 7.644 #3 | 4.866 #2 |
| min_to_code | all | 4.01 #1 | 6.72 #3 | 4.692 #2 |
| min_per_task | all | n/a | n/a | n/a |

### X5 Reviews needed for good code

| Metric | Scope | LT | SKF | SKU |
|---|---|---|---|---|
| review_rounds | all | n/a | n/a | n/a |
| review_fix_commits | all | n/a | n/a | n/a |
| blind_findings_total | all | n/a | n/a | n/a |

### X6 Code with fewest problems

| Metric | Scope | LT | SKF | SKU |
|---|---|---|---|---|
| accept | all | 1 #1 | 1 #1 | 1 #1 |
| suite_green | all | 1 #1 | 1 #1 | 1 #1 |
| blind_bugs | all | n/a | n/a | n/a |
| blind_critical | all | n/a | n/a | n/a |
| blind_high | all | n/a | n/a | n/a |
| blind_medium | all | n/a | n/a | n/a |
| blind_low | all | n/a | n/a | n/a |
| blind_approve | all | n/a | n/a | n/a |
