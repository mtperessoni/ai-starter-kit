# docs-flow-eval: rule-as-data v2 and v3, 2026-10-14

**Scenario:** reconnect-window-90, fixture b. The sheet has one decision: how a screen reader hears the countdown; the answer was `ok`, so 1A.

**Runs:** two of each arm.
- `rule-as-data-v2`: v1 plus P1 to P5, run on `general-purpose` with Sonnet.
- `rule-as-data-v3`: v2 plus cost rules, run on the dedicated `docs-eval-executor` agent.

**Baselines:** the current prd-flow and v1 were not rerun. Their rows in `../history.md` are from the same day on fixture a. Costs compare across the fixtures; the decision record does not.

**Not run:** reviews and human waits.

## Efficiency (mean of two runs)

| Arm | Dispatches | Elapsed min | Turns | Input tokens | Tool calls | Docs gate fails |
|---|---|---|---|---|---|---|
| current-prd-flow (fixture a) | 5.5 | 18.5 | 109 | 7.1M | 206 | 4 of 9 runs |
| rule-as-data-v1 (fixture a) | 1 | 5.5 | 34 | 4.1M | 101 | 0 |
| rule-as-data-v2 | 1 | 5.7 | 34 | 3.9M | 87 | 0 |
| rule-as-data-v3 | 1 | 6.3 | 38 | 2.8M | 100 | 0 |

Context per turn, which drives the token cost:

| Arm | Start | Mean | Peak |
|---|---|---|---|
| v2 (`general-purpose`) | 57k | 117k | 144k |
| v3 (dedicated agent) | 24k | 72k | 99k |

## Context kept and PRD function

| Check | v2-1 | v2-2 | v3-1 | v3-2 | v1 (before) |
|---|---|---|---|---|---|
| No stale old value anywhere in docs/ | ok | ok | ok | ok | 1 of 2 failed |
| Rule rows match the sheet; CNX-10 added | ok | ok | ok | ok | ok |
| INDEX current (generated) | ok | ok | ok | ok | no |
| Decision and rejected alternative recorded | ok | ok | ok | ok | no |
| Red evidence in the commit | ok | ok | ok | ok | no |
| New test files (hook, countdown) | 2 | 2 | 2 | 1 | 0 |
| Changed tests pass | 16 | 15 | 15 | 23 | ok |
| Full unit suite | 1289 | 1288 | 1288 | 1288 | ok |
| gate_lite (L1 to L6) | 0 | 0 | 0 | 0 | 1 |
| Current gate.py | G7 only | G7 only | G7 only | G7 only | G2 + G7 |
| Blind reader (5 questions) | 5 | 5 | 5 | 5 | 4.5 |

The current gate now fails only on G7, the hand-written CHANGELOG line per rule, which the proposal replaces with the commit body. G2 is gone because the INDEX is generated.

## Verdict

- **P1 to P5 close the context gap at no cost.** v2 matches v1 on time (5.7 against 5.5 min) and uses fewer tool calls. All four readers scored 5/5 against 4.5 for v1, and every PRD check holds: rows as approved, INDEX current, no stale value, decision and red evidence in the commit.
- **The dedicated executor agent cuts context by 38%.** Start context fell from 57k to 24k and mean context from 117k to 72k, giving 2.8M against 3.9M input tokens, with no loss of quality.
- **v3 did not cut time.** The contract's cost rules (X02 bounded output, X03 batched edits, X06 a ceiling of 60 calls) were not followed: 45 to 53 Edits and 91 to 109 calls. A rule in a contract does not change how many Edits an agent makes.
- **Time is set by turns, not by tokens.** A single executor needs about 5.5 to 7 min for an 18-file change.

## Found by this round

| ID | Finding | Action |
|---|---|---|
| E1 | `Assumed: A1..A8` names IDs whose text lives only in the git-ignored sheet (3 of 4 readers) | Done: V08 now asks for each assumption in words |
| E2 | Open change folders that restate a rule (`changes/003-conversation-reconnect`) go stale when the rule changes | V03's old-value Grep should list open change folders too, or open folders must not restate values |
| E3 | The surveyor is now the largest stage. It takes about 7 min on Opus with about 2.1M input tokens, more than the executor. It spends 54 s on base lint and setup and rereads its own 33 KB `sweep.md` | Next arm: a lean surveyor (no base lint, no sweep reread, a dedicated agent with a small base) |
| E4 | Edits cost about 1.2 s each in the IDE session and runs make about 50 of them | Untested: compare the same arm run from the CLI, without IDE diagnostics |
| E5 | The sheet changes between surveyor runs. Fixture a decided "stop the attempt at zero", fixture b "screen reader hears once" | Fixtures are frozen per scenario; a new survey is a new fixture |

## End to end

| Flow | Survey | Executor | Approvals | Total |
|---|---|---|---|---|
| Current | about 7 min | 18.5 min | sheet and `diff.md` (2 human rounds) | about 25.5 min |
| v2 or v3 | about 7 min | about 6 min | sheet only (1 human round) | about 13 min |

The next gain is in the survey (E3), then the edit cost (E4).

## Limits

- Two runs per arm, one scenario, in the FE repository, where the docs are small.
- Reviews were not run.
- v3 changed the agent and the contract together. The token gain is attributed to the agent (start context) and not to the contract, whose rules were not followed.
