# Classification and divergence

Read by the surveyor, which classifies. The chief never reads this page nor a PRD row to classify: it may state a guess (or `unclear`) in the dispatch, and the surveyor's return fixes the case and the size; a divergence comes back as `Route: user` with the block below. IDs, texts and paths in the examples are illustrative: always read the real line. The surveyor's mode per case: `query` (C1), `light` (C2, C3, C4, C6), `full` (C5), `short` (a rule change mid-execution).

## Cases
| Case | When | Signals in the request | Route |
|---|---|---|---|
| C0 no PRD | No `docs/prd/INDEX.md`. Only that | "create the PRD", "document the product", first use in the repository | The surveyor reports it; hand over to `/prd-create`, then `/trd-create` |
| C1 query | Wants to know how something works or why | "how", "why", "what happens if", "what is the rule for" | Surveyor `query`: its return is the answer, with IDs and Source, saying per rule cited "verified in code" (one Grep found the Source symbol with a caller outside tests) or "not verified". For the state of rules (`proposed`, `approved`, `superseded`, `implemented`) it runs `gate.py --status`. No edits |
| C2 implement within the rule | The rule exists, is approved, and the code does not meet it yet | "implement the amendment", a row marked `pending code`, "the spec still lacks X" | Surveyor `light` (rows, Source verdict, the task card); over one task or an area change: its Route is docs `trd-plan`; then executor, reviewer, executor `close` |
| C3 bug | The code does something different from the PRD and the user confirms the PRD is right | "it is broken", "it should do what the PRD says" | Surveyor `light`, executor `task`, reviewer, executor `close`; the PRD changes only if the Source moves |
| C4 stale PRD | The code is right and the PRD says something else, confirmed by the user | drift found in the PRD versus code check, removed env var, cited file that no longer exists | Surveyor `light`, then docs `c4` without interview (old text literally to the CHANGELOG), then executor `close` |
| C5 rule change | Changed rule, new rule, gap in the PRD, or a fix to a defect the PRD documents as current behavior | "change", "it should", "from now on", "add", "fix" something the PRD describes as today's behavior | C5 route of `SKILL.md`, from surveyor `full`. Includes a new product, module or incoming spec document in a repository with PRDs: size L, new PRD variant (below) |
| C6 refactor | Structure changes and behavior does not | "rename", "extract", "move", "split", "clean up" | Surveyor `light` (area TRD and invariants in the card; TRD update when files, entry points or tests move), executor `task`, reviewer, executor `close` |

## Size
Stated in the case line: `C5 · size L · <one line>`. It decides which files the change folder holds (`agent-plan.md`, "Where the plan lives") and how wide the surveyor sweeps (`impact.md`, "Sweep by size").

| Size | When | Change folder |
|---|---|---|
| S | C1, C2, C3, C4, C6. Never a C5 | None, or only `plan.md` |
| M | C5 with an evident design: no new data model, contract, external dependency or open technical unknown | `brief.md`, `plan.md` |
| L | C5 with any of: a new data model, a new contract, an external integration, a technical unknown, a new feature area, a new PRD | `brief.md`, `design.md`, `plan.md` |

A C5 is size M or L, never S: a one-row change is size M.

A one-rule C5 (one rule row touched, one task) is the short path: sheet, PRD row, one card, close. A `brief.md` is written only for size L.

## A new context is a new PRD
When the repository already has PRDs and the request is a new product context (a product, module or incoming spec document that runs on its own), it is C5 size L, new PRD variant, never C0. The surveyor sweeps it against every existing PRD of `docs/prd/INDEX.md` (`impact.md` K11). The variant writes only approved rows, after the interview: the docs agent lays out the new PRD folder with the anatomy of `.claude/skills/prd-create/reference/anatomy.md` and adds its INDEX section (its HTML tab appears the next time someone runs `/docs-html`). Only `/prd-create` (C0) writes `*(proposed)*` rules (Source `planned`); prd-flow confronts and interviews them per section and replaces the marker with `*(approved YYYY-MM-DD, pending code)*`. A proposed rule is C5 input, never C2.

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
| "Diagnose", "understand why", "plan" | C1 until the user asks for a change | A diagnosis is only a diagnosis: show the cause and the options and wait |
| A `pending code` rule whose code is already committed | C2 | Code without a caller outside the tests is not wired; the rule is still pending |
| A `*(proposed)*` rule | C5, never C2 | It came from a document and nobody confronted it; it enters the confrontation and the interview first |
| A new product, module or spec document in a repository with PRDs | C5 size L | Not C0: C0 is only for a repository without `docs/prd/INDEX.md` |

## Behavior of a real session
To explain what the system did in a real session or request, the surveyor returns `Route: user` asking for its id and, with authorization to read the evidence, consults what was recorded before concluding (sources in `repo.md`, "Evidence of real sessions"). Without the id, say which code paths explain the behavior and which evidence would tell them apart, instead of asserting one.

## PRD versus code divergence
The surveyor returns it in this form as its `Route: user`; the chief asks it as is:

```
ORD-03 · PRD: "An order is cancelled after 30 minutes without payment (ORDER_PAYMENT_TIMEOUT)."
Code: the env var no longer exists in src/infra/config/settings.py; the timeout lives in PaymentConfig (src/features/orders/config.py).
Which is right?
- The code (the PRD is stale: I fix the PRD, case C4)
- The PRD (the code regressed: I fix the code, case C3)
- Neither (I want a new rule: case C5)
```

Criteria for "diverges": the cited file or symbol does not exist; it exists but has no caller outside the tests; a number or a name in the text does not match the code; the described flow is not what the code does. A wording difference with no effect on behavior is not a divergence.
