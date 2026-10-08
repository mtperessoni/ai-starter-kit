# Interview (C5, step 4)

Used in C5 step 3 and in the short C5. Read by the surveyor (it prepares the questions and the scaffolds) and by docs `rules` (it writes the records); the chief never reads this page nor writes `interview.md`, `approved-rules.md` or `decisions.md`. IDs, texts and paths in the examples are illustrative: always read the real line.

| Who | Does |
|---|---|
| surveyor | Writes the scaffolds in the formats below: `interview.md` with every dimension prefilled, `approved-rules.md` with the rows to change, the new rules (next free ID per prefix, proposal text), the `## Conflicts` table and the `## Supersedes` lines, and `changes/NNN-<slug>/decisions.md`; in the short C5 it appends dated sections instead. Returns the questions for the dimensions left `open`, ready for AskUserQuestion (format below), at most 4 a round, plus the assumed block to confirm |
| chief | Asks those questions as returned, and passes the user's answers verbatim (and the user's own words for each confirmation) to docs `rules`. Records each decision as one line in `## Chief` |
| docs `rules` | Writes the answers into `interview.md`, the rule text, Example, conflict resolutions, Supersedes, `DEC-` rows and the `Confirmed:` line; runs `<python> .claude/skills/prd-flow/scripts/gate.py --rules .claude/prd-flow/state/<slug>/approved-rules.md` until green, at most 2 reruns after fixing its own files, then `blocked` with the error lines; returns the read-back (the rows as the PRD will hold them), the last gate line, and the next round of questions as `Route: user` when a dimension is still open |

A protected rule the user confirmed is recorded by docs `rules` in `approved-rules.md` and `decisions.md` (`impact.md` "Protected rules"); an ADR path is written by the docs agent in `prd` mode. D08 contract and D13 transition always get a real answer, even "nothing changes": docs carries them into the PRD.

Only the dimensions left `open` become questions; `doc` ones and the `assumed` ones the user confirmed at the confrontation enter the read-back as facts. The interview starts right after the confrontation.

## Format of a question
Prepared by the surveyor (or by docs `rules` for a follow-up round) so the chief asks it unchanged in one AskUserQuestion, at most 4 per round, each with:
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
Docs `rules` returns the rows as they would look; the chief shows them and asks for corrections, which go back to docs `rules`. Each answer that chose between real options also gets a `DEC-NN` row in `decisions.md`, written by docs `rules`.

## Records

### `interview.md`
`gate.py --rules` reads the `interview.md` beside the approved-rules file (Q3 when it fails).

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
| Scaffold states | The surveyor writes `doc`, `assumed`, `open` or `n/a` (`impact.md` "Pre-interview states") and no `Confirmed:` line |
| Closing states | One of `user`, `doc`, `assumed-confirmed`, `n/a`, `question`. An `assumed` row becomes `assumed-confirmed` or `user`; an `open` row becomes `user` or `question`. `open` and `assumed` are not allowed at closure |
| `question` | The Answer carries a `Q-` ID that exists in `approved-rules.md` or the PRD |
| `Confirmed:` | One line after each table: the person, the date and the user's own words |
| Short C5 | Appends `## Dimensions (YYYY-MM-DD)` with only the reopened dimensions (at least one) and its own `Confirmed:` line. Outside a C5 the file is new and starts with the line `Scope: short C5 outside a C5` (execution.md, short C5); without it the first table needs every dimension |

### `approved-rules.md`
A heading per PRD file, whatever PRD it belongs to; each row exactly as the PRD will hold it: `| ID | Rule | Source | Change via | Example |`, the rule text starting with `*(approved YYYY-MM-DD, pending code)*` (replace the scaffold's placeholder date), Source `planned`, Example optional. The docs agent copies the rows literally and `gate.py --rules --applied` (Q4) checks it.

```markdown
# Approved rules · <slug> · <YYYY-MM-DD> · <approver>
## docs/prd/product/04-checkout.md
| CHK-02 | *(approved 2026-10-04, pending code)* Payment waits at most 20 s for the provider, then shows "try again" and keeps the cart. | planned | config | Provider answers after 45 s → the customer sees "try again" and the cart is intact |
| CHK-13 | *(approved 2026-10-04, pending code)* A request in flight during the deploy keeps the timeout it started with. | planned | code | Payment started at 30 s timeout, deploy sets 20 s → that payment still waits 30 s |
## docs/prd/product/06-orders.md
| ORD-03 | *(approved 2026-10-04, pending code)* An order without payment is cancelled after 30 minutes, unless a payment attempt is still waiting for the provider. | planned | code | Payment waiting at minute 30 → the order stays open until the answer |
## Conflicts
| ID | Resolution | Note |
|---|---|---|
| ORD-03 | rewritten | |
| CHK-05 | compatible | retry reuses the same timeout, so 20 s holds |
## Supersedes
- CHK-07: Payment shows a spinner until the provider answers.
```

| Rule | Detail |
|---|---|
| Conflicts | Every ID of the pack's `Conflicts:` line has a row (gate Q5). Resolution is one of `rewritten`, `superseded`, `compatible` |
| `rewritten` | The same ID appears as a row under its file heading with the new text and the marker. Rewriting keeps the ID; the old text goes literally to the CHANGELOG at promotion. An ID is never reused for a different rule |
| `superseded` | The ID is listed under `## Supersedes` as `- ID: old text`, never as a table row, and it exists in the PRD |
| `compatible` | The Note states why both rules hold |
| `*(proposed)*` | A rule that came only from a document is not approved until confronted and interviewed; never put a `*(proposed)*` row here |
| Short C5 | A dated section: `## YYYY-MM-DD`, then `### <prd file>.md` with its rows (same cells). A re-approved ID replaces its earlier row; the gate takes the latest |

### `decisions.md`
The surveyor created `changes/NNN-<slug>/decisions.md` from `docs/templates/change-decisions.md` (next free `NNN`, checked against remote branches). Docs `rules` adds `| ID | Question | Decision | Rejected alternative | Why | Rules |` rows with IDs `DEC-NN`: one per trade-off decided and per answer that chose between real options. The docs agent commits it with `docs(prd)`; promotion copies the rows into the CHANGELOG entry under `Decisions:`.

## Rule owner
When the confrontation named an owner (`repo.md` "Rule owners") and the approver is not the owner, the surveyor includes the question "did the owner agree?" and the interview does not close until the user states the owner agreed. Docs `rules` records the owner in `decisions.md`; the CHANGELOG entry then says `decided by <owner>, written by <approver>`.

## Exit criteria
1. Every dimension in a closing state, `n/a` with a reason; `interview.md` passes Q3.
2. Every row with ID (or section and number, for a table without IDs), text, Source (`planned`) and Change via.
3. Every rule with a number, a branch or a failure path carries an `Example` (D15).
4. Every conflict of the pack resolved in `## Conflicts` (Q5); no contradiction with a live rule left.
5. Every trade-off of the confrontation with a `DEC-` row.
6. A final read-back and an explicit "it is clear" from the user, copied into `Confirmed:`.
7. `gate.py --rules` green, its last line in the docs `rules` return.

If the user wants to stop earlier: the chief records it and what is missing in `## Chief`. A rule with an open dimension does not go to the PRD; it becomes a `Q-` row in "Open questions" with the adopted default, if the user prefers to continue.
