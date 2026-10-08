# Efficiency metrics

The single scorecard every eval round uses to judge a change to the kit (MAINTAINING.md M07). The goal: the fewest tokens, the shortest wall time, the best output, the fewest errors, never one bought by worsening another. Computed per run by `eval/run.py`, compared across rounds with `eval/rounds.py --baseline`. Sources: `proposals/efficiency-audit.md` and `eval/AUDIT-prd-flow.md`.

## Headline KPIs (one line per run)
| KPI | Definition | Target, one-rule C5 (S5) |
|---|---|---|
| Cost per accepted result | `cost_usd` over hidden tests passed (`cost_per_accept`) | at most the base |
| Wall time | `wall_min` | at most 15 min |
| Main-thread calls | unique main API calls (`main_calls`) | at most 30 |
| Main-thread tokens | `tokens_main`; after the first executor dispatch (`main_tokens_post_exec`) | at most 3.5M; at most 1.5M |
| Main-only time | wall minus agent intervals (`main_only_min`) | at most 6 min |
| Total turns | main plus agent turns | at most 70 |
| Agents per change | subagents spawned, by role (`dispatch_map`) | as planned for the size, no extras |
| Rework | gate fails + review fix rounds + test or lint retries + re-dispatches (`rework_actions`) | at most 2 |
| Loops | the same gate step or command repeated (`max_reruns_per_step`) | at most 2 |
| Error rate | tool errors over tool calls, by kind | at most 2% |
| First pass | accepted with no review fix, no gate rerun after a fail, no re-dispatch (`first_pass`) | true |
| Ceremony ratio | docs and state tool calls over code and test tool calls | at most 1.0 |
| Parallel factor | agent minutes during execution over execution wall time (`parallel_factor`) | at least 1.5 on a multi-task feature (S8) |
| Waves and width | waves dispatched and executors per wave, against the plan's computed waves | equal to the plan |
| Inline residency | tokens the main read from docs, TRD or source before the surveyor | 0 |

## Hard gates (a change failing one is not adopted)
| Gate | Definition |
|---|---|
| Behavior | hidden tests 100% |
| Consistent PRD | `contradiction_left` 0 |
| Conflict recall | the expected conflict IDs named in the surveyor's impact (`conflict_recall` 1.0) |
| Protocol | every planned step dispatched (`dispatch_map` 1.0) and `main_violations` 0 (main edits under docs/ or src/, main reads of source before the surveyor, extra main gate runs, worker-only references read by the main) |

## Supporting metrics (M1 to M8 of M07)
| Group | Fields |
|---|---|
| M1 Tokens and cost | `tokens_total`, `tokens_main`, `tokens_subagents`, `cost_main_usd`, `cost_subagents_usd`, `context_peak`, `cache_hit_rate`, `main_cache_write` (a single write above 30k is a cache bust), `output_share`, `tokens_per_task` |
| M2 Tasks | `tasks_done` over `tasks_planned`, `hidden_passed` over `hidden_total`, `completed` |
| M3 Total time | sum of `wall_min` per arm |
| M4 Time per run | `wall_min`, `main_only_min`, `agent_min`, `cold_starts`, `min_to_docs`, `min_to_code`, `min_per_task` |
| M5 Errors and waste | `error_rate`, `error_kinds`, `gate_runs_main`, `gate_runs_sub`, `gate_fail_ratio`, `rereads`, `max_reruns_per_step` |
| M6 Implementation versus plan | `plan_coverage`, `plan_drift`, `first_pass_rate`, `review_rounds`, `findings_by_severity`, `review_weighted` (blind findings weighted Critical 8, High 4, Medium 2, Low 1, per 100 changed lines) |
| M7 Output quality | `prd_fidelity`, `conflict_found`, `conflict_recall`, `contradiction_left`, `gap_recorded`, `traceability`, `single_source` |
| M8 Protocol | `dispatch_map`, `main_violations`, `docs_first` |

## Definitions of the flow fields
| Field | Definition |
|---|---|
| `main_calls`, `start_context` | unique main API calls; input tokens of the first main call |
| `main_cache_write`, `cache_busts` | largest cache write of a main call after the first; calls above 30k |
| `dispatch_map` | share of the required roles (surveyor, docs, executor, reviewer) dispatched; role by `subagent_type` `prd-flow-<role>`, else by description |
| `main_violations` | main Edit or Write under `src/`, `docs/` or `tests/`, main reads of those before the first surveyor, main reads of worker-only references, main gate runs outside `--rules`, `--step plan` and `close` plus repeats of those; None when no surveyor or executor ran |
| `waves`, `wave_widths` | an executor dispatch opens a wave when no executor is outstanding; widths count executors per wave |
| `parallel_factor` | executor agent minutes over the wall time from the first executor start to the last executor end |
| `ceremony_ratio` | tool calls on docs, changes, specs and `.claude` paths over calls on `src` and `tests` paths |
| `rework_actions` | gate fails + review rounds past the first + failed test runs + re-dispatched task cards + the largest rerun count of one gate or lint command |
| `first_pass` | accepted, no review fix round, no gate rerun after a fail, no re-dispatch |
| `conflict_recall` | expected conflict IDs named in the surveyor `impact.md` over expected IDs |
| `review_weighted` | blind findings weighted 8, 4, 2, 1 per 100 changed code lines |
| Two-phase arm | phase 2 transcript is `<pair>.p2.jsonl`; costs, tokens and counts add over both phases |
| Hermetic limit | on a machine where the user-level CLAUDE.md, skills and agents still load despite `CLAUDE_CONFIG_DIR`, `start_context` shows it; `--bare` needs an API key |

## How a round runs
| Rule | Why |
|---|---|
| Hermetic: a temp `CLAUDE_CONFIG_DIR` (no personal `~/.claude`, skills, hooks or memory), pinned model and effort; the starting context is recorded | The operator's setup added 39k tokens and an output proxy to every run |
| The base arm is rerun with the same reps when the environment or model changes; otherwise its 3-rep baseline is reused | One reused sample cannot carry a noise band |
| 3 reps on the deciding scenario (S5), 1 on the others | A single run swung a round by US$2 to 3 |
| One change per round, or one ablation arm per change | Rounds that changed 2 to 6 things at once could not attribute a regression |
| A regression is explained from the transcripts before it is fixed; the fix names the metric it should move | Fixes built on unchecked premises (LS26) became the largest regressions |

## Adoption
Hard gates hold; on S5 the median of 3 reps is within +10% of the base on `cost_per_accept` and `wall_min`; every other metric outside the noise band (the spread of the reps) counts as a win or a loss, and wins must at least equal losses in each group.
