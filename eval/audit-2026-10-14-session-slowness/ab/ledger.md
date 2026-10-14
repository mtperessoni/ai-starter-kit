# A/B ledger

Session dir: ~/.claude/projects/c--Projects-agora-consulta-fe/9265d548-d0d5-4a50-b285-cedd7f057040
Base: 46b66879. Scenario: reconnect window 60 s to 90 s plus countdown (slug reconnect-window-90). Sheet answer for every arm: `ok`.

| Arm | Stage | Agent | Model |
|---|---|---|---|
| shared | surveyor full | a59abdea46f61aee8 | opus |
| A1 | docs apply | a24395d2b07e8796a | opus |
| A2 | docs apply | aa412b1858674ceaa | opus |
| B1 | executor (contract B) | a92a9355ee7fe0ed5 | sonnet |
| B2 | executor (contract B) | aa44ef3b3b7303604 | sonnet |
| A2 | executor task T01 | a4a4b570bd6109709 | sonnet |
| A1 | executor task T01 | a336590eccfdbb01f | sonnet |
| A2 | executor task T02 | a0f5a739cbcdd0c24 | sonnet |
| A1 | executor task T02 | aef17c28614bd02eb | sonnet |
| A2 | executor close C5 | a584e597b68ba4f10 | sonnet |
| A1 | executor close C5 | a108600366063bb2d | sonnet |
| A2 | executor fix (tsc after close) | ae37a457fc55802eb | sonnet |

| A2 | executor fix commit 2c213efe | ae37a457fc55802eb | sonnet |
| A2 | executor close C5 rerun | a5ee5ec0acee0694e | sonnet |

A2 close rerun blocked again: "no compare result for this test content" (the fix changed the tree; DP07 requires a new compare). Chief reran compare (compare-A2b.log), then a third close.

| A2 | executor close C5, third run | a082abb2d507c93ac | sonnet |

All four readers first stopped (the W junctions resolved to forbidden A/B paths, a prompt defect of mine); each was resumed with an explicit allowance for its own target. Reader metrics count both legs.

| Reader | Agent |
|---|---|
| W1 | a9408ec74d4658bfb |
| W2 | a587d60cf2819b2ff |
| W3 | a6d0fced41f38454b |
| W4 | aab45c5dae898239a |

Blind aliases (junctions): W1 = B2, W2 = A1, W3 = B1, W4 = A2. Readers get only W paths and the five questions, never grader-questions.md.

A2 close blocked: tsc failed, `reconnectDeadline` missing from `ConversationSession` because T01 and T02 split the hook state and the interface across two executors. Promote already committed 2379aa5a.

Infra notes: `gates.sh baseline` failed twice per A worktree before succeeding: (1) the temp copy under the 8.3 path `PERESS~1` makes vite fail to load the 10 test files whose paths hold `[triageId]` and `(internal)`; (2) `new_failures.has_summary` does not strip ANSI colors, so vitest's colored `Test Files` line never matches. Workaround: TEMP on a long path plus NO_COLOR=1. Baselines are chief work and are excluded from both arms' agent metrics.

Notes: A2 docs committed f4ae2ac0 with 3 G28 errors (sibling drift of triage-documents with modulo-integrador, out of scope); plan = 2 tasks in 2 waves with a review after wave 1 (reviews not run in either arm). B1 e4dd675c, B2 08cf8674: one commit each; neither edited INDEX (contract B04).
