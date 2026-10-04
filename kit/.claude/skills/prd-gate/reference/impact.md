# Confrontation and impact (C5, read by the surveyor worker)

IDs, texts and paths in the examples are illustrative: always read the real line.

## Sweep
| ID | Where to look | How |
|---|---|---|
| K01 | Rules that cite the ID | `Grep "<ID>"` in the test folders for tests citing the rule" docs/prd` outside its own row |
| K02 | Same section and neighboring sections of the journey | Rows of the same table; the previous and next step of the end-to-end journey |
| K03 | Variants | Where `repo.md` documents them. A rule that cites only one variant almost always has a pair in the other |
| K04 | Tenants | Where `repo.md` documents them; per-tenant differences |
| K05 | Invariants and tests | `docs/trd/invariants.md` for the kind of change; `Grep "<ID>"` in the test folders for tests citing the rule\|FR-0NN"` in the test folders for tests citing the rule or the FR |
| K06 | Active changes | `Grep "<ID>"` in the test folders for tests citing the rule" changes --glob "!archive/**"`; a change folder in progress in the area |
| K07 | Open questions, contract, governance | Linked `Q-`, `R-`, `S-` rows; what consumers persist; the Change via column; README "What weighs most today" |
| K08 | Consumer contract in a sibling repository | If the change touches a field, value or key that goes to another repository, check its validation there before the interview (commands in `repo.md`). A value the consumer does not accept breaks the whole delivery |
| K09 | Safety net removed or weakened | Does the change remove or loosen a list, guard, fallback, switch or wait? List what it covered and what becomes uncovered (failure, delay, end of session, disconnection). It becomes a trade-off in the confrontation and an interview question; never an extra task during execution (review.md V06) |
| K10 | Verification prerequisites | What proving the rule requires: a real model (API key in the environment?), a database, a backend. Without the prerequisite, say in the confrontation that the proof stays pending and who runs it |

Sweep of large code: delegate to an Explore agent with the K01 to K07 questions and ask only for the answers.

## Confrontation format
```
Current rule · CHK-02 (product/04-checkout.md)
  "<literal row text>"  · Source: src/features/checkout/payment_call.py · Change via: config
Proposal
  "<how it would read>"
What changes
  Customer: ...   Operator: ...   Backend: ...
Impact
  Rules: CHK-05 (same timeout on retry), ORD-03
  Variants: web and mobile; mobile retries in background
  Tenants: all (shared config)
  Tests: src/features/checkout/tests/test_payment_call.py cites CHK-02
  Change: 007-checkout · Open: Q-CHK-04
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
