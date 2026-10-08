# Audit: round 2026-10-08-chief2, quick tier

Scope: 2 runs in `eval/results/2026-10-08-chief2/` (FLOW-FAST, S5 and S8, 1 rep each, `eval/arms-min.json`), kit at `dc6f7b9` on `fix/prd-flow-cost` (fixes 1 to 5 of `eval/AUDIT-chief-quick.md` and the eval metric fixes). Predictions: `eval/predictions/2026-10-08-chief2.md`, committed alone (`e521bf1`) before the run. Both runs ended `ok`; the transcripts carry only `rate_limit_event` with `status: allowed_warning` (seven-day window at 26 to 27%), no 429 and no session limit, so EA7 is not triggered. Spend: US$11.93 of the US$20 approved (S5 4.854, S8 7.077). Numbers come from `rounds.py`, `agents_report.py` and small scripts over the transcripts; full outputs, local and git-ignored: `rounds-vs-short-FLOW-FAST.md`, `rounds-vs-chief-FLOW-FAST.md`, `rounds-vs-big-GATE.md`, `agents.md` in the round folder.

## Scorecard

Candidate `2026-10-08-chief2:FLOW-FAST` against `2026-10-08-short:FLOW-FAST` (pre-chief; S5 is the median of 3 reps), `2026-10-08-chief:FLOW-FAST` (contract v6 before the fixes, 1 rep) and `2026-10-08-big:GATE` (adoption baseline; S5 median of 3). One rep per scenario: a single number, no spread.

| Metric | Scn | Chief2 | Short | vs short | Chief | vs chief | GATE | vs GATE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| tokens_main | S5 | 0.808M | 1.639M | -50.7% | 1.034M | -21.9% | 3.816M | -78.8% | win |
| tokens_main | S8 | 0.809M | 2.127M | -62.0% | 1.024M | -21.0% | 6.838M | -88.2% | win |
| tokens_total | S5 | 4.475M | 4.004M | +11.8% | 5.447M | -17.8% | 6.771M | -33.9% | loss vs short only |
| tokens_total | S8 | 7.606M | 7.120M | +6.8% | 8.570M | -11.2% | 9.671M | -21.4% | loss vs short only |
| cost_usd | S5 | 4.854 | 4.495 | +8.0% | 5.674 | -14.5% | 5.770 | -15.9% | within band vs short |
| cost_usd | S8 | 7.077 | 6.293 | +12.5% | 7.812 | -9.4% | 7.887 | -10.3% | loss vs short |
| cost_per_accept | S5 | 0.693 | 0.642 | +7.9% | 0.811 | -14.5% | 0.824 | -15.9% | PASS (adoption band +10%) |
| cost_per_accept | S8 | 0.786 | 1.049 | -25.1% | 0.868 | -9.4% | 0.876 | -10.3% | win (short S8 had 6/9) |
| runner_wall_min | S5 | 17.05 | 14.66 | +16.3% | 21.57 | -21.0% | 16.21 | +5.2% | FAIL vs short (band +10%) |
| runner_wall_min | S8 | 22.67 | 22.45 | +1.0% | 25.82 | -12.2% | 17.53 | +29.3% | tie vs short, loss vs GATE |
| wall_min (active turns) | S5 | 17.00 | 11.43 | +48.7% | 21.53 | -21.0% | 16.16 | +5.2% | secondary (biased short base) |
| wall_min (active turns) | S8 | 22.62 | 17.77 | +27.3% | 25.78 | -12.3% | 17.47 | +29.5% | secondary |
| accept (hidden) | S5 | 1.0 (7/7) | 1.0 | 0 | 1.0 | 0 | 1.0 | 0 | tie |
| accept (hidden) | S8 | 1.0 (9/9) | 0.667 | +0.333 | 1.0 | 0 | 1.0 | 0 | tie (win vs short) |
| error_rate | S5 | 0.049 (9/183) | 0.024 | x2.0 | 0.062 | -21% | 0.035 | x1.4 | loss vs short |
| error_rate | S8 | 0.029 (8/277) | 0.033 | -12% | 0.045 | -36% | 0.016 | x1.8 | win vs short |
| main_violations | S5, S8 | 0, 0 | 1, 6 | to 0 | 0, 0 | 0 | 52, 85 | to 0 | pass |
| chief_violations | S5, S8 | 2, 2 | not bound | n/a | 1, 1 | +1 each | not bound | n/a | **hard gate FAIL** |
| return_compliance | S5, S8 | 1.0, 1.0 | 0.0 | n/a | 1.0, 1.0 | 0 | 0.0 | n/a | pass |
| surveyor_first | S5, S8 | true, true | true | n/a | true, true | 0 | false | n/a | pass |

Headline: cost per accepted task S5 0.693 (short 0.642, +7.9%, inside the band; chief -14.5%), S8 0.786 (short 1.049, -25%; chief -9.4%). Wall time per accepted task on `runner_wall_min`: S5 17.05 min (short 14.66, +16.3%, outside the band; chief -21%), S8 22.67 min (short 33.66 per accept, -33%; raw +1.0%). The fixes recovered most of the chief round's regression (cost -9% to -15%, wall -12% to -21% against chief) but S5 wall time is still 2.4 min over short, and `chief_violations` got worse (1 to 2 per run).

Adoption (`rounds.py`, M07): FAIL against short (hard gate `chief_violations`; S5 `runner_wall_min` +16%; M3, M4, M7 lose). FAIL against chief (hard gate only, plus M2, M7 and M8 by one or two rows each; every cost and time group wins). FAIL against GATE (hard gate; M3, M4, M5 lose; S5 cost per accept -16% and runner wall +5% both inside the band).

## Predictions

| ID | Met when | Measured | Verdict |
|---|---|---|---|
| P1 | `chief_violations` 0 in both runs | 2 and 2 | **Missed** (worse than chief's 1 and 1; causes C1, C2) |
| P2 | docs dispatches at most 1 per run | 2 and 2 (`rules`, `prd-plan`) | **Missed** as written. The fix did take (3 to 2: `prd` and `trd-plan` are one `prd-plan` dispatch); the prediction was miscalibrated, since SKILL step 3 keeps docs `rules` as its own dispatch |
| P3 | docs cost S5 at most 1.20, S8 at most 1.80 | 1.67 and 2.93 | **Missed** (S5 -0.18 against chief; S8 +0.13, cause C4 and C5) |
| P4 | close recovery 0, one close per run | 0 and 0; 1 close each; promote committed, tree clean, change archived | Met |
| P5 | S5 1 reviewer (serial); S8 stays 2 | S5 1; S8 1 | **Missed** on S8: `## Plan` said `Review: per wave` and the chief reviewed once after the last wave (C3, a protocol breach) |
| P6 | promote errors 0 | 0 and 0 | Met |
| P7 | `tokens_main` S5 at most 1.034M, S8 at most 1.024M | 0.808M and 0.809M | Met |
| P8 | S5 `cost_per_accept` at most 0.706 | 0.693 | Met |
| P9 | S8 `cost_per_accept` at most 0.868 | 0.786 | Met (about 0.25 USD of it is the skipped wave-1 review, C3) |
| P10 | S5 `runner_wall_min` per accept at most 16.13 | 17.05 | **Missed** |
| P11 | S8 `runner_wall_min` per accept at most 24.70 | 22.67 | Met (about 1 min of it is the skipped review) |
| P12 | accept 1.0 in both runs | 1.0 and 1.0 | Met |
| P13 | `error_rate` S5 at most 0.062, S8 at most 0.045 | 0.049 and 0.029 | Met |
| P14 | `return_compliance` 1.0, `surveyor_first` true, `main_violations` 0 | 1.0, true, 0 in both | Met |
| P15 | chief gates in `rounds.py`; `agents_report` cost within 2%; `waves` equals the plan | gates printed; 4.85 vs 4.854 and 7.08 vs 7.077; waves 1 and 2 for plans of 1 and 2 waves | Met (but see D6) |

10 met, 5 missed (P1, P2, P3, P5, P10). By the round's stop rule this is "fix first": P1 and P2 miss and P10 misses while the dispatch predictions mostly hold. EA5 is not triggered: this round met most of its predictions (10 of 15) and the previous quick round decided only one (P6, missed) and left the rest undecided, so this is not the second consecutive round missing its predictions.

## What the fixes did (role cost and time, from `agents_report`)

| Role | S5 chief2 | S5 chief | S5 short (r1 / r2 / r3) | S8 chief2 | S8 chief | S8 short |
|---|---|---|---|---|---|---|
| main | 1.15 USD, 18 calls | 1.28, 23 | 1.92 / 1.72 / 1.97 | 1.17, 18 | 1.31, 22 | 2.11, 41 |
| surveyor | 1.04, 2.8 min | 1.00, 3.3 | 0.82 / 0.64 / 0.68, 1.7 to 1.9 | 1.08, 2.8 | 1.38, 4.2 | 0.91, 2.4 |
| docs | 1.67 (2), 4.7 min | 1.85 (3), 5.3 | 1.04 / 1.35 / 0.97, 2.1 to 3.0 | 2.93 (2), 7.3 | 2.80 (3), 7.4 | 1.47 (1), 3.4 |
| executor (tasks and close) | 0.71 (2), 4.0 min | 1.12 (5) | 0.47 / 0.38 / 0.59 | 1.38 (4), 6.8 | 1.93 (4) | 1.23 (4) |
| reviewer | 0.28 (1), 1.0 min | 0.42 (2) | 0.24 / 0.27 / 0.28 | 0.51 (1), 1.8 | 0.40 (2) | 0.52 (2) |

- Fix 1 (docs): 3 dispatches to 2. Saved 0.18 USD and 0.6 min on S5, nothing on S8 (the single `prd-plan` agent ran 57 tool uses, context peak 71k, 2.19M cache reads, 2.29 USD).
- Fix 2 (close): one close dispatch per run, no recovery, promote committed (`git status` clean, `docs(prd): promote <slug>` is the last commit, change folder under `changes/archive/`). S5 saved 2 executor starts.
- Fix 3 (serial review): S5 one review on `Wave: last`, as designed (-0.14 USD, about -1 min).
- Fix 4 (`## Plan` carries the task IDs): docs wrote it correctly in both runs, but the chief still opened `plan.md` (C1).
- Fix 5 (promote skips Q- and DEC-): no promote error in either run.
- S5 still sits 2.4 min over short. Against the short medians: docs +2.3 min (the separate `rules` start is 1.0 min of it), surveyor +1.0 min, the close executor 1.5 min (the short main closed in its own turn), against a main that is about the same (4.5 min).

## Causes (from the transcripts)

| # | Cause | Evidence | Measured cost |
|---|---|---|---|
| C1 | The resumed chief opens `plan.md` although `## Plan` has everything | Both phase-2 sessions read `state.md` (which holds `Plan:`, the `WAVE n:` lines and `Review:`), then think "Let me also read the plan to understand what T01 entails" / "read the plan to see the task details" and Read `changes/001-<slug>/plan.md`. The dispatch template `Plan: <path> · Task: <ID>` puts the path in front of the chief, and nothing in `## Plan` or the `Next:` line says not to open it | 1 chief violation per run (hard gate); the plan (3,518 and 5,339 characters) then rides in every later chief call |
| C2 | The chief runs Bash for facts it already has | S5 phase 1: `git log --oneline -6` "to capture the exact commit subjects for the summary" (the eval prompt asks for a commit list; the docs returns carried `Commit:`). S8 phase 2: `python --version` because the dispatch line needs `Python: <interpreter>` and `state.md` does not record it | 1 chief violation per run (hard gate) |
| C3 | The Execution line carries both review branches, and the sonnet chief took the wrong one | S8 `## Plan`: `Review: per wave` (wave 1 has T01 and T02), followed by the verbatim Execution line that also spells out "(a serial plan, `Review: once after the last wave`: the literal "Wave: last" ...)". The chief's thinking: "The Review line confirms it runs once, after the last wave". Dispatches: T01 and T02 in one message, then T03, then one reviewer `Wave: last. Commits: 1fc4c92 5e5416a ae57e66` | E06 breach: wave 1 was never reviewed before T03 built on it. It also flatters S8: about -0.25 USD and -1 min that a correct run would spend |
| C4 | Docs `rules` is still a separate cold start | Both runs: `Confirm ... rules` / `prd-flow docs rules` (1,438 and 2,342 prompt characters) then `prd-plan`. In the unattended eval the read-back is approved without change | S5 0.46 USD and 1.0 min; S8 0.64 USD and 1.7 min per C5 |
| C5 | A protection that is not broken still produces ADRs | S8 `## Survey`: `Protected: Exact Money ... · constitution I · ADR. Not broken: points are a count ...` and the same for the public API. Docs wrote `docs/adr/0001-...` and `0002-...` plus the index (5 calls in a 50k to 71k context); the chief round's S8 tree has no ADR | About 0.3 USD and 0.6 min on S8 (5 of the agent's 42 calls, at its average of 0.055 USD and 0.13 min per call) |
| C6 | Surveyor costs more than before v6 | S5 1.04 USD and 2.8 min against 0.64 to 0.82 and 1.7 to 1.9 in short; it now prepares every question round | +0.2 to +0.4 USD, +1 min per C5 (unchanged from the chief audit's C3) |
| C7 | Returns over the 2,000-character cap | 7 of 14 returns: reviewer 5,408 (S5) and 3,961 (S8), docs 2,480 and 3,058, surveyor 2,992 and 2,017 | Small: main tokens are already 0.8M |
| C8 | Close executor stages the change folder after moving it | Both runs: `git add ... changes/001-<slug>` after the archive move, `fatal: pathspec ... did not match any files`, then a retry | 1 error and 1 extra call per run |

## Subagent and context checklist

| Check | S5 | S8 | Flag |
|---|---|---|---|
| Dispatch map | surveyor, docs `rules`, docs `prd-plan`, executor T01, reviewer (last), executor close | surveyor, docs `rules`, docs `prd-plan`, executors T01+T02, executor T03, reviewer (last), executor close | S8 wave-1 review skipped (C3) |
| Agents per change | 6 for 1 task | 8 for 3 tasks (9 by the plan) | none |
| Main residency | 18 calls, 0.81M tokens; reads `repo.md`, `state.md` twice, `plan.md` once; 1 Bash | 18 calls, 0.81M; same reads; 1 Bash | `plan.md` and Bash (C1, C2) |
| Prompt in | 189 to 1,438 characters | 194 to 2,342 | none |
| Return out | 3 of 6 over 2,000 | 4 of 8 over 2,000 | yes (C7) |
| Agent reads | max 20 files, 1 reread | max 23 files, 1 reread | none |
| Loops | none | `gate.py --step trd` and `--step plan` twice each inside docs | none over 2 |
| Cold starts | none under 10 calls | none under 10 calls | none |
| Parallelism | serial plan by shape | wave 1 width 2, `parallel_factor` 1.29 | below 1.5 on S8 |
| Model by role | opus surveyor and docs, sonnet chief, executors, reviewer | same | none |
| Cache | 0 busts | 0 busts | none |
| Closing | 1 dispatch after the reviewer | 1 | none |

## Metric defects (EA3)

| # | Defect | Evidence | Effect |
|---|---|---|---|
| D6 | `dispatch_map` and the gates do not check the review count against the `Review:` line | S8: `Review: per wave` with 2 waves, 1 reviewer dispatch, `dispatch_map` 1.0, `review_rounds` 1 | A skipped wave review passes every hard gate and lowers cost and wall time (P5, P9, P11 flattered) |
| D7 | `cost_by_role` is empty in `rounds.load_column` | `six.derive(...)["cost_by_role"]` is `{}` for chief and chief2 | Per-role cost comes only from `agents_report.py`; harmless while that tool is right |

The eval fixes of `fbf4148` hold: the four chief gates reach `rounds.py`, `agents_report` totals match `cost_usd` within 0.1%, `waves` counts only executor tasks, and the scorecard uses `runner_wall_min`.

## Ranked fixes (agent management and context first)

| # | Fix | Removes | Metric moved, expected size | Effort |
|---|---|---|---|---|
| 1 | Docs writes into `## Plan` a line "Chief: dispatch from these lines only; never open the plan, each executor reads its card" and a `Python: <interpreter>` line; the SKILL resume step says the same in one line; the chief's report lists the `Commit:` fields of the returns, never `git log` | C1, C2 | `chief_violations` 2 to 0 per run (hard gate); 3.5k to 5.3k fewer characters in each later chief call | 3 lines (docs card step 3, SKILL resume, chief report rule) |
| 2 | Docs writes only the Execution line that applies: one variant for `Review: per wave`, another for `Review: once after the last wave`, never both branches in one line | C3 | S8 reviewer dispatches 1 to 2 (E06 restored); cost about +0.25 USD and +1 min on S8, which is the honest number | Docs card step 3 |
| 3 | Eval: `dispatch_map` (or a new hard gate) compares reviewer dispatches with the `Review:` line and the wave count | D6 | Makes C3 visible as a gate failure | Small, `protocol.py` |
| 4 | Surveyor writes `Protected:` only for a protection the change breaks; a protection checked and not broken goes to `Contexts:` or a `Checked:` note, so docs writes no ADR for it | C5 | S8 about -0.3 USD and -0.6 min; fewer files for the reviewer | Surveyor card and `impact.md` line 91 |
| 5 | Decide (maintainer): fold docs `rules` into `prd-plan` when the question rounds leave nothing open, showing the rules read-back together with the wave table at step 5 (an adjustment is one `prd-plan adjust`) | C4 | -1 cold start per C5: S5 -0.46 USD and -1.0 min, S8 -0.64 USD and -1.7 min; closes most of the S5 wall gap to short (+2.4 min) | SKILL steps 3 to 5 and the docs card; a behavior change for the user (the rules read-back moves to the plan approval), so a person decides |
| 6 | Close executor stages with `git add -A changes/` after the archive move | C8 | -1 error per run (error_rate about -0.5 point) | One line in the executor card |
| 7 | Enforce the 2,000-character return cap (findings and surveys to their file, the return holds counts and the path) | C7 | Small chief-token gain | Reviewer, docs, surveyor cards |
| 8 | Revisit the surveyor's question preparation cost only after 1 to 5 are measured | C6 | Up to -0.3 USD and -1 min per C5 | Needs its own prediction |

## Verdict
The fixes worked where they aimed at dispatch shape: close has no recovery and its promote is committed, the serial S5 plan is reviewed once, promote no longer errors, and cost and wall time fell 9% to 21% against the chief round, putting S5 cost per accept inside the adoption band against short (+7.9%). The round still fails its hard gate (`chief_violations` 2 per run: the chief opens `plan.md` and runs one Bash), S5 wall time stays 16% over short, and S8 skipped its wave-1 review; so fix first (fixes 1 to 4, with fix 5 for the maintainer to decide), then another quick round before the confirm tier.
