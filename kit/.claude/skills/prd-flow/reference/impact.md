# Confrontation and impact (C5, read by the surveyor agent)

IDs, texts and paths in the examples are illustrative: always read the real line.

## Sweep
| ID | Where to look | How |
|---|---|---|
| K01 | Rules that cite the ID | `Grep "<ID>" docs/prd` outside its own row |
| K02 | Same section and neighboring sections of the journey | Rows of the same table; the previous and next step of the end-to-end journey |
| K03 | Variants | Where `repo.md` documents them. A rule that cites only one variant almost always has a pair in the other |
| K04 | Tenants | Where `repo.md` documents them; per-tenant differences |
| K05 | Invariants and tests | `docs/trd/invariants.md` for the kind of change; `Grep "<ID>\|FR-0NN"` in the test folders for tests citing the rule or the FR |
| K06 | Active changes, local and remote | `Grep "<ID>" changes --glob "!archive/**"`; a change folder in progress in the area. Remote: for each in-scope ID, the next free IDs and the next change number, take the most recent 30 of `git for-each-ref refs/remotes` and `git grep -l "<ID>" <ref> -- docs/prd changes`. A hit goes to the confrontation and is asked about. `gh pr list` only when `gh` is available |
| K07 | Open questions, contract, governance | Linked `Q-`, `R-`, `S-` rows; what consumers persist; the Change via column; README "What weighs most today" |
| K08 | Consumer contract in a sibling repository | If the change touches a field, value or key that goes to another repository, check its validation there before the interview (commands in `repo.md`). A value the consumer does not accept breaks the whole delivery |
| K09 | Safety net removed or weakened | Does the change remove or loosen a list, guard, fallback, switch or wait? List what it covered and what becomes uncovered (failure, delay, end of session, disconnection). It becomes a trade-off in the confrontation and an interview question; never an extra task during execution (review.md V06) |
| K10 | Verification prerequisites | What proving the rule requires: a real model (API key in the environment?), a database, a backend. Without the prerequisite, say in the confrontation that the proof stays pending and who runs it |
| K11 | Semantic sweep across every PRD | `docs/prd/INDEX.md` has one section per PRD: Grep it for the subject's entities, actors, states and numbers (never read it whole) and take candidates from every PRD, not only the one the request names, because a conflict can live in another context. Pick up to 8 section files whose subject could interact (same entity, actor, state, number or journey step), read their rule tables, and list each rule the proposal would contradict, constrain or duplicate. A rule phrased with other words is found here, not by K01 |
| K12 | History | `Grep` each in-scope ID in `docs/prd/CHANGELOG.md`; per ID with history show `Decided <date>: <why>; rejected: <alternative> (<why>)` from the entry's Decisions block |
| K13 | Rule owner and shared PRD | `repo.md` "Rule owners": when the change touches an owned section, name the owner. `repo.md` "Shared PRDs": when the PRD folder is shared, say the sibling repository path that must receive the same change |
| K14 | Unconditional rules the new rule makes false | For every candidate row of K01, K02 and K11 stated without a condition (a fixed value, price or limit; "always", "every", "never"), ask: does the new rule make it false for some input? If yes, it is a conflict, never "unchanged": it must be rewritten in the same row (same ID, new text) or superseded. Example: "Shipping costs 15.00." against a new "shipping is free above 100.00" is a conflict; SHP-01 is rewritten as "Shipping costs 15.00, free above 100.00" |

### Sweep by size
| Case | Sweep |
|---|---|
| Size L, a change touching more than one PRD section, or a request that reuses an existing ID | Full: K01 to K14 |
| Size M touching one section | K01, K02, K06 (local), K09, K11, K14; K12 history only for the IDs it edits; K07, K08, K10, K13 only when the pack shows the trigger (a linked `Q-` row, a consumer field, a verification prerequisite, an owned or shared section); K03 to K05 where `repo.md` documents variants, tenants or invariants for the area |

The confrontation still prints `Checked:` and `Conflicts:` in every case. K11, K12 and K14 are never skipped for the IDs the change touches; in the short C5 they run on the touched rules only.

Sweep of large code: Grep by symbol and read by range; never whole files, never a subagent.

## Conflicts
Every conflict K01, K11 or K14 finds is recorded in three places, with the same IDs:

| Where | What |
|---|---|
| `impact.md` | The `Conflicts:` line of the confrontation, each ID with why it conflicts and the proposed resolution (`rewrite`, `supersede`, or `compatible: <why>`) |
| `pack.md` | The header line `Conflicts: <IDs>`, or `Conflicts: none` |
| `approved-rules.md` | One row per ID in the `## Conflicts` table, Resolution and Note left empty for the main thread (format in `interview.md` "Records"); a conflict that will be rewritten also gets its row under its file heading with the current text, so the main only edits the text |

## Pre-interview states
The single home of these states (the surveyor and `interview.md` cite it). The surveyor writes them into the `interview.md` scaffold, one row per dimension D01 to D15 and the extra ones of `repo.md`:

| State | Meaning |
|---|---|
| `doc: <source>` | The PRD states it and the change does not touch it |
| `assumed: <proposed default and where it comes from>` | Inferred from current code, or the change touches it |
| `open: <question with scenario and recommended default>` | Nothing answers it |
| `n/a: <reason>` | Does not apply |

A dimension the change touches is never `doc`. The confrontation shows the assumed ones in one block of at most 6 lines; the user confirms or corrects them explicitly before the interview.

## Confrontation format
```
Current rule · CHK-02 (product/04-checkout.md)
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
  Owner: none   [or: <owner> owns product/04-*; the user must state they agreed]
  Variants: web and mobile; mobile retries in background
  Tenants: all (shared config)
  Tests: src/features/checkout/tests/test_payment_call.py cites CHK-02
  Change: 007-checkout · Open: Q-CHK-04
Assumed (confirm or correct, at most 6 lines)
  - D04 numbers: 20 s, from PaymentConfig default
Trade-offs and risks
  - A shorter wait fails more slow-but-successful payments: possible double charge on retry
  - Requests in flight during the deploy: which timeout applies?
  - Rollback: config, publish the previous version
```

Trade-offs to always consider: safety and risk to the user, regression of another rule, cost and latency, privacy and personal data, rollback, audit, in-flight sessions during the transition, effects on systems being migrated.

## Protected rules
The repository's list is in `repo.md`, "Protected rules". Always protected, in any repository:

| Protection | Source | Right path |
|---|---|---|
| Invariant covered by a structural test | `docs/trd/invariants.md` | Changing the invariant is a repository rule change: ADR or constitution amendment |
| A registered exception to a principle | constitution, ADR | A new ADR to change the exception |
| A safety control | constitution | Loosening it requires an ADR and the safety reviewer |

With a protection involved: say which, its source and the right path in the confrontation and in the return's `Protected:` line; the main asks whether the protection still holds (the document may be stale). It continues only with explicit confirmation, recording in `state.md` the chosen path (`Protected: <ID or invariant> · ADR`, constitution amendment, or "the protection was stale"). An ADR path is written by the `prd-flow-docs` agent at step 5, never by the main; a constitution amendment goes back to the user.
