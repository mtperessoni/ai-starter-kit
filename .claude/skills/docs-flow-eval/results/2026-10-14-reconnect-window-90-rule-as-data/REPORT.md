# docs-flow-eval: the kit's new flow (rule as data), 2026-10-14

**Scenario:** reconnect-window-90, fixture b (sheet answer `ok`). **Arm:** `current-prd-flow`, rewritten for rule as data: the kit branch overlaid on the scenario base (`worktrees.py setup --kit`), the frozen sheet and pack as the survey, one `docs-eval-executor` dispatch following the overlaid `prd-flow-executor.md`, then the chief runs the change gate and `quality.py`.
**Not run:** reviews, baseline, full-suite compare, `gates.sh close`, human waits.

## Acceptance (plan row "Eval")

| Criterion | Target | cur-3 | cur-4 |
|---|---|---|---|
| Executor time | at most 7 min | 7.0 | 6.2 |
| Docs gate failures | 0 | 0 | 0 |
| Blind reader | 5/5 | 5 | 4.5, then 5 with the frozen CHANGELOG note |

## Efficiency

| Run | Kit | Elapsed min | Turns | Input tokens | Tool calls | Stale | Reader |
|---|---|---|---|---|---|---|---|
| cur-1 | f0d0546..383d3e3 | 6.0 | 36 | 2.70M | 106 | 1 | - |
| cur-2 | same | 6.4 | 47 | 3.88M | 124 | 1 | - |
| cur-3 | 12558da | 7.0 | 46 | 4.18M | 125 | 0 | 5 |
| cur-4 | 12558da | 6.2 | 37 | 3.37M | 122 | 0 | 4.5 / 5 |

Against the old prd-flow (fixture a: 18.5 min, 5.5 dispatches, 7.1M tokens, gate failures in 4 of 9 runs), the new flow takes one dispatch, about a third of the time and half the tokens, with no gate failure. Against the v2 and v3 arms it costs the same time (6.6 against 5.7 and 6.3 min) and v2's tokens (3.8M against 3.9M; v3 2.8M).

## Found and fixed in this round

| ID | Finding | Fix |
|---|---|---|
| F1 | cur-1 and cur-2 copied "(today: it stops at 60 s)" from the sheet's Becomes text into CNX-01: the kit executor had lost rule V02 of the v2 arm | 12558da: a row holds today's rule only, even when the sheet carried a note |
| F2 | cur-2 rewrote the DEC rows of the open change 003 to 90 s; cur-1 left them | 12558da: a `decisions.md` is a record, never rewritten |
| F3 | A reader of a CHANGELOG without a frozen note concluded "no rejected alternative is recorded" although the commit body had it (`gate.py --history CNX-10` prints it) | update.md U6h "Migration to rule as data" adds the frozen note on update; a fresh reader then scored 5/5 |

## Open

- cur-4 left "at most 60 s" in line 6 of `changes/003-conversation-reconnect/brief.md`; `quality.py` Q1 scans only `docs/`, not open change folders.
- The countdown's screen-reader behavior (decision 1A) has no unit test in any run: the unit project collects only `.test.ts`.
