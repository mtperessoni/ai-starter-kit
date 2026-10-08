# Efficiency analysis: prd-flow against prd-gate

Date: 2026-10-07. Small fixture, scenarios S5 (hidden conflict), S6 (incoming spec), S7 (open dimension), one rep per cell. Arms: **prd-gate** (`fix/existing-repo-adoption`), **flow r1** (PR #10), **flow r2** (+ `424b160`, workers dispatched, one gate run per step), **flow r3** (+ `2ac17cb` step 4 formats, `ede5753` fewer serial agents). Every number comes from `python eval/rounds.py` over `eval/results/2026-10-07-flow*`. Reproduce:

```bash
python eval/rounds.py eval/results/2026-10-07-flow:GATE eval/results/2026-10-07-flow:FLOW eval/results/2026-10-07-flow-v2:FLOW eval/results/2026-10-07-flow-v3:FLOW
```

## The six metrics, totals over the three runs

| Metric | Field | prd-gate | flow r1 | flow r2 | flow r3 |
|---|---|---|---|---|---|
| M1 Tokens | tokens_total | 11.3M | 18.9M | 22.7M | 23.4M |
| | tokens_main (most expensive model) | 7.4M | 15.7M | **8.7M** | 17.1M |
| | tokens_subagents | 3.6M | 2.9M | 13.0M | 3.1M |
| | context_peak (median) | 99k | 128k | 109k | 145k |
| | cost_usd | 11.53 | 18.38 | 17.17 | 19.63 |
| M2 Tasks done | tasks_done / tasks_planned | 3 / 4 | 6 / 6 | 5 / 7 | 4 / 4 |
| | hidden tests passed | 19 / 22 | 22 / 22 | 22 / 22 | 22 / 22 |
| M3 Total time | wall_min | 32.6 | 52.7 | 65.2 | 56.8 |
| M4 Time per run | main_min (total) | 21.7 | 41.2 | 27.7 | 41.0 |
| | agent_min (total) | 10.9 | 11.5 | 37.5 | 15.9 |
| | cold_starts | 7 | 6 | 19 | 9 |
| | min_to_code (median) | 8.0 | 12.8 | 16.0 | 12.3 |
| M5 Errors | tool_errors / tool_calls | 8 / 258 | 1 / 308 | 22 / 568 | 7 / 319 |
| | gate_runs main / subagents | 7 / 13 | 26 / 0 | 10 / 47 | 23 / 6 |
| | error kinds: gate check, environment, missing file | 3, 1, 1 | 2, 0, 0 | 10, 6, 4 | 6, 1, 2 |
| M6 Plan | plan_coverage, plan_drift (median) | 0.5, 0 | 1, 0 | 1, 0 | 1, 0 |
| | review_rounds, blind findings | 2, 1 | 4, 0 | 1, 1 | 4, 2 |

Read prd-gate with care: it is cheaper partly because it did less. In S7 it stopped without code (4 of 7 hidden tests); in S6 it skipped the TRD, the review and wrote the plan after the code. S5 is the only like-for-like scenario.

## What decides cost and time

**1. Where the docs phase runs (by far the largest lever).** The same scenario, inline versus dispatched:

| Scenario | Inline (main thread writes PRD, TRD, plan) | Dispatched (writer and planner agents) |
|---|---|---|
| S5 | r1 US$7.80, 22.2 min · r3 US$8.10, 25.1 min | r2 US$5.79, 22.7 min |
| S6 | r1 US$4.71, 11.8 min | r2 US$5.95, 21.7 min (format loop) · r3 **US$4.42, 14.1 min** |
| S7 | r1 US$5.87, 18.6 min · r3 US$7.11, 17.7 min | r2 US$5.43, 20.8 min (format loop) |

Dispatched is cheaper in 5 of 6 pairs at about the same wall time. Inline runs also run the gate 8 to 10 times on the main thread, each resending 100k to 155k tokens. In r3 the main thread chose inline on purpose: *"I'll write the PRD inline (I hold full context; cheaper than a cold-start worker for a one-rule change)"*, using the cold-start cost the kit itself stated (LS26). Rule compliance is the dominant source of variance: one rep per cell cannot separate a better rule from a lucky run.

**2. Format loops.** r2 dispatched every time but every `writer-prd` failed Q2/Q3 on free-form state files, rewrote them and failed Q4 (47 gate runs in subagents, 10 gate-check errors). `2ac17cb` removed it: r3 has 6 gate runs in subagents.

**3. Serial cold starts.** About one minute per agent. r2 had 19, r3 9. Time grows with the number of serial agents, not with the work.

**4. Environment and path errors.** `python` not found, scripts opened from the wrong folder, state files read at `.prd-flow/state` instead of `.claude/prd-flow/state`: 1 to 6 per round, each a retry turn.

## Paths to improve each metric

Ordered by expected effect per unit of effort. "Done" items are on PR #11; none of them is measured yet unless the round says so.

| # | Metric | Change | Expected effect | Status |
|---|---|---|---|---|
| P1 | M1, M3, M4 | The dispatch rule carries the measured numbers, names Task as the Agent tool, includes Promote; no "inline is cheaper" escape | Main tokens back to r2 level (about 3M per run), cost about US$4.5 to 6 per run, no 8 to 10 main gate runs | Done (LS27), unmeasured |
| P2 | Eval | `docs_dispatched` as a tracked metric (a writer or planner subagent ran) and 2 reps for S5 before any decision | Separates rule quality from model variance; today one inline run swings a round by US$2 to 3 | Proposed |
| P3 | M5 | The worker prompt carries the absolute state folder and the interpreter (`python` or `python3`) from `repo.md` "Commands" | Removes the environment and missing-file retries (1 to 6 per round) | Proposed |
| P4 | M5 | On Q2 or Q3, `gate.py --rules` prints the expected skeleton (heading and table header) | A failed first run fixes itself in one turn | Proposed |
| P5 | M4 | One docs agent resumed across steps 5, 7 and 8 where the session can resume agents (SendMessage), falling back to the current two agents | Two docs cold starts instead of three, the pack read once | Proposed |
| P6 | M1 | Split `reference/workers.md` into one file per worker | Each worker reads its briefing only (today the whole file or a guessed range) | Proposed |
| P7 | M4 | Size M with one PRD section: the surveyor runs only K01, K02, K11 (no history or remote sweep when no ID is reused) | About 1 minute less before the interview | Proposed, check it keeps `conflict_found` |
| P8 | M6 | Keep: every FLOW run passed all hidden tests, plan coverage 1, drift 0, no contradiction left | Guard these as hard gates of the next rounds | Keep |

## Decision rule for the next round

Run `eval/arms-flow.json` with S5 at 2 reps and S6, S7 at 1, then `eval/rounds.py`. Adopt when, against prd-gate: hidden tests and `contradiction_left` not worse; S5 `cost_usd` within +10% and `wall_min` within +10%; `tokens_main` per run at most 3.5M; `docs_dispatched` true in every run.
