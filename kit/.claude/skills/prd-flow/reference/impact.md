# Confrontation and impact (C5, read by the surveyor worker)

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
| K11 | Semantic sweep | Read the Section column of every PRD file in `docs/prd/INDEX.md`, not only grep hits. Pick up to 8 section files whose subject could interact (same entity, actor, state, number or journey step), read their rule tables, and list each rule the proposal would contradict, constrain or duplicate. A rule phrased with other words is found here, not by K01 |
| K12 | History | `Grep` each in-scope ID in `docs/prd/CHANGELOG.md`; per ID with history show `Decided <date>: <why>; rejected: <alternative> (<why>)` from the entry's Decisions block |
| K13 | Rule owner and shared PRD | `repo.md` "Rule owners": when the change touches an owned section, name the owner. `repo.md` "Shared PRDs": when the PRD folder is shared, say the sibling repository path that must receive the same change |

K11 and K12 are never skipped, in the short C5 they run on the touched rules only.

Sweep of large code: delegate to an Explore agent with the K01 to K07 questions and ask only for the answers.

## Pre-interview states
The single home of these states (the surveyor and `interview.md` cite it). Per dimension D01 to D15 and the extra ones of `repo.md`:

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
Conflicts: ORD-03 (cancels at 30 min, contradicts a 20 s wait)   [or: none found in the checked files]
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

With a protection involved: say which, its source and the right path, and ask whether the protection still holds (the document may be stale). Continue only with explicit confirmation, recording in `state.md` the chosen path (ADR, constitution amendment, or "the protection was stale").
