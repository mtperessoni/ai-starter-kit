# Ledger: reconnect-window-90, current-prd-flow (rule as data), 2026-10-14

Kit under test: branch `feat/docs-flow-eval` at 3212cc2 plus 383d3e3, overlaid by `worktrees.py setup --kit`. Fixture b (sheet answer `ok`).

| Run | Stage | Agent id | Model | Gate base (seed) |
|---|---|---|---|---|
| cur-1 | executor | a8635864c59c81066 | docs-eval-executor default | d9d9d125 |
| cur-2 | executor | af7da4b71a6cb4267 | docs-eval-executor default | 64c7383d |
| cur-3 | executor (kit 12558da) | a1f90ee9ed6e0675b | docs-eval-executor default | 1af86ff4 |
| cur-4 | executor (kit 12558da) | ac3454c4403b21183 | docs-eval-executor default | 79c74183 |

cur-1 and cur-2 both left "(today: it stops at 60 s)" in the CNX-01 row (copied from the fixture's Becomes text); cur-2 also rewrote the DEC rows of the open change 003. Fixed in the executor contract (12558da) and rerun as cur-3 and cur-4.
