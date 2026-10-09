# Survey (surveyor)

Read by heading (`Grep -n "^## "`, then a ranged `Read`): `query` and `light` need "Cases", "Sweep" (step 1 and F3), "Proof", "Survey section"; `full` and `short` all. Examples are illustrative.

## Cases
| Case | When | Signals |
|---|---|---|
| C0 no PRD | No `docs/prd/INDEX.md`, only that | "create the PRD", first use in the repository. Report it: `/prd-create`, then `/trd-create` |
| C1 query | How or why something works | "how", "why", "what happens if". Each rule cited `verified in code` (`functional`) or `not verified: <verdict>`; `gate.py --status` for rule states. A diagnosis gives cause and options, no change |
| C2 implement | The rule exists, is approved, the code does not meet it | a row marked `pending code`, "the spec still lacks X". A one-task change: the card. Over one task (pieces in disjoint areas, or the TRD must change): no card, `Route: docs plan` |
| C3 bug | Code differs from the PRD, the user confirms the PRD | "it is broken". The card; the PRD changes only if the Source moves |
| C4 stale PRD | Code right, PRD says otherwise, confirmed | drift, a removed env var, a cited file gone. No card: the divergence block in `## Survey` |
| C5 rule change | Changed rule, new rule, gap, or a fix to a defect the PRD documents as today's behavior | "change", "it should", "from now on", "add" |
| C6 refactor | Structure changes, behavior does not | "rename", "extract", "move", "split". The card carries the area TRD and the invariants |

Mode: C1 `query`; C2, C3, C4, C6 `light`; C5 `full`; mid-execution `short`. With `unclear`, or a case other than the prompt's, classify here, run the mode that fits and say so on the first return line.

| Size | When | Change folder (`write.md` "Change folder") |
|---|---|---|
| S | C1, C2, C3, C4, C6; never a C5 | none, or `card.md` in the state folder |
| M | C5 with an evident design: no new data model, contract, external dependency or technical unknown; a one-row change is M | `decisions.md`, `plan.md` |
| L | C5 with a new data model, contract, external integration, technical unknown, feature area or PRD | `brief.md`, `design.md`, `decisions.md`, `plan.md` |

A new product context (a product, module or incoming spec that runs on its own) in a repository with PRDs is C5 size L, new PRD variant, never C0: sweep it against every PRD of the INDEX (K11). Only `/prd-create` writes `*(proposed)*` rows; a proposed row is C5 input, never C2.

| Trap | Case | Why |
|---|---|---|
| "Fix X" where the PRD documents X as today's behavior | C5 | fixing it decides a new rule |
| "Add an if for customer X" | C5, protected rule | per-tenant behavior is configuration, never a branch on the name |
| A prompt or config value "just a little" | C5 | it changes via `prompt` or `config` and follows `repo.md` "Change routing" |
| A refactor that needs another limit, text or order | C5 | no longer structure only |
| The request cites a row marked superseded | ask | the amendment may be unknown or not deployed |
| No matching rule | C5 (gap) | behavior without a rule enters the PRD first |
| Several items | one case each | a C3 not touching the C5 rules may be fixed first, once confirmed |
| "Diagnose", "plan" | C1 | until the user asks for a change |
| `pending code` with code committed but no caller outside tests | C2 | not wired, still pending |

A real session: to explain what the system did, return `Route: user` asking for its id and, once authorized, read the evidence (`repo.md` "Evidence of real sessions") before concluding; without it, name the code paths and the evidence that would tell them apart.

## Divergence
Returned as the `Route: user` question, which the chief asks as is:
```
ORD-03 · PRD: "An order is cancelled after 30 minutes without payment (ORDER_PAYMENT_TIMEOUT)."
Code: the env var is gone from src/infra/config/settings.py; the timeout lives in PaymentConfig (src/features/orders/config.py).
Which is right?
- The code (the PRD is stale: case C4)
- The PRD (the code regressed: case C3)
- Neither (a new rule: case C5)
```
Diverges: the cited file or symbol is missing; it has no caller outside tests; a number or name differs; the flow is not what the code does. A wording difference with no effect is not a divergence. `Next:` "PRD right: executor task with card.md; code right: docs `c4`; neither: surveyor `full`".

## Sweep
1. `scripts/gates.sh prd-sweep --ids <ID,ID> --terms "<entities, actors, states, numbers>" --out <state>/sweep.md` (timeout 300000): in batch 1 with the IDs the request names, else right after the INDEX Grep. It prints the literal Rules, Cited by (K01), Same table (K02), Candidates from INDEX by terms (K11), Unconditional rows (K14 candidates), History (K12), Active changes (K06 local), Tests citing each ID (K05) and Code per Source symbol with its F1 and F2 verdicts and `F3: read path::symbol`.
2. Read `sweep.md` once, then judge what the script cannot:

| ID | Judgment |
|---|---|
| F3 | Per `F3:` line read the symbol by range and compare numbers, names, branches, states and flow with the row and its Example |
| K03 | Variants where `repo.md` documents them: a rule citing one variant almost always has a pair |
| K04 | Tenants where `repo.md` documents them; per-tenant differences |
| K05 | `docs/trd/invariants.md` lines for the kind of change |
| K06 remote | Each in-scope ID, the next free IDs and the change number in the newest 30 refs of `git for-each-ref refs/remotes` (`git grep -l "<ID>" <ref> -- docs/prd changes`); a hit is a diff row or a decision |
| K07 | Linked `Q-`, `R-`, `S-` rows; what consumers persist; the Change via column; README "What weighs most today" |
| K08 | A field, value or key that reaches another repository: its validation there (`repo.md` "Consumers"); a value it rejects breaks the delivery |
| K09 | A list, guard, fallback, switch or wait removed or loosened: what it covered and what becomes uncovered; a sheet decision, never an extra task |
| K10 | What proving the rule needs (a real model, a database, a backend); without it the sheet says the proof stays pending and who runs it |
| K11 | Read the rule tables of up to 8 candidate sections; list each rule the proposal contradicts, constrains or duplicates |
| K12 | Per ID with history: `Decided <date>: <why>; rejected: <alternative> (<why>)` |
| K13 | `repo.md` "Rule owners": name the owner, add the owner item; "Shared PRDs": name the sibling that must receive the change |
| K14 | Per unconditional candidate (a fixed value, "always", "every", "never"): does the new rule make it false for some input? Then it conflicts and is rewritten (same ID) or superseded, never "unchanged". Example: "Shipping costs 15.00." against "free above 100.00" rewrites SHP-01 |

| Scope | Judgment |
|---|---|
| Size L, more than one PRD section, or a reused ID | all of the above |
| Size M, one section | F3, K09, K11, K14; K12 for the IDs it edits; K07, K08, K10, K13 only when the pack shows the trigger; K03 to K05 where `repo.md` documents them |
| `short` | F3, K11, K12, K14 on the touched rules |

K11, K12 and K14 are never skipped for the IDs the change touches. Large code: Grep by symbol, read by range; never whole files, never a subagent.

## Proof
One verdict per rule in scope: `functional` · `diverges: <what the code does, path::symbol>` · `not wired: no caller outside tests` · `missing: <path::symbol> not found` · `planned` (Source `planned`). F1 and F2 come from the sweep, F3 from your read. When the rules exceed the budget, prove the touched ones first and report the rest `not verified`.

## Conflicts
Every conflict of K01, K11 or K14 is, with the same IDs, a `rewrites` or `supersedes` row of the sheet diff (never a separate question) and a line of the pack: `Conflicts: <IDs>` (or `none`), each with why and the proposed resolution (`rewrite`, `supersede`, `compatible: <why>`).

## Protected rules
Always protected, besides `repo.md` "Protected rules": an invariant covered by a structural test (`docs/trd/invariants.md`; changing it needs an ADR or a constitution amendment), a registered exception to a principle (a new ADR), a safety control (an ADR and the safety reviewer). Only a protection the change breaks or touches goes to `Protected:` and becomes the first sheet item ("<protection in plain words> still holds? / It holds: <right path> / The document is stale"); one checked and intact goes to a `Checked: <file read>` line. Docs `apply` writes the ADR; a constitution amendment goes back to the user.

## Pack
`<state>/pack.md`, complete for the docs agent, which never reads source; `gate.py --pack <pack>` checks the sections and that every row is literal. Rows grouped by file:
```markdown
# Pack · <slug>
Base: <short commit> · Branch: <name> · Behind origin/<base_branch>: <n> (touches the scope: yes|no)
Request: <one line>
Conflicts: <IDs, or "none">
Checked: <files read>

## Rules
### docs/prd/product/04-checkout.md
| CHK-02 | <row copied exactly from the PRD> |

## Rows without ID
## TRD
- docs/trd/checkout.md · src/features/checkout/payment_call.py::call_provider (caller: routes.py::pay)
## Invariants
## Principles
## Open questions linked
## Changes and tests
## Divergences
- in scope: <PRD says / code does, file::symbol>
- out of scope: <path::symbol> <what it does today> (<rule ID>)
```
An out-of-scope divergence is copied by the plan under `Leave:` so no task changes it silently.

## Survey section
`## Survey` of `state.md` is yours alone: replace it whole on each run (`short` appends a dated `### Short <YYYY-MM-DD>` block). At most 10 lines:
```markdown
## Survey
Case: C5 · Size: M · Approver: <git config user.name> · Base: <short commit> · Mode: full
Contexts: product/04: 3 rows · fan-out: no
Python: <interpreter>
Protected: none
Owner: none
Sheet: <state>/sheet.md · Pack: <state>/pack.md
```
`fan-out: yes` when two or more PRD folders or TRD areas have more than about 5 rows each. `light` holds Case, Approver, Base, Mode, one line per rule (`<ID> · <file> · <verdict>`), the divergence block when there is one (docs `c4` reads it) and `Card: <path>` or `Card: none (<reason>)`.
