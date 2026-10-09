# Predictions: round run-speed

Written before the run. Arm BASE = main at 3524bd2 (the kit before the run-speed work), arm CAND = `feat/run-speed` HEAD at the time of the run; both two-phase (opus plan, sonnet execution), same harness and protocol (`eval/arms-run-speed.json`). Scenarios S5 x2, S8 x1, S9 x1, S10 x1, ten runs. Plan: `proposals/plan-run-speed.md` (W6, goals G1 to G7). Metric definitions: `eval/METRICS.md` "Run-speed fields". "Median" is over the reps of the scenario; with one rep it is the run.

The base values are estimates from the 2026-10-08 rounds and the clara-ai run (`run-timing-report.md`), not measured on this harness; the round replaces them.

## Per goal

| Goal | Metric | BASE predicted | CAND predicted | Met when |
|---|---|---|---|---|
| G1 Batch verification: no related test or suite in an executor, one `gates.sh verify <slug>` per wave run by the chief, one baseline per plan commit | `baseline_runs`, S10 | 3 to 5 (docs agent runs it, executor reruns it, the close runs it) | exactly 1 | S10 CAND `baseline_runs` = 1 |
| G1 | `verify_runs`, S10 | 0 | 1 (one wave, one verification) | S10 CAND = number of waves |
| G1 | `agent_test_runs`, S5, S8, S10 | 3 to 10 (each executor runs related tests and sometimes the suite) | 0 (only a single named test file, which does not count) | 0 in every CAND run |
| G1 | `baseline_runs`, S5 and S8 | 2 to 3 | 1 | median 1 on both |
| G1 | `verify_runs`, S5 and S8 | 0 | one per wave (S5 1, S8 2) | equals the waves of the plan |
| G1 | `runner_wall_min`, S10 | 28 to 40 min (each full suite is about 100 s, plus waits) | 18 to 26 min | at least 20% below BASE |
| G2 No polling, no live process at handback | `poll_calls`, S10 | 3 to 10 (until or sleep loops waiting on the slow suite) | 0 | S10 CAND = 0 |
| G2 | `poll_calls`, S5 and S8 | 0 to 2 | 0 | median 0 |
| G2 | `bg_alive_at_return`, every scenario | 0 to 2 (S10 mostly) | 0 | 0 in all 5 CAND runs |
| G3 Fewer cold starts | `cold_starts`, S8 (2 waves) | 9 to 12 | 6 to 8 | at least 30% below BASE (target 40%) |
| G3 | `cold_starts`, S5 | 6 to 8 | 4 to 6 | median at least 25% below BASE |
| G3 | `min_to_docs`, S5 | about 9 min | 6 to 8 min | not above BASE |
| G4 Fewer user rounds lost to a wrong model | `rejected_answers`, S9 | 1 to 3 (the chief carries the monthly-spend premise into the interview) | 0 to 1 | CAND at most 1 and below BASE |
| G4 | `question_rounds`, S9 | 3 to 5 | 2 to 3 | CAND at most BASE |
| G4 | round 0 model sentence (transcript text, matches `premise.round0_matches`), S9 | missing in 1 of 1 | present in 1 of 1 | present, before any rule question |
| G4 | S9 PRD diff | a rule or Planned row on the wrong model in BASE (`prd_fidelity` f2 contradicted) | no rule on the wrong model, wish recorded as an open question (f1 to f4 stated) | `prd_fidelity` at least 0.75 and f2 not contradicted |
| G5 Fewer fix dispatches (the wave verification finds failures once, the chief routes them in one batched fix) | `review_rounds`, `rework_actions`, S5 and S8 | 2 and 3 to 5 | 1 to 2 and 2 to 3 | each at least 30% below BASE (target 40%) |
| G5 | `first_pass`, S5 | false in 1 of 2 | true in 2 of 2 | at least as many true as BASE |
| G6 Telemetry per repository | retro of each repo (`gates.sh retro`), S11 not in this round | not measured | not measured | deferred to the first real cross-repo delivery; S11 is built and graded by hand when needed |
| G7 Wall time | `runner_wall_min`, S5 median | about 15 min | 11 to 13 min | within +10% of BASE (adoption rule), target -15% |
| G7 | `runner_wall_min`, S8 | about 20 min | 15 to 17 min | within +10% of BASE, target -15% |
| G7 | `cost_per_accept`, S5 median | BASE | -5% to -15% | within +10% of BASE (adoption rule) |

## Per metric (all scenarios)

| Metric | Direction | Predicted change CAND against BASE | Why |
|---|---|---|---|
| `baseline_runs` | lower | S10 3 to 5 to 1; S5, S8 2 to 3 to 1 | W1.1: baseline in the background at the plan commit, docs Plan step 4 removed |
| `poll_calls` | lower | to 0 | W1.7 long command rule: explicit timeout, foreground, no loops; detectors in W5.3 |
| `bg_alive_at_return` | lower | to 0 | same rule: never return with a live process |
| `question_rounds` | lower | S9 down 1 to 2; others equal | W2.3 round 0 model sentence replaces a wrong-model interview |
| `rejected_answers` | lower | S9 to at most 1; others 0 | W2.1 to W2.3 |
| `bash_code_edits` | lower | 2 to 6 to 0 to 1 in executors (sed -i, python heredocs) | W4.3 Edit and Write only, hook warns |
| `git_unsafe_calls` | lower | 0 to 2 in S8 wave 1 (stash, checkout between executors) to 0 | rule text only, no hook blocks them: measured, a gate warning; S8 has a wave of width 2 or more |
| `verify_runs` | one per wave | 0 to one per wave | the chief runs `gates.sh verify <slug>` once per wave; executors run no related test or suite |
| `agent_test_runs` | lower | 3 to 10 to 0 | executors verify nothing beyond a single named test file; the chief's wave verification replaces it |
| `cold_starts` | lower | down 25% to 40% | W3.1 resume with SendMessage, W2.6 delta re-survey, W3.7 dispatch ledger |
| `main_calls`, `tokens_main` | lower | S5 median down 10% | W5.1 batched dispatch; no extra main reads |
| `rework_actions`, `review_rounds` | lower | down 30% to 40% | W4.2 executor self-check, W4.5 batched fixes |
| `runner_wall_min` | lower | S5 -15%, S8 -15%, S10 -30% | W1, W5.1 |
| `cost_usd` | lower | S5 -5%, S10 -10% | fewer cold starts and reruns; the resumed agents keep a warm cache |

## Hard gates (must hold for CAND, otherwise the round fails whatever the speed)

| Gate | Value |
|---|---|
| Hidden tests | 100% on S5, S8, S9, S10 |
| `contradiction_left`, `conflict_recall` | 0 and 1.0 on S5 |
| `main_violations`, `chief_violations`, `return_compliance`, `surveyor_first` | 0, 0, 1.0, true |
| `git_unsafe_calls`, `bg_alive_at_return`, `agent_test_runs` | 0 in every CAND run (`git_unsafe_calls` is measured, a gate warning, not a block) |
| S10 | one verification per wave (`verify_runs` = 1), `baseline_runs` = 1 and `poll_calls` = 0 |
| S9 | `rejected_answers` at most 1, no rule on the wrong model |
| Adoption (`eval/adoption.py`) | M2, M7, M8 no loss; S5 `cost_usd` and `wall_min` within +10%; `tokens_main` at most 3.5M; wins at least losses per group |

## Cost and stop rule

Expected cost US$20 to 30 for ten runs (US$1.5 to 3.5 each, BASE runs on S10 higher because of the repeated 100 s suite), cap US$100 at US$10 per run; judge and blind review add about US$0.3 per run. Wall time about 1.5 to 2 hours at parallel 3.

Stop rule (EA5, `MAINTAINING.md`): if most predictions above are missed, or two rounds in a row miss, stop this line of work, keep only the changes that moved a gate metric and record the numbers in the lesson LS31 of `rules/09-lessons.md`.
