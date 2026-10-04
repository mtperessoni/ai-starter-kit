# Classification (F0) and divergence (F2)

IDs, texts and paths in the examples are illustrative: always read the real line.

## Cases
| Case | When | Signals in the request | Route |
|---|---|---|---|
| C0 bootstrap | No `docs/prd/INDEX.md`, or the user asks to create the PRD or the TRD | "create the PRD", "document the product", first use in the repository | `bootstrap.md` |
| C1 query | Wants to know how something works or why | "how", "why", "what happens if", "what is the rule for" | F1, then answer with IDs and Source. No edits |
| C2 implement within the rule | The rule exists, is approved, and the code does not meet it yet | "implement the amendment", a row marked `pending code`, "the spec still lacks X" | F1, F2, F6 if the area changes, F7 |
| C3 bug | The code does something different from the PRD and the user confirms the PRD is right | "it is broken", "it should do what the PRD says" | F1, F2, fix; the PRD changes only if the Source moves |
| C4 stale PRD | The code is right and the PRD says something else, confirmed by the user | drift found in F2, removed env var, cited file that no longer exists | F1, F2, F5 without interview; old text literally to the CHANGELOG |
| C5 rule change | Changed rule, new rule, gap in the PRD, or a fix to a defect the PRD documents as current behavior | "change", "it should", "from now on", "add", "fix" something the PRD describes as today's behavior | Full flow F1 to F7 |
| C6 refactor | Structure changes and behavior does not | "rename", "extract", "move", "split", "clean up" | Area TRD + invariants; F6 if files, entry points or tests move |

## Classification traps
| Situation | Right case | Why |
|---|---|---|
| "Fix X" and the PRD documents X as today's behavior | C5 | Fixing it is deciding a new rule |
| "Add an if for customer X" | C5 with a protected rule | Per-tenant behavior is a configuration row, never a branch on the name |
| Change a prompt or a config value "just a little" | C5 | It changes via `prompt` or `config`: it follows the publish route of `repo.md`, not a code edit |
| A refactor that needs a different limit, text or order | Escalate C6 to C5 | It stopped being structure only |
| A row marked `(superseded: ...)` and the request cites the old one | Ask | The requester may not know the amendment, or the amendment may not be deployed yet |
| A request with no matching rule in the PRD | C5 (gap) | Behavior without a written rule is a new rule; it enters the PRD before the code |
| A request with several items | One case per item | Each item follows its route; a C5 gets its own slug; a C3 of the same request can be fixed first, after confirmation, if it does not touch the C5 rules |
| "Diagnose", "understand why", "plan" | C1 until the user asks for a change | A diagnosis is only a diagnosis: show the cause and the options and wait (R01) |
| A `pending code` rule whose code is already committed | C2 | Code without a caller outside the tests is not wired; the rule is still pending |

## Behavior of a real session
To explain what the system did in a real session or request, ask for its id and, with authorization to read the evidence, consult what was recorded before concluding (sources in `repo.md`, "Evidence of real sessions"). Without the id, say which code paths explain the behavior and which evidence would tell them apart, instead of asserting one.

## PRD versus code divergence (F2)
Always show it like this and ask:

```
ORD-03 · PRD: "An order is cancelled after 30 minutes without payment (ORDER_PAYMENT_TIMEOUT)."
Code: the env var no longer exists in src/infra/config/settings.py; the timeout lives in PaymentConfig (src/features/orders/config.py).
Which is right?
- The code (the PRD is stale: I fix the PRD, case C4)
- The PRD (the code regressed: I fix the code, case C3)
- Neither (I want a new rule: case C5)
```

Criteria for "diverges": the cited file or symbol does not exist; it exists but has no caller outside the tests; a number or a name in the text does not match the code; the described flow is not what the code does. A wording difference with no effect on behavior is not a divergence.
