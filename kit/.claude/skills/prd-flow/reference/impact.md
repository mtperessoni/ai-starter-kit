# Survey, confrontation and impact (read by the surveyor only)

IDs, texts and paths in the examples are illustrative: always read the real line. Read this file by heading (`Grep -n "^## "`, then `Read` with offset and limit): `light` mode needs only "Functional proof", "Prepared questions" and "Survey section"; `full` and `short` need all of it.

## Functional proof
Every rule the request touches, and every rule the answer or the change relies on, is proven against the code before anything is said about it. Per rule:

| Step | Check | How |
|---|---|---|
| F1 | The Source exists | `Grep -n "<symbol>" <path>`; Source `planned` skips to the verdict `planned` |
| F2 | It is wired | a caller outside the test folders: `Grep -n "<symbol>"` across the source folders of `ai-kit.json`, excluding its own definition and the tests |
| F3 | It does what the row says | read the symbol by range and compare numbers, names, branches, states and the flow with the row text and its `Example` |

Verdict, one per rule: `functional` · `diverges: <what the code does, path::symbol>` · `not wired: no caller outside tests` · `missing: <path::symbol> not found` · `planned`. A wording difference with no effect on behavior is `functional`. The criteria and the divergence block are in `classification.md` "PRD versus code divergence". In `query` mode each rule cited in the answer carries `verified in code` (verdict `functional`) or `not verified: <verdict>`.

## Sweep
| ID | Where to look | How |
|---|---|---|
| K01 | Rules that cite the ID | `Grep "<ID>" docs/prd` outside its own row |
| K02 | Same section and neighboring sections of the journey | Rows of the same table; the previous and next step of the end-to-end journey |
| K03 | Variants | Where `repo.md` documents them. A rule that cites only one variant almost always has a pair in the other |
| K04 | Tenants | Where `repo.md` documents them; per-tenant differences |
| K05 | Invariants and tests | `docs/trd/invariants.md` for the kind of change; `Grep "<ID>\|FR-0NN"` in the test folders for tests citing the rule or the FR |
| K06 | Active changes, local and remote | `Grep "<ID>" changes --glob "!archive/**"`; a change folder in progress in the area. Remote: for each in-scope ID, the next free IDs and the next change number, take the most recent 30 of `git for-each-ref refs/remotes` and `git grep -l "<ID>" <ref> -- docs/prd changes`. A hit goes to the confrontation and becomes a question. `gh pr list` only when `gh` is available |
| K07 | Open questions, contract, governance | Linked `Q-`, `R-`, `S-` rows; what consumers persist; the Change via column; README "What weighs most today" |
| K08 | Consumer contract in a sibling repository | If the change touches a field, value or key that goes to another repository, check its validation there (commands in `repo.md`). A value the consumer does not accept breaks the whole delivery |
| K09 | Safety net removed or weakened | Does the change remove or loosen a list, guard, fallback, switch or wait? List what it covered and what becomes uncovered (failure, delay, end of session, disconnection). It becomes a trade-off and a question; never an extra task during execution |
| K10 | Verification prerequisites | What proving the rule requires: a real model (API key in the environment?), a database, a backend. Without it, say in the confrontation that the proof stays pending and who runs it |
| K11 | Semantic sweep across every PRD | `docs/prd/INDEX.md` has one section per PRD: Grep it for the subject's entities, actors, states and numbers (never read it whole) and take candidates from every PRD, not only the one the request names. Pick up to 8 section files whose subject could interact (same entity, actor, state, number or journey step), read their rule tables, and list each rule the proposal would contradict, constrain or duplicate. A rule phrased with other words is found here, not by K01 |
| K12 | History | `Grep` each in-scope ID in `docs/prd/CHANGELOG.md`; per ID with history show `Decided <date>: <why>; rejected: <alternative> (<why>)` from the entry's Decisions block |
| K13 | Rule owner and shared PRD | `repo.md` "Rule owners": when the change touches an owned section, name the owner and prepare the owner question. `repo.md` "Shared PRDs": name the sibling repository path that must receive the same change |
| K14 | Unconditional rules the new rule makes false | For every candidate row of K01, K02 and K11 stated without a condition (a fixed value, price or limit; "always", "every", "never"), ask: does the new rule make it false for some input? If yes, it is a conflict, never "unchanged": it is rewritten in the same row (same ID, new text) or superseded. Example: "Shipping costs 15.00." against a new "shipping is free above 100.00" is a conflict; SHP-01 is rewritten as "Shipping costs 15.00, free above 100.00" |

### Sweep by size
| Case | Sweep |
|---|---|
| Size L, a change touching more than one PRD section, or a request that reuses an existing ID | Full: K01 to K14 |
| Size M touching one section | K01, K02, K06 (local), K09, K11, K14; K12 only for the IDs it edits; K07, K08, K10, K13 only when the pack shows the trigger; K03 to K05 where `repo.md` documents variants, tenants or invariants for the area |
| `short` | K01, K02, K11, K12, K14 on the touched rules only |

The confrontation always prints `Checked:` and `Conflicts:`. K11, K12 and K14 are never skipped for the IDs the change touches. Large code: Grep by symbol and read by range; never whole files, never a subagent.

## Conflicts
Every conflict K01, K11 or K14 finds is recorded with the same IDs in:

| Where | What |
|---|---|
| `impact.md` of the state folder and `## Survey` | The `Conflicts:` line, each ID with why it conflicts and the proposed resolution (`rewrite`, `supersede`, or `compatible: <why>`) |
| `pack.md` | The header line `Conflicts: <IDs>`, or `Conflicts: none` |
| `approved-rules.md` | One row per ID in the `## Conflicts` table, Resolution and Note left empty for the docs agent in `rules` mode; a conflict to rewrite also gets its row under its file heading with the current text |

## Pre-interview states
The surveyor writes them into the `interview.md` scaffold, one row per dimension D01 to D15 and the extra ones of `repo.md`:

| State | Meaning |
|---|---|
| `doc: <source>` | The PRD states it and the change does not touch it |
| `assumed: <proposed default and where it comes from>` | Inferred from current code, or the change touches it |
| `open: <question with scenario and recommended default>` | Nothing answers it |
| `n/a: <reason>` | Does not apply |

A dimension the change touches is never `doc`. The assumed ones go into one block of at most 6 lines that the user confirms or corrects with the change question.

## Prepared questions
The chief only asks: every question reaches it ready, in `## Survey` (interview rounds) or in the `Route: user:` field (the one question that decides the next dispatch). Format of each question:

```
Q1 · D05 · "The payment provider takes 45 s to answer: what does the customer see?"
  - "Try again" after 20 s, cart kept (Recommended): fewer stuck carts; a slow success may be charged twice on retry
  - Wait up to 60 s: fewer false failures; the customer waits longer
  - Keep today's 30 s: no change; the complaints stay
```

| Rule | Detail |
|---|---|
| Language | Product language with a concrete scenario and the effect on the user, the operator or the stored record. No rule IDs, symbol names, internal acronyms or words like "flag", "key", "handler" in the quoted text; the `Q1 · D05` label is for the docs agent only |
| Options | Two to four, each with its trade-off; the recommended one first, marked "(Recommended)" |
| Rounds | At most 4 questions per round; more open dimensions make more rounds, in the order that unblocks the most rows |
| Never asked | Anything the code or the PRD already answers |
| Order | Protected rule and rule owner questions first, then the change question, then the interview rounds |

The change question (full mode, in `Route: user:`): "Change the rule as proposed, with the assumed lines above? / Keep today's rule (the request becomes a fix or nothing) / Adjust the proposal (say how)". A protected rule question: "<protection in plain words> still holds? / It holds: <right path, an ADR or a constitution amendment> / The document is stale". An owner question: "<owner> owns this rule: did they agree?".

## Survey section
`## Survey` of `state.md` is the surveyor's only section; the chief reads it to show and ask, so it is complete without any other file. Replace it whole on each run (append a dated `### Short <YYYY-MM-DD>` block in `short` mode); never touch another section.

```markdown
## Survey
Case: C5 · Size: M · Approver: <name> · Base: <short commit> · Mode: full
Contexts: product/04: 3 rows · fan-out: no
Python: <interpreter>
Protected: none   [or: <rule or invariant> · <source> · <right path>; only a protection the change breaks or touches, an untouched one goes to a Checked: line]
Owner: none   [or: <owner> owns product/04-*]
Scaffolds: pack.md, impact.md, interview.md, approved-rules.md, changes/007-checkout-timeout/decisions.md
Confrontation
  <the confrontation, at most 25 lines, 15 in short mode>
Questions
  <round 1, at most 4 questions in the format above; then round 2 ...>
```

In `light` mode the section holds `Case`, `Approver`, `Base`, `Mode`, one line per rule (`<ID> · <file> · <verdict>`), the divergence block when there is one (the docs agent in `c4` mode reads it: rule ID, PRD text, what the code does, Source) and `Card: <path>` or `Card: none (<reason>)`.

## Confrontation format
```
Current rule · CHK-02 (product/04-checkout.md) · functional
  "<literal row text>"  · Source: src/features/checkout/payment_call.py · Change via: config
Proposal
  "<how it would read>"
What changes
  Customer: ...   Operator: ...   Backend: ...
Checked: product/04-checkout.md CHK-01..CHK-14, product/06-orders.md ORD-01..ORD-09
Conflicts: ORD-03 (cancels at 30 min while a payment may still be waiting; propose rewrite)   [or: none found in the checked files]
History
  CHK-02 Decided 2026-03-02: 30 s matches the provider SLA; rejected: 10 s (too many false failures)
Impact
  Rules: CHK-05 (same timeout on retry), ORD-03
  Remote branches: none   [or: feat/x touches CHK-02]
  Variants: web and mobile; mobile retries in background
  Tenants: all (shared config)
  Tests: src/features/checkout/tests/test_payment_call.py cites CHK-02
  Change: 007-checkout · Open: Q-CHK-04
Assumed (confirm or correct, at most 6 lines)
  - D04 numbers: 20 s, from PaymentConfig default
Trade-offs and risks
  - A shorter wait fails more slow-but-successful payments: possible double charge on retry
  - Rollback: config, publish the previous version
```

Trade-offs to always consider: safety and risk to the user, regression of another rule, cost and latency, privacy and personal data, rollback, audit, in-flight sessions during the transition, effects on systems being migrated.

## Format of `pack.md`
The pack is complete for the docs agent, which never reads source: literal rule rows, the file and symbol map, conflicts, Leave items, the `DEC-` rows once written, contexts. `gate.py --pack` checks the sections and that every rule row is literal. Rows are grouped by file, whatever PRD they belong to.

```markdown
# Pack · <slug>
Base: <short commit> · Branch: <name> · Behind origin/<base_branch>: <n> (touches the scope: yes|no)
Request: <one line>
Conflicts: <IDs, or "none">

## Rules
### docs/prd/product/04-checkout.md
| CHK-02 | <row copied exactly from the PRD> |

## Rows without ID
### docs/prd/product/04-02-limits.md
| 5 | <row copied exactly from the PRD> |

## TRD
- docs/trd/checkout.md · src/features/checkout/payment_call.py::call_provider (caller: src/features/checkout/routes.py::pay)

## Invariants
- <ID> <one line>

## Principles
- III <one line>

## Open questions linked
- Q-CHK-04 <one line>

## Changes and tests
- src/features/checkout/tests/test_payment_call.py (imports call_provider)

## Divergences
- in scope: <PRD says / code does, with file::symbol>
- out of scope: <path::symbol> <what it does today> (<rule ID>)

## Pre-interview
- States in `interview.md`
```

An out-of-scope divergence is listed so the plan copies it under `Leave:` and no task changes it silently.

## Protected rules
The repository's list is in `repo.md`, "Protected rules". Always protected, in any repository:

| Protection | Source | Right path |
|---|---|---|
| Invariant covered by a structural test | `docs/trd/invariants.md` | Changing the invariant is a repository rule change: ADR or constitution amendment |
| A registered exception to a principle | constitution, ADR | A new ADR to change the exception |
| A safety control | constitution | Loosening it requires an ADR and the safety reviewer |

With a protection the change breaks or touches (not one merely checked and left intact): name it, its source and the right path in `## Survey` `Protected:`, and prepare the protected rule question. The chief records the answer in `## Chief` (`Protected: <ID> · ADR`, constitution amendment, or "stale"); the docs agent in `prd` mode writes the ADR; a constitution amendment goes back to the user.
