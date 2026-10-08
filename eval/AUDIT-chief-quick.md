# Audit: round 2026-10-08-chief, quick tier

Scope: 2 runs in `eval/results/2026-10-08-chief/` (FLOW-FAST, S5 and S8, 1 rep each, `eval/arms-min.json`), kit at `a3a954f` on `fix/prd-flow-cost` (contract v6, the chief, with the review 1/5 and 2/5 fixes; the predictions were written for `5d14a4d`). Both runs ended `ok`, no 429, no session limit (EA7 not triggered). Spend: US$13.49 of the US$20 approved (5.67 + 7.81). Numbers come from `rounds.py`, `agents_report.py`, `transcript.summarize_phases` and small scripts over the transcripts; full outputs, local and git-ignored: `eval/results/2026-10-08-chief/rounds-vs-short-FLOW-FAST.md`, `rounds-vs-big-GATE.md`, `agents.md`.

## Scorecard

Candidate `2026-10-08-chief:FLOW-FAST` against `2026-10-08-short:FLOW-FAST` (pre-chief, same arm; S5 is the median of 3 reps, the candidate has 1) and `2026-10-08-big:GATE` (adoption baseline; S5 median of 3). The chief fields for every column were recomputed from the transcripts because `rounds.py` reports them as "no data" (metric defect D1 below).

| Metric | Scn | Chief | Short | Delta vs short | GATE | Delta vs GATE | Verdict |
|---|---|---|---|---|---|---|---|
| tokens_main | S5 | 1.03M | 1.64M | -36.9% | 3.82M | -72.9% | win |
| tokens_main | S8 | 1.02M | 2.13M | -51.9% | 6.84M | -85.0% | win |
| tokens_total | S5 | 5.45M | 4.00M | +36.1% | 6.77M | -19.5% | loss vs short |
| tokens_total | S8 | 8.57M | 7.12M | +20.4% | 9.67M | -11.4% | loss vs short |
| cost_usd | S5 | 5.67 | 4.50 | +26.2% | 5.77 | -1.7% | loss vs short |
| cost_usd | S8 | 7.81 | 6.29 | +24.1% | 7.89 | -1.0% | loss vs short |
| cost_per_accept | S5 | 0.811 | 0.642 | +26.3% | 0.824 | -1.6% | loss vs short (adoption band +10%: FAIL) |
| cost_per_accept | S8 | 0.868 | 1.049 | -17.3% | 0.876 | -0.9% | win (accept went up) |
| wall_min (graded) | S5 | 21.5 | 11.4 | +88.3% | 16.2 | +33.2% | loss (biased base, see b) |
| wall_min (graded) | S8 | 25.8 | 17.8 | +45.1% | 17.5 | +47.6% | loss (biased base) |
| runner_wall_min | S5 | 21.6 | 14.7 | +47.1% | 16.2 | +33.1% | loss |
| runner_wall_min | S8 | 25.8 | 22.5 | +15.0% | 17.5 | +47.3% | loss |
| accept (hidden) | S5 | 1.0 (7/7) | 1.0 | 0 | 1.0 | 0 | tie |
| accept (hidden) | S8 | 1.0 (9/9) | 0.667 (6/9) | +0.333 | 1.0 | 0 | win vs short |
| error_rate | S5 | 0.062 | 0.024 | x2.6 | 0.035 | x1.8 | loss |
| error_rate | S8 | 0.045 | 0.033 | x1.4 | 0.016 | x2.8 | loss |
| main_violations | S5, S8 | 0, 0 | 1, 6 | to 0 | 39.5, 63 | to 0 | win |
| chief_violations | S5, S8 | 1, 1 | 26, 31 (pre-chief, not bound) | n/a | 53, 85 | n/a | hard gate FAIL (0 required) |
| return_compliance | S5, S8 | 1.0 (11/11), 1.0 (10/10) | 0.0 | n/a | 0.0 | n/a | pass |
| surveyor_first | S5, S8 | true, true | true | n/a | false | n/a | pass |

Headline: cost per accepted task S5 0.811 (short 0.642, +26%; GATE 0.824, -2%); S8 0.868 (short 1.049, -17%, only because S8 went from 6/9 to 9/9). Wall time per accepted task on `runner_wall_min`: S5 21.6 min (short 14.7, +47%; GATE 16.2, +33%); S8 25.8 min (short 33.7 = 22.5 / 0.667, -23%; GATE 17.5, +47%). The chief bought a leaner main thread (main tokens -37% to -52%) with more total tokens, more cost and much more wall time: by M07 that is not a gain.

Adoption (`rounds.py`, M07): FAIL against short (S5 `cost_per_accept` +26%, S5 `wall_min` +88%; groups M3, M4, M5, M7 lose) and FAIL against GATE (S5 `wall_min` +33%; M3 to M6 lose). Hard gates hold except `chief_violations 0` (1 in each run), which `rounds.py` cannot see.

## Predictions (single rep: only S5 and S8 parts)

| ID | Met when | Measured | Verdict |
|---|---|---|---|
| P1 | `chief_violations` median 0, max at most 2 (5 runs) | 1 and 1 | Cannot decide (needs S5 x3 and S7). Max holds so far; median 0 needs all 3 remaining runs at 0. Same single cause in both runs (C2) |
| P2 | `return_compliance` median at least 0.9, min at least 0.75 | 1.0 and 1.0 | Met on both runs measured; final needs the other 3 |
| P3 | `surveyor_first` true in 5 of 5 | 2 of 2 | Met so far; cannot decide 5 of 5 |
| P4 | S5 median at most 1.31M and S8 at most 1.70M | S5 1.03M (1 rep), S8 1.02M | S8 part met (decidable); S5 median cannot be decided from 1 rep (the rep is below) |
| P5 | total cost of 5 runs 22.55 to 28.82 | 13.49 for 2 runs; the same 2 pairs in short: 10.79 (+25%) | Cannot decide; trending above the +15% ceiling |
| P6 | S5 median at most 13.1 and S8 at most 20.5 (`wall_min`) | S5 21.5 (1 rep), S8 25.8 | **Missed** (the S8 half decides it). On `runner_wall_min` the corrected S8 threshold is 25.8 (22.45 x 1.15) and S8 sits on it (25.82) |
| P7 | S5 median 1.0, S7 1.0, S8 at least 0.667 | S5 1.0, S8 1.0 | S8 part met; S5 median and S7 cannot be decided |
| P8 | `conflict_recall` 1.0 in 3 of 3 (S5) | 1.0 in 1 of 1 | Cannot decide |

One prediction decided (P6, missed); P4 and P7 met on their S8 halves; the rest need the confirm tier. EA5 is not triggered: the short round hit 6 of 10 of its own predictions.

## Answers to the caller

### (a) S8 hidden tests: 9 of 9, up from 6 of 9. Not attributable to contract v6.
- The three pre-chief failures were exactly the express tests (`test_express_costs_a_flat_fee`, `..._never_free_above_the_free_shipping_amount`, `..._the_same_for_a_vip`): rerun on the short build, `shipping` was 15.00 or 0.00 where 25.00 was expected.
- Cause, from the short transcript: the phase-1 surveyor read "costs a flat 25.00" as "an optional flat 25.00 surcharge on top" of normal shipping and concluded "Conflicts: none ... express is an added surcharge, not the shipping fee, so nothing becomes false". Docs wrote SHP-03 "surcharge ... added on top of normal shipping", CHK-01 "plus any express surcharge" and a new `express` Receipt field (also against "no new public name besides the choice and the points field"). The executors implemented that PRD faithfully. It was a phase-1 interpretation error, not an execution error.
- In the chief run the surveyor's unconditional-rule check found SHP-01 and SHP-02 made false by express and rewrote them; docs wrote SHP-03 "when chosen, shipping is a flat 25.00" and CHK-09 "no public name is added besides the express choice and the points field". Hidden tests 9/9.
- The big round had S8 at 9/9 in all three arms (GATE, FLOW, FLOW-FAST, pre-v6). So S8 is 9/9 in 4 of 5 runs and the short 6/9 is the outlier. One rep cannot credit v6 (its surveyor now prepares every question and `impact.md` grew), and the surveyor's reading of "costs a flat" stays a variance risk: no question round forces "replaces or adds to shipping?".

### (b) `wall_min` and `runner_wall_min`: what the gap is and which to use
- `wall_min` sums `duration_ms` over the `result` events of each session. `runner_wall_min` is the runner's clock around both sessions (`run.py` `started_at` to the end of the sessions; build, judge and grading are outside it).
- When the main dispatches agents with `run_in_background` and ends its turn, the session emits several `result` events, and each `duration_ms` covers only an active turn. The minutes the main sits idle while the background agents work are in no `result`. Short round, phase 2: S5-r1 had 4 background dispatches and 5 results, 3.10 min summed against 7.34 min of session span (from the transcript timestamps); S8 had 3 background dispatches and 4 results, 7.26 against 11.68. Those are the 4.5 and 4.7 min gaps. S5-r3 (0 background dispatches, 1 result per session): gap 0.08. In the chief round the chief dispatched nothing in the background, one result per session, gaps 0.04 and 0.05.
- The remaining 0.04 to 0.5 min is CLI start and the step between the phases.
- The agents keep working in those idle minutes, so they are real elapsed time. `wall_min` under-counts exactly the runs that use background agents and flatters them (metric defect D2, EA3). **The scorecard should use `runner_wall_min`** (or the sum of the session spans) until `wall_min` is fixed; the predictions and `adoption.py` use `wall_min`. On `runner_wall_min` the chief regression is +47% on S5 and +15% on S8 against short, not +88% and +45%.

## Where the time and money went (cause, from the transcripts)

Cost by role (`cost_by_role`, transcript, scaled to the reported cost):

| Role | S5 chief | S5 short r1 / r2 / r3 | S8 chief | S8 short |
|---|---|---|---|---|
| main | 1.28 | 1.92 / 1.72 / 1.97 | 1.31 | 2.11 |
| surveyor | 1.00 | 0.82 / 0.64 / 0.68 | 1.38 | 0.91 |
| docs | 1.85 (3 dispatches) | 1.04 / 1.34 / 0.97 | 2.80 (3 dispatches) | 1.47 (1 dispatch) |
| executor | 1.12 (5 dispatches) | 0.47 / 0.38 / 0.59 | 1.93 (4) | 1.23 (4) |
| reviewer | 0.42 (2) | 0.24 / 0.27 / 0.28 | 0.40 (2) | 0.52 (2) |

| # | Cause | Evidence | Measured cost |
|---|---|---|---|
| C1 | Docs runs as 3 cold dispatches (`rules`, `prd`, `trd-plan`) where short ran 1 | Both runs: `prd` stopped with `Route: user:` to confirm intro prose (S5 "shipping intro rewritten", S8 "new Loyalty section and intro prose"), so `trd-plan` started cold and reread 13 to 17 files. `rules` (closing the interview, the main's work before v6) is a separate start too | Docs S5 +0.81 USD, 5.3 min of agent time against 2.4; S8 +1.33 USD, 7.4 min against 3.4. The `trd-plan` start alone: S5 0.83 USD, 3.0 min; S8 1.09 USD, 3.1 min |
| C2 | The close lost its own output, then re-closed into a false "baseline missing" | S5 close executor: ran promote, did not commit it (card step 1), redirected `gates.sh close` into `state/<slug>/close-gate-out.txt`; close passed (exit 0) and deleted the state folder with the file in it; the executor reran close, which now found no baseline. Two extra executor dispatches followed (`Fix missing baseline`, `Run compare gate`) | 3 dispatches instead of 1, about 1.5 min with gaps, 0.10 USD; the delivered S5 tree has the promote uncommitted (`git status`: 3 renames, 3 modified PRD files) while `promoted` reads true |
| C3 | Surveyor slower and costlier | v6 surveyor prepares every question round and sweeps every PRD (`impact.md` reference grew by 132 lines) | S5 3.3 min against 1.8; S8 4.2 against 2.4; +0.18 to +0.47 USD |
| C4 | Main-only time did not shrink with the main's calls | Main calls 23 and 22 against 28 to 41, but main-only time is S5 6.2 min (short 2.9 to 6.7) and S8 4.3 (4.7): the chief's time is per dispatch (one thinking turn plus a cold start), so more dispatches cost time even when each turn is small | 11 and 10 dispatches against 5 to 9 |
| C5 | One review per wave on a serial plan | S5 plan: 2 waves of width 1, each reviewed (2 reviewer starts against 1 in short r1 and r2) | +0.18 USD, about 1.3 min plus a gap |
| C6 | `promote.py` treats an open question as a rule | S8: `promote: ERROR 1 approved rule(s) have no Source line: Q-LOY-01`; the close executor fixed it inside its run | 1 failed promote plus recovery calls in every C5 with an open question |
| C7 | Agents try to commit the git-ignored state | 4 `git add .claude/prd-flow` errors across the two runs; with C6, the gate format errors and missing-file reads, error_rate is 0.062 and 0.045 | error_rate x1.4 to x2.6 |

## Subagent and context checklist

| Check | S5 | S8 | Flag |
|---|---|---|---|
| Dispatch map | surveyor, docs x3, executor x2, reviewer x2, close, 2 recovery | surveyor, docs x3, executor x3, reviewer x2, close | docs split (C1); S5 close recovery (C2) |
| Agents per change | 11 for 2 tasks (plan needs about 7) | 10 for 3 tasks (about 9) | yes, S5 |
| Main residency | 23 calls, 1.03M tokens, 0.40M after the first executor; reads: `repo.md`, `state.md`, `plan.md` once | 22 calls, 1.02M, 0.28M after the first executor; same reads | `plan.md` read at the phase-2 resume: the only chief violation in each run |
| Prompt in | 180 to 989 characters | 194 to 1,411 | none |
| Return out | 3 of 11 over 2,000 (surveyor 2,342, docs 2,095, reviewer 3,758) | 5 of 10 (surveyor 3,376, docs 2,236 and 3,275, reviewers 3,138 and 2,807) | yes |
| Agent reads | max 18 files, 2 rereads | max 22 files, 1 reread | none |
| Loops | 2 close runs (C2) | none | S5 |
| Cold starts | 2 executor starts for 3 calls each (C2) | none under 10 calls | S5 |
| Parallelism | serial plan by shape | wave 1 width 2, `parallel_factor` 1.16 | below the 1.5 target on S8 |
| Model by role | opus surveyor and docs, sonnet executor and reviewer | same | none |
| Cache | 0 busts | 0 busts | none |
| Closing | 3 dispatches after the last reviewer | 1 | S5 (C2) |

## Metric defects (EA3)

| # | Defect | Evidence | Effect |
|---|---|---|---|
| D1 | `chief_violations`, `return_compliance`, `surveyor_first` never reach `rounds.py`: `grade.py` does not write them to `metrics.json` and `six.FLOW_KEYS` does not fill them from the transcript | `transcript.summarize_phases` returns 1 / 1.0 / true for S5; `rounds.py` prints "N/A ... no data" for all three hard gates | The C6-07 hard gates are never enforced: this round passes them on paper while `chief_violations` is 1 in each run |
| D2 | `wall_min` drops the idle minutes of sessions with background agents | (b) above | Under-counts by up to 4.7 min; flatters background dispatching; the short baseline and P6 are biased low |
| D3 | `agents_report.py` sums the cumulative `modelUsage` of every `result` event | Short S5-r1 phase 2: 5 results each carrying 1.50 USD, report total 10.50 against a real 4.51 | The cost column is wrong for any multi-result session (whole short round); its main `minutes` share D2 |
| D4 | `waves` counts close and recovery executor dispatches as waves | S5 `waves` 4 for a 2-wave plan; S8 `wave_widths` [2, 1, 1], `waves_match` false for a plan of 2 waves | False `waves_match` misses |
| D5 | `promoted` reads the working tree, not the history | S5 promote left uncommitted, `promoted` true | Hides C2's delivery defect |

## Ranked fixes (agent management and context first)

| # | Fix | Removes | Metric moved, expected size | Effort |
|---|---|---|---|---|
| 1 | Docs runs `rules`, `prd` and `trd-plan` in one dispatch; the prose confirmation joins the wave-table approval in one question round (a change is a `prd adjust` or `trd-plan adjust` dispatch) | C1 | Two cold docs starts per C5: about -0.8 USD (S5) and -1.3 USD (S8), -3 to -5 min of wall (measured docs excess over short) | Docs card modes and SKILL steps 3 to 5 |
| 2 | Close: executor reads the `gates.sh close` stdout or writes it under `.ai-kit/runs/`, never inside the state folder; promote is committed before close; `close_gate.py` refuses a dirty `docs/` or `changes/` (owner executor) and prints "already closed" when the state is gone and the change is archived | C2, D5 | S5: -2 dispatches, about -1.5 min, -0.10 USD; promote always committed | Executor card step 3, about 15 lines in `close_gate.py` |
| 3 | Fix D1 and D2 in the eval before the confirm tier: chief fields into `FLOW_KEYS`/`metrics.json`; `wall_min` from the session span or `runner_wall_min` | D1, D2 | Hard gates enforced; wall comparisons unbiased (up to 4.7 min per run) | Small, eval code |
| 4 | Docs `trd-plan` writes the plan path and the task IDs of each wave into `## Plan` of `state.md`, so the resumed chief needs no `plan.md` | P1 cause in both runs | `chief_violations` 1 to 0 per run (hard gate) | One line in the docs card and the chief's resume line |
| 5 | A serial plan of width-1 waves gets one review after the last wave (review per wave only when a wave has 2 or more tasks or a later wave depends on findings) | C5 | S5: -1 reviewer start, about -0.2 USD, -1.5 min | `execution.md` and the chief card |
| 6 | Surveyor question round always asks "does the new option replace or add to the existing amount?" when a new fee meets an existing fee rule | (a) variance | S8 accept stays 9/9 instead of depending on the reading | One row in `interview.md` dimensions |
| 7 | `promote.py` skips `Q-` rows (they live in the PRD open questions) | C6 | -1 failed promote and its recovery calls per C5 with an open question | Small script change |
| 8 | Cards state that `.claude/prd-flow/` is never committed | C7 | error_rate: -4 errors over 2 runs (about -1 point) | One line in the executor and docs cards |
| 9 | Enforce the 2,000-character return cap: findings and surveys go to their file, the return holds counts and the path | 8 of 21 returns over the cap | Small chief-token gain (chief tokens are already 1.0M) | Surveyor, docs, reviewer cards |
| 10 | Fix D3 and D4 in `agents_report.py` and `transcript.py` | D3, D4 | Correct per-role cost and `waves_match` | Small, eval code |

## Verdict
Contract v6 does what it promised in the main thread (main tokens -37% and -52%, `main_violations` 0, returns 100% compliant, the surveyor first), but the work it moved out costs more than it saved: cost +24% to +26% and wall time +15% to +47% against the pre-chief arm, so M07 fails and P6 misses. The excess comes from dispatch shape (3 cold docs starts, a close that lost its output, a review per serial wave), so the next step is fixes 1 to 4 and a new quick round, not the confirm tier.
