# Efficiency metrics

The single scorecard every eval round uses to judge a change to the kit (MAINTAINING.md M07). The goal: the fewest tokens, the shortest wall time, the best output, the fewest errors, never one bought by worsening another. Computed per run by `eval/run.py`, compared across rounds with `eval/rounds.py --baseline`. Sources: `proposals/efficiency-audit.md` and `eval/AUDIT-prd-flow.md`.

## Headline KPIs (one line per run)
| KPI | Definition | Target, one-rule C5 (S5) |
|---|---|---|
| Cost per accepted result | `cost_usd` over hidden tests passed (`cost_per_accept`) | at most the base |
| Wall time | `runner_wall_min` (the run clock) | at most 15 min |
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
| Parallel factor | executor agent minutes over the time at least one executor ran (`parallel_factor`; reviews and the gaps between waves are out) | at least 1.5 inside the executor segments of a wave of width 2 or more (S8 wave 1); a serial wave is 1.0 by shape, not a miss |
| Waves and width | waves dispatched and executors per wave, against the plan's computed waves | equal to the plan |
| Inline residency | tokens the main read from docs, TRD or source before the surveyor | 0 |

## Hard gates (a change failing one is not adopted)
| Gate | Definition |
|---|---|
| Behavior | hidden tests 100% |
| Consistent PRD | `contradiction_left` 0 |
| Conflict recall | the expected conflict IDs named in the surveyor's impact (`conflict_recall` 1.0) |
| Protocol | every planned step dispatched (`dispatch_map` 1.0) and `main_violations` 0 (main edits under docs/ or src/, main reads of source before the surveyor, extra main gate runs, worker-only references read by the main; kept for the GATE arm's history) |
| Chief contract (prd-flow arms, C6-07) | `chief_violations` 0, `return_compliance` 1.0, `surveyor_first` true |

## Supporting metrics (M1 to M8 of M07)
| Group | Fields |
|---|---|
| M1 Tokens and cost | `tokens_total`, `tokens_main`, `tokens_subagents`, `cost_main_usd`, `cost_subagents_usd`, `context_peak`, `cache_hit_rate`, `main_cache_write` (a single write above 30k is a cache bust), `output_share`, `tokens_per_task` |
| M2 Tasks | `tasks_done` over `tasks_planned`, `hidden_passed` over `hidden_total`, `completed` |
| M3 Total time | sum of `runner_wall_min` per arm; `wall_min` (active turns only) beside it |
| M4 Time per run | `runner_wall_min`, `wall_min`, `main_only_min`, `agent_min`, `cold_starts`, `min_to_docs`, `min_to_code`, `min_per_task` |
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
| `main_violations` | main Edit or Write under `src/`, `docs/` or `tests/` (paths relative to the project root), main reads of those before the first surveyor (carried across the phases of a two-phase run; the request's own document under `docs/incoming/` is exempt), main reads of worker-only references, and the categories counted separately (`main_source_reads`: Read, Grep or `cat` of `src/` or `tests/` after the surveyor; `main_diff_reads`: `git diff` or `git show` without `--stat` or `--name-only` after the surveyor; `kit_script_reads`: reads of `scripts/` files, `gate.py`, `promote.py`; `agent_file_edits`: main edits of `deliveries.md`, `impact.md`, `pack.md`, `execution.md`, `review.md`, `approved-rules.md`; `retro_rereads`: reads of `retro.md`), and main gate runs outside the allowed set: `--rules` once (plus reruns directly after a failed run of the same command), `gates.sh close`, `gates.sh context|baseline`, and one `--step plan` after the docs agent returned; `--step` runs otherwise belong to agents. Exempt: one Grep of `docs/prd/INDEX.md`, git config/rev-parse/log, reads of `repo.md` and of plan.md by range; None when no surveyor or executor ran |
| `chief_violations` | every chief (main thread) tool use outside Agent or Task dispatch, AskUserQuestion, Skill (loading the skill), Read, Write or Edit of `state.md`, Read of `repo.md`; every chief Bash call counts, scripts, git and gates included; None when nothing was dispatched |
| `return_compliance` | share of subagent returns (the last tool_result of each dispatch) that end with the five fields `Status`, `Files`, `Commit`, `Route`, `Next` in order (C6-02); `returns_total` and `returns_ok` are the counts; None with no returns |
| `surveyor_first` | true when the first dispatch of the run (phase 1) is the surveyor; None with no dispatch |
| `waves`, `wave_widths` | executors dispatched in one assistant message are one wave; a later dispatch opens a wave when no executor is outstanding; a fix dispatch (description names a fix) after the first wave never opens one. An executor ends at its completion (last child event, task notification or final result), not at the immediate result of a background launch |
| `parallel_factor` | executor agent minutes over the union of executor intervals (executor segments only) |
| `cost_by_role`, `cost_main_usd`, `cost_subagents_usd` | each assistant message priced by its own model (`costs.py` table) and attributed to the main or to the role of the subagent that sent it, then scaled so each model matches the result's `costUSD`; `cost_main_usd` is the `main` role, `cost_subagents_usd` the rest |
| `runner_wall_min` | the runner's clock around both sessions (build, judge and grading outside it); it includes the idle minutes of a main waiting for background agents, so it is the time the scorecard and the adoption rule use |
| `wall_min` | active turns only: sum of `duration_ms` over every `result` event of a session (a main that ends its turn while background agents run emits several), then over the phases; it misses the idle minutes of background agents, so it is a secondary column |
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
Hard gates hold; on S5 the median of 3 reps is within +10% of the base on `cost_per_accept` and `runner_wall_min`; every other metric outside the noise band (the spread of the reps) counts as a win or a loss, and wins must at least equal losses in each group.

## Agents report
`python eval/agents_report.py <results-folder> [--arm ARM] [--scenario S] [--out file.md]` prints, per run, one row per agent (main included): role, model, calls, input tokens (fresh, cache read, cache write, start write: the cache write of the agent's first call, its start cost), output tokens, cost, minutes, Read calls, distinct files, rereads, prompt and return length in characters, max context, then run totals (cost is the last `result` event of each session, since `modelUsage` is cumulative) and flags: prompt over 4000 characters, return over 2000, more than 25 files read, more than 3 rereads, more than 50 calls. Offline; it reads the `.jsonl` and `.p2.jsonl` transcripts only. Output tokens come from the stream events and understate real output, so compare the cost column instead.

## Harness
Auto-memory is off in every run: `--settings {"autoMemoryEnabled": false}` on the command, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` in the environment, and `"auto_memory": false` in each `<run>.run.json`. `traceability` ignores `DEC-nn` and `Q-nn` rows: only rule IDs count.

## Two-phase budget
A two-phase arm splits `budget_usd` between the sessions: 70% to phase 1 and 30% to phase 2 (`run.split_budget`). A phase 2 with no state folder holding `approved-rules.md` and no `changes/` folder is skipped with a `<run>.p2.skipped.txt` reason, not a crash.

## Hard gates from the transcript
`main_violations`, `chief_violations`, `return_compliance` and `surveyor_first` are written to `metrics.json` by `grade.py` and recomputed from the transcripts by `rounds.py`; all four are hard gates (0, 0, 1.0, true). `waves` and `wave_widths` count only executor task dispatches (fix, close, promote, baseline and compare-gate dispatches are not waves).
