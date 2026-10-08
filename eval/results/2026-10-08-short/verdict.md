# Verdict: round 2026-10-08-short against its predictions

Predictions: `eval/predictions/2026-10-08-short.md`. Numbers from `python eval/rounds.py eval/results/2026-10-08-big:GATE eval/results/2026-10-08-short:FLOW-FAST --baseline eval/results/2026-10-08-big:GATE` (full output in `rounds-vs-big-GATE.md`, local) after the regrade fix (`1ac5796`: both transcripts of every run, graded on the round's own builds), plus small scripts over the transcripts for the promote and per-run rows.

**Result: 6 hits, 4 misses of 10. Adoption verdict (M07): FAIL**, on two hard gates: hidden tests 100% (S8 6 of 9) and `main_violations` 0 (5 of 5 runs above 0). EA5 is not triggered by this round alone (most predictions met).

| Fix | Metric | Predicted | Measured | Verdict |
|---|---|---|---|---|
| 1 Source line per ID, promote guard | runs with a promote failure | 0 runs | 1 of 5 (S7: `gate --final` exit 1, TRD `checkout.md` still had a Planned row; a fold and a second commit followed). Big round: 8 of 12 | miss |
| 2 Self-sufficient resume, `Lens:` | `dispatch_map` | 1.0 in 5 of 5 | 1.0 in 5 of 5 (GATE 0.5) | hit |
| 2 | blind Critical or High in S7 | 0 | 0 Critical, 1 High | miss |
| 3 One close command | `main_violations`, median per run | at most 1 | 1, 1, 2, 9, 6: median 2, total 19 (GATE 161) | miss |
| 5, 6 Batched bookkeeping and commits | `main_calls`, S5 median | at most 35 | 32 (38, 28, 32) | hit |
| 5, 6 | `tokens_main`, S5 median | at most 2.2M | 1.64M (2.01M, 1.43M, 1.64M) | hit |
| 7 Decisions and Leave on the card | `prd_fidelity` S7 and S8 | both at least 0.8 | 1.0 and 1.0 | hit |
| 7 | S8 `wall_min` | at most 18 | 17.8 graded (`runner_wall_min` 22.5, big 22.7) | hit |
| all | S5 `cost_per_accept` against GATE | -10% to -25%, at most GATE | 0.636 against 0.752: -15.4% | hit |
| all | hard gates: hidden tests, `contradiction_left`, `conflict_recall` | hold | hidden tests fail in S8 (`accept` 0.667, 6 of 9); `contradiction_left` 0; `conflict_recall` 1.0 in 3 of 3 | miss |

## Notes
- Metric defect found and fixed before this verdict (EA3): the earlier regrade graded phase 1 only and picked the newest temp build of each run name, which was a later dry run (seed only). It reported `tasks_done` 0, `wall_min` about 7 and `accept` 0.43 / 0.57 / 0.11; the regraded values are above.
- `wall_min` (sum of the graded sessions) and `runner_wall_min` differ by up to 4.7 min (S8, S5-r1); the predictions used `wall_min`. On `runner_wall_min` S8 is 22.5 and the S8 time prediction would miss.
- Against GATE on the shared scenarios (S5 x3, S7, S8; GATE's S6 left out): total cost 25.06 against 26.20 (-4%), `tokens_main` 9.59M against 20.91M (-54%), and cost moves to subagents (14.48 against 5.31). S7 alone costs more (5.40 against 2.51: GATE ran S7 with no subagent and accept 0.571).
