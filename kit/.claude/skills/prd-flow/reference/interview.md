# Interview (C5, step 4)

IDs, texts and paths in the examples are illustrative: always read the real line.

Ask only the dimensions that the pre-interview of `pack.md` left **open**; `doc` ones and the `assumed` ones the user confirmed at step 3 enter the read-back as facts. Rounds are the most expensive part of the skill (the context is already large), so each one must count.

## Format of a question
AskUserQuestion, at most 4 per round, each with:
- product language, not code language: a usage example ("the customer taps Pay twice → the app ...?") and the effect on the user, the operator or the stored record. No rule IDs, symbol names, internal acronyms or words like "flag", "key", "handler"; IDs belong to the read-back. If the user asks for clarity, restart from the example and cut by half, without repeating the previous text;
- a concrete scenario: "Payment provider takes 45 s to answer → the app ...?";
- options with the trade-off in the description, the recommended one first, marked "(Recommended)";
- nothing the code or the PRD already answers.

## Dimensions
| ID | Dimension | Guiding question |
|---|---|---|
| D01 | Happy path | What happens, step by step, in the common case? |
| D02 | Variants | Does it hold the same on each variant listed in `repo.md` (platforms, channels, engines)? |
| D03 | Tenants | Does it hold for every tenant or customer, or vary? If it varies, which configuration field carries the variation? |
| D04 | Numbers | Limits, ceilings, timeouts: which value, where is it configurable, who changes it? |
| D05 | Failures | Dependency down, timeout, invalid response: what does the user experience and in which state does it end? |
| D06 | States | In which state does the rule apply; which transition creates or removes it? |
| D07 | Safety and risk | Can it harm the user, expose sensitive data, or bypass a control? Which guard covers it? |
| D08 | Contract | Does what consumers receive change? Can they accept and store it? |
| D09 | Audit | What is recorded to answer "what did the system receive and produce, and why"? |
| D10 | Privacy | Does new personal data go to a log, a model, a third party or the database? Masked? Deleted on request? |
| D11 | Rollback | How does it go back without a deploy? |
| D12 | Governance | If it is editable configuration: approval, immutable versions, audit of the publish |
| D13 | Transition | Sessions or requests in flight during the deploy: old rule or new? |
| D14 | Observability | Which log or metric shows the rule working? |
| D15 | Acceptance | Which test, with which input and which output, proves the rule? The answer lands in the rule's `Example` column (prd-writing.md "Example column") |

Extra domain dimensions (D16 and up) are in `repo.md`.

## Closing each round
Show the rows as they would look and ask for corrections. Each interview answer that chose between real options also gets a `DEC-NN` row in `decisions.md` (below).

## Record: `interview.md`
This conversation writes it; `gate.py --rules` reads the `interview.md` beside the approved-rules file (Q3 when it fails).

```markdown
## Dimensions
| Dimension | State | Answer |
|---|---|---|
| D01 happy path | user | Payment waits 20 s, then "try again" |
| D03 tenants | doc | product/04-checkout.md CHK-01 |
| D04 numbers | assumed-confirmed | 20 s from PaymentConfig default |
| D11 rollback | n/a | configuration only |
| D14 observability | question | Q-CHK-04 |
Confirmed: <name> · <YYYY-MM-DD> · "<the user's words>"
```

| Rule | Detail |
|---|---|
| Rows | D01 to D15 plus every ID of `repo.md` "Extra interview dimensions", Dimension starting with its ID |
| State | One of `user`, `doc`, `assumed-confirmed`, `n/a`, `question`. `open` and `assumed` are not allowed at closure |
| `question` | The Answer carries a `Q-` ID that exists in `approved-rules.md` or the PRD |
| `Confirmed:` | One line after each table: the person, the date and the user's own words |
| Short C5 | Appends `## Dimensions (YYYY-MM-DD)` with only the reopened dimensions (at least one) and its own `Confirmed:` line |

## Record: `decisions.md`
At the end of this step, this conversation allocates the change folder (next free `NNN`, already checked against remote branches in K06) and creates `changes/NNN-<slug>/decisions.md` from `docs/templates/change-decisions.md`. `writer-prd` commits it with `docs(prd)`; the planner reuses the folder.

`| ID | Question | Decision | Rejected alternative | Why | Rules |` with IDs `DEC-NN`: one row per trade-off decided and per interview answer that chose between real options. The Promote task copies the rows into the CHANGELOG entry under `Decisions:`.

## Rule owner
When the confrontation named an owner (`repo.md` "Rule owners") and the approver is not the owner, this step does not close until the user states the owner agreed. The owner is recorded in `decisions.md` (`state.md` only points to it); the CHANGELOG entry then says `decided by <owner>, written by <approver>`.

## Exit criteria
1. Every dimension answered (`user`, `doc`, `assumed-confirmed`, `question`), or `n/a` with a reason; `interview.md` passes Q3.
2. Every row with ID (or section and number, for a table without IDs), text, Source (`planned`) and Change via.
3. Every rule with a number, a branch or a failure path carries an `Example` (D15).
4. No contradiction with a live rule; the superseded ones listed.
5. Every trade-off of the confrontation with a decision (a `DEC-` row).
6. A final read-back and an explicit "it is clear" from the user, copied into `Confirmed:`.

Then write `approved-rules.md`. The `Example` column is optional (four-column tables stay valid); `writer-prd` copies the rows literally and `gate.py --rules --applied` (Q4) checks that:

```markdown
# Approved rules · <slug> · <YYYY-MM-DD> · <approver>
## docs/prd/product/04-checkout.md
| CHK-02 | *(approved 2026-10-04, pending code)* Payment waits at most 20 s for the provider, then shows "try again" and keeps the cart. | planned | config | Provider answers after 45 s → the customer sees "try again" and the cart is intact |
| CHK-13 | *(approved 2026-10-04, pending code)* A request in flight during the deploy keeps the timeout it started with. | planned | code | Payment started at 30 s timeout, deploy sets 20 s → that payment still waits 30 s |
## Supersedes
- CHK-02 (30 s)
```

A rule that came only from a document is written with `*(proposed)*` and is not approved until confronted and interviewed; never put a `*(proposed)*` row in `approved-rules.md`.

Short C5: the file gets a dated section. Format: `## YYYY-MM-DD`, then `### <prd file>.md` with its rows (same cells). A re-approved ID replaces its earlier row; the gate takes the latest.

If the user wants to stop earlier: save the state and say what is missing. A rule with an open dimension does not go to the PRD; it becomes a `Q-` row in "Open questions" with the adopted default, if the user prefers to continue.
