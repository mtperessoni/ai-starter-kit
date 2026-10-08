# Audit: round 2026-10-08-chief3, quick tier

Scope: 2 runs in `eval/results/2026-10-08-chief3/` (FLOW-FAST, S5 and S8, 1 rep each, `eval/arms-min.json`), kit at `4e1f191` on `fix/prd-flow-cost` (run from `39398c6`, which adds only the predictions). Changes under test: `e444830` (chief never opens the plan or runs Bash, one review variant, protected only when touched), `1d08cf0` and `4e1f191` (fold docs `rules` into `prd-plan` on a closed interview), `5f394f1` (eval `review_coverage`). Predictions: `eval/predictions/2026-10-08-chief3.md`, committed alone (`39398c6`) before the run. Spend: US$13.17 of the US$20 approved (S5 5.076, S8 8.090).

EA7: both runs ended `ok`; every rate-limit event is `allowed_warning` (seven-day window 28 to 29%, resets 2026-10-14 12:00; five-hour window reached 92% during S8 phase 2, resets 2026-10-08 15:10), no 429 and no session limit, so the round is graded. The next paid round should start after 15:10 or it risks the five-hour limit. S8 did stop early for another reason: the harness phase-2 budget cap (C3), not a usage limit.

Numbers come from `rounds.py`, `agents_report.py` and small scripts over the transcripts; full outputs, local and git-ignored: `rounds-vs-short-FLOW-FAST.md`, `rounds-vs-chief2-FLOW-FAST.md`, `rounds-vs-big-GATE.md`, `agents.md` in the round folder.

## Scorecard

Candidate `2026-10-08-chief3:FLOW-FAST` against `2026-10-08-short:FLOW-FAST` (pre-chief, kit `0019169`; S5 median of 3), `2026-10-08-chief2:FLOW-FAST` (kit `dc6f7b9`, 1 rep) and `2026-10-08-big:GATE` (adoption baseline; S5 median of 3). One rep per scenario: a single number, no spread.

| Metric | Scn | Chief3 | Short | vs short | Chief2 | vs chief2 | GATE | vs GATE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| tokens_main | S5 | 0.796M | 1.639M | -51.5% | 0.808M | -1.5% | 3.816M | -79.1% | win vs short and GATE |
| tokens_main | S8 | 1.076M | 2.127M | -49.4% | 0.809M | +33.0% | 6.838M | -84.3% | loss vs chief2 (C4) |
| tokens_total | S5 | 4.876M | 4.004M | +21.8% | 4.475M | +9.0% | 6.771M | -28.0% | loss vs short and chief2 |
| tokens_total | S8 | 7.616M | 7.120M | +7.0% | 7.606M | +0.1% | 9.671M | -21.2% | loss vs short |
| cost_usd | S5 | 5.076 | 4.495 | +12.9% | 4.854 | +4.6% | 5.770 | -12.0% | loss vs short |
| cost_usd | S8 | 8.090 | 6.293 | +28.6% | 7.077 | +14.3% | 7.887 | +2.6% | loss, and without a close (C3) |
| cost_per_accept | S5 | 0.725 | 0.642 | +12.9% | 0.693 | +4.6% | 0.824 | -12.0% | FAIL vs short (band +10%) |
| cost_per_accept | S8 | 0.899 | 1.049 | -14.3% | 0.786 | +14.4% | 0.876 | +2.6% | loss vs chief2 and GATE |
| runner_wall_min | S5 | 16.09 | 14.66 | +9.8% | 17.05 | -5.6% | 16.21 | -0.7% | PASS vs short (just inside +10%) |
| runner_wall_min | S8 | 27.40 | 22.45 | +22.1% | 22.67 | +20.9% | 17.53 | +56.3% | loss on every baseline |
| wall_min (active turns) | S5, S8 | 16.04, 27.35 | 11.43, 17.77 | +40%, +54% | 17.00, 22.62 | -6%, +21% | 16.16, 17.47 | -1%, +57% | secondary |
| accept (hidden) | S5, S8 | 1.0 (7/7), 1.0 (9/9) | 1.0, 0.667 | tie, win | 1.0, 1.0 | tie | 1.0, 1.0 | tie | pass |
| error_rate | S5 | 0.032 | 0.024 | +33% | 0.049 | -35% | 0.035 | -9% | win vs chief2 |
| error_rate | S8 | 0.029 | 0.033 | -12% | 0.029 | 0 | 0.016 | x1.8 | loss vs GATE |
| main_violations | S5, S8 | 0, 0 | 1, 6 | to 0 | 0, 0 | 0 | 52, 85 | to 0 | pass |
| chief_violations | S5, S8 | 1, 1 | not bound | n/a | 2, 2 | -1 each | not bound | n/a | **hard gate FAIL** |
| review_coverage | S5, S8 | 1.0, n/a | n/a | n/a | n/a | n/a | n/a | n/a | S8 n/a is a metric defect (D8); 2 of 2 by transcript |
| return_compliance | S5, S8 | 1.0, 1.0 | 0.0 | n/a | 1.0 | 0 | 0.0 | n/a | pass |
| surveyor_first | S5, S8 | true, true | true | n/a | true | 0 | false | n/a | pass |

Headline: cost per accepted task S5 0.725 (short 0.642, +12.9%, outside the band; chief2 +4.6%; GATE -12%), S8 0.899 (chief2 0.786, +14.4%; GATE 0.876, +2.6%) and S8 never ran its close, so its true cost is higher. Wall time per accepted task on `runner_wall_min`: S5 16.09 (short +9.8%, inside the band by 0.04 min; chief2 -5.6%), S8 27.40 (chief2 +20.9%, GATE +56%). No row moved both cost and wall time the right way against chief2 except S5 wall, and S8 lost both.

Adoption (`rounds.py`, M07): FAIL against short (hard gate `chief_violations`; S5 `cost_per_accept` +13%; M3, M4, M7 lose). FAIL against chief2 (hard gate; M1, M3, M4, M6, M7 lose; S5 cost and wall inside the band). FAIL against GATE (hard gate; M3, M4, M5, M6 lose; S5 cost -12% and wall -1%).

## Predictions

| ID | Met when | Measured | Verdict |
|---|---|---|---|
| P1 | `chief_violations` 0 in both runs | 1 and 1 | **Missed** (down from 2 and 2; C1, C2) |
| P2 | `review_coverage` 1.0 in both runs | S5 1.0; S8 n/a by the metric, 2 reviews for 2 waves by transcript (`Wave: 1`, then `Wave: last`) | Met by transcript; the S8 metric is a defect (D8), not a hit |
| P3 | docs dispatches S5 1 (folded), S8 2 | S5 2 (`rules`, `prd-plan`); S8 3 (`rules`, `rules` for `Confirmed:`, `prd-plan`) | **Missed** on both (C5, C2) |
| P4 | S5 `runner_wall_min` at most 16.13 | 16.09 | Met (by 0.04 min) |
| P5 | S5 `cost_per_accept` at most 0.693 | 0.725 | **Missed** |
| P6 | S8 `cost_per_accept` at most 0.786 | 0.899, without a close | **Missed** |
| P7 | accept 1.0 in both runs | 1.0 and 1.0 | Met |
| P8 | close recovery 0 in both runs | S5 0 (one close, promote committed, change archived); S8 no close at all: phase 2 stopped at US$2.85 of its US$3.00 cap, no final gate, no promote, no archive | **Missed** (the delivery did not finish) |

3 met (P2 by transcript, P4, P7), 5 missed (P1, P3, P5, P6, P8). Read P8 as undecided instead and it is still 4 missed of 7 decided. **Chief3 misses most of its predictions.** Chief2 missed the ones it was run to prove (P1 the hard gate, P2, P10) and ended "fix first"; this round misses again, including the same hard gate. The stop rule (EA5) applies: stop this line of work and adopt the best measured version (Verdict).

## What the changes did (role cost and time, from `agents_report`)

| Role | S5 chief3 | S5 chief2 | S8 chief3 | S8 chief2 |
|---|---|---|---|---|
| main (both phases) | 1.11 USD, 18 calls | 1.15, 18 | 2.51, 22 | 1.17, 18 |
| surveyor | 1.21, 3.2 min | 1.04, 2.8 | 0.83, 3.8 | 1.08, 2.8 |
| docs | 1.74 (2), 4.7 min | 1.67 (2), 4.7 | 2.53 (3), 8.1 | 2.93 (2), 7.3 |
| executor tasks | 0.64 (1), 3.3 min | 0.50 (1), 2.5 | 1.57 (3: T01, T02 sonnet, T03 opus), 6.3 | 1.22 (3, sonnet), 6.0 |
| reviewer | 0.21 (1) | 0.28 (1) | 0.65 (2) | 0.51 (1) |
| close executor | 0.16 | 0.21 | none (budget) | 0.16 |

- `e444830` chief: Bash is gone from both runs (chief2 had one per run). The plan read stayed on S5; on S8 the sonnet chief did not open the plan (it read `state.md` only).
- `e444830` review variant: S8 wrote `Review: per wave` with the per-wave Execution line only, and the chief reviewed wave 1 before T03 and the last wave after it. The E06 breach of chief2 is fixed.
- `e444830` protected: S8 wrote one ADR (public API touched: `express` and `points`) against two in chief2; S5 wrote `Protected: none` with a `Checked:` line. Took as designed.
- `1d08cf0` and `4e1f191` fold: never taken. S5 is the case it was built for and still ran `rules` then `prd-plan` (C5).
- S8 cost rose 1.01 USD against chief2: main +1.34 (C4), the wave-1 review +0.27 that chief2 skipped (the honest cost, predicted), T03 on opus +0.41 (C6); docs fell 0.40 with one ADR fewer. The close never ran (C3).

## Causes (from the transcripts)

| # | Cause | Evidence | Measured cost |
|---|---|---|---|
| C1 | The S5 sonnet chief still opens `plan.md` | Phase 2 thinking after reading `state.md`: "1. Read the plan to understand what T01 is", then Read `changes/001-vip-free-delivery/plan.md`, although the `## Plan` line it had just read says "For executors only; the chief never opens it, it has everything below". The path stays in front of the chief: `Plan: <path>` heads `## Plan` and the executor task line needs it | 1 chief violation (hard gate); the plan rides in the 6 later chief calls |
| C2 | The S8 chief confirms the read-back by `SendMessage`, then pays a second docs `rules` start | The `rules` dispatch carried only `Answers:`; the chief then called `SendMessage` to the same docs agent with `Confirmed: "..."`, got "No such tool available: SendMessage", and dispatched a fresh docs `rules` (1,049 prompt characters, 6 calls) only to write the `Confirmed:` line. The SKILL task line "docs `rules` `Answers:` <words>, then `Confirmed: "<words>"`" reads as a continuation of the same agent. S5 put `Answers:` and `Confirmed:` in one prompt and needed one dispatch | 1 chief violation (hard gate); 0.21 USD and 0.6 min for the extra start, plus the chief turns around the failure |
| C3 | The quick-tier budget cap truncates a correct S8 | `split_budget` gives phase 2 30% of US$10 = US$3.00. S8 phase 2 cost 2.85; the chief wrote "Budget is at $0.22, insufficient to safely run executor close" and stopped. A correct S8 now pays the wave-1 review (+0.27) and ran T03 on opus (+0.41), so it no longer fits where chief2 (2.23, one review skipped) did | S8 has no close, no final gate, no promote: its cost, wall, error and close metrics are understated by about 0.16 to 0.2 USD and 1 min, and P8 cannot pass |
| C4 | The S8 phase-1 chief spends about 1 USD more on its own turns | Phase-1 main by subtraction (result cost minus subagents): 1.88 USD against 0.83 in chief2, 12 calls against 9, 4.5 min of own time against 3.2. The chief mapped four decisions onto the options with two free-text corrections (Q2, Q4), wrote a protected-API answer, handled the `SendMessage` error and redispatched. The streamed usage records almost no output tokens, so the split between thinking and context is not measurable from the transcript | +1.05 USD on S8 (tokens_main +33%) |
| C5 | The fold condition is not reachable on S5, and nothing points the chief at it | S5 `## Survey`: Q1 and Q2 options carry `[rule-text: SHP-03 ...]`, but Q3 "No change: 15.00 flat ..." and the confrontation answer carry none, and the SHP-01 and SHP-02 rewrites live only in the confrontation's Proposal. The surveyor `full` return's `Next:` (fixed text in the surveyor card) and the chief's own `## Chief` say "then docs `rules` with the answers; then docs `prd-plan`", unconditionally. The chief never mentions folding | -1 cold start not taken: S5 docs `rules` 0.54 USD and 1.2 min (chief2 measured 0.46 and 1.0) |
| C6 | Docs plans an executor task on opus | S8 `## Plan`: `WAVE 2: T03 · opus per task` (checkout wiring). The opus executor cost 1.02 USD against 0.61 for the sonnet T03 of chief2 | +0.41 USD on S8 |
| C7 | Surveyor writes the version output as the interpreter | `## Survey`: `Python: Python 3.14.3`, and every dispatch carried `Python: Python 3.14.3` | No error seen in this round; an agent that runs it literally fails |
| C8 | Returns over the 2,000-character cap | 8 of 17 returns: reviewer 3,814, 4,948, 6,776; docs 2,148, 4,374, 2,624; surveyor 2,736, 2,688 | Small: main tokens stay at 0.8 to 1.1M |

## Subagent and context checklist

| Check | S5 | S8 | Flag |
|---|---|---|---|
| Dispatch map | surveyor, docs `rules`, docs `prd-plan`, executor T01, reviewer (last), executor close | surveyor, docs `rules`, (`SendMessage` failed), docs `rules`, docs `prd-plan`, executors T01+T02, reviewer (wave 1), executor T03, reviewer (last); no close | S5 fold not taken (C5); S8 second `rules` (C2) and no close (C3) |
| Agents per change | 6 for 1 task | 9 for 3 tasks, close missing | one docs start more than the plan needs on each |
| Main residency | 18 calls, 0.80M; `repo.md`, `state.md` twice, `plan.md` once | 22 calls, 1.08M; `repo.md`, `state.md` twice; `SendMessage` | C1, C2, C4 |
| Prompt in | 197 to 963 characters | 236 to 2,151 | none |
| Return out | 3 of 7 over 2,000 | 5 of 10 over 2,000 | C8 |
| Agent reads | max 18 files, 1 reread | max 20 files, 2 rereads | none |
| Loops | none | none | none |
| Cold starts | none under 10 calls | docs `rules` for `Confirmed:` only, 6 calls | C2 |
| Parallelism | serial plan | wave 1 width 2 in one message | none |
| Model by role | opus surveyor and docs, sonnet chief, executor, reviewer | T03 executor on opus | C6 |
| Cache | 0 busts (max main write 15k) | 0 busts (max 16k) | none |
| Closing | 1 dispatch after the reviewer | none: stopped on the budget cap | C3 |

## Metric defects (EA3)

| # | Defect | Evidence | Effect |
|---|---|---|---|
| D8 | `review_coverage` is n/a when `## Plan` is written by Bash | `protocol.py` reads the `Review:` and `WAVE` lines only from `Write` or `Edit` inputs on `state.md`; S8 docs appended `## Plan` with `printf ... >> state.md` in Bash. The hard gate printed "0 of 1 runs fail", judging S5 alone | A skipped review on a Bash-written plan passes the gate silently; here the review count was right (2 of 2) |
| D9 | `dispatch_map` and the gates do not require a close | S8: no executor `close`, no promote, change not archived; `dispatch_map` 1.0, every hard gate except `chief_violations` passes, accept 1.0 | An unfinished delivery scores as complete, and cheaper |
| D10 | `agents_report` labels the two-phase main with the phase-2 model and the streamed usage misses output tokens | Main row `claude-sonnet-4-6` for both phases; S8 main output 172 tokens for 2.51 USD | Per-role cost totals still match `cost_usd`; main cost can only be split by subtraction |

## Ranked fixes (agent management and context first)

| # | Fix | Removes | Metric moved, expected size | Effort |
|---|---|---|---|---|
| 1 | Take the plan path out of the chief's view: the executor and reviewer read `Plan:` from `## Plan` themselves, the task line becomes `Task: T01`, and `## Plan` opens with the dispatch lines | C1 | `chief_violations` 1 to 0 on S5 (hard gate); about 3.5k characters fewer in each later chief call | Executor and reviewer cards, SKILL task line, docs step 3 |
| 2 | One docs `rules` dispatch carries `Answers:` and `Confirmed:` together in the unattended case, and the SKILL line says "a new dispatch, never a message to the previous agent" for a later confirmation | C2 | `chief_violations` 1 to 0 on S8; -0.21 USD and -0.6 min per run that confirms separately | One SKILL line |
| 3 | Eval config: raise the quick-tier S8 budget (US$12) or split 60/40, so a correct S8 can close | C3 | S8 completes; cost and wall rise by the close (about +0.2 USD, +1 min), which is the honest number | `arms-min.json`, maintainer (EA1) |
| 4 | Eval: read `## Plan` from the final `state.md` of the run (or from Bash writes too) and add a close gate (`close_done`) | D8, D9 | Makes a skipped review and an unfinished close fail the hard gates | Small, `protocol.py` |
| 5 | Executors on sonnet unless the plan's row names a reason; docs writes the reason | C6 | S8 -0.4 USD | Docs card step 3 |
| 6 | Either drop the fold (it never fired in two scenarios) or make it reachable: the surveyor marks every answer that closes a row, including "no change" and the confrontation, and its `Next:` names the fold branch | C5 | S5 -0.5 USD and -1.2 min when it fires | Surveyor card, `interview.md`; a person decides which |
| 7 | Surveyor writes the interpreter name (`python`), never the version string | C7 | Removes a latent error | One line |
| 8 | Enforce the 2,000-character return cap | C8 | Small chief-token gain | Reviewer, docs, surveyor cards |

## Verdict
Chief3 fixed what it aimed at in protocol shape (no chief Bash, the wave-1 review restored, one ADR fewer, S5 wall inside the band), but it fails its hard gate again (`chief_violations` 1 per run: the plan read on S5, `SendMessage` on S8), the fold never fired, cost per accept rose against chief2 on both scenarios, S8 wall rose 21%, and S8 ran out of its phase-2 budget before the close. It misses 5 of 8 predictions after a chief2 round that ended "fix first" on its hard gate, so the stop rule applies.

Best measured version: no FLOW-FAST round beats GATE on both cost and wall time per accepted task with every hard gate green. Short (`0019169`) is the cheapest and fastest on S5 but failed a hidden test on S8 (6/9). Chief2 (`dc6f7b9`) and chief3 (`4e1f191`) fail `chief_violations`, are slower on S8 (+29% and +56% against GATE), and each has an unfinished or skipped step on S8. Adopt GATE as measured in `eval/results/2026-10-08-big` (`fix/existing-repo-adoption`, the current baseline). If the maintainer keeps prd-flow for its 50% to 85% lower main tokens, fixes 1 to 4 are the smallest set before one more quick round; that would be an explicit exception to EA5, not its outcome.
