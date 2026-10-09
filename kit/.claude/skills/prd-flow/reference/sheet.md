# Decision sheet (surveyor writes, docs reads)

The surveyor writes `sheet.md` (`short`: `sheet-short-<k>.md`, k = 1, 2, ..., only the touched rows, never over `sheet.md`); the chief prints it verbatim and ends the turn; docs `apply` reads the reply. Examples are illustrative.

## Format
Headings and labels come from `repo.md` `sheet_labels` (prose in the repo `language`; the `Kind` tokens stay English).
```markdown
# <the change in one line>

## What changes in the rules
| Rule | Today (literal) | Becomes | Kind |
|---|---|---|---|
| CHK-02 | "Payment waits 30 s for the provider" | "Payment waits 20 s, then shows try again and keeps the cart" | rewrites |
| CHK-13 | (none) | "A payment in flight during the deploy keeps its timeout" | adds |
| CHK-07 | "Shows a spinner until the provider answers" | (removed, CHK-02 covers it) | supersedes |

## What does not change
- Shipping, discounts and the receipt layout.

## Assumed (holds unless you correct it)
- A1 Applies to every tenant (shared config).
- A2 Rollback: a deploy of the previous version.

## Decisions (answer by number)
**1. When the provider is slow** · rule CHK-02
Today: the customer waits 30 s, then sees an error and the cart is lost (CHK-02).
Why it matters: about 4% of payments take more than 20 s.
- A) 20 s, then "try again", cart kept (Recommended): fewer stuck carts; a slow success may be charged twice on retry
- B) 60 s: fewer false failures; the customer waits longer
Example: provider answers at 45 s, then (A) shows "try again" with the cart intact.
Interacts with: 2

**2. A payment in flight during the deploy** · rule CHK-13
Today: no rule; a payment started before a deploy takes the new timeout.
Why it matters: a deploy in the middle of a payment could cut it short.
- A) Keep the timeout it started with (Recommended): no payment cut early; both timeouts live for a few minutes
- B) Take the new timeout at once: one timeout only; a payment may end early
Example: a payment starts with 30 s, the deploy lands at second 10, then (A) still waits until second 30.
Interacts with: 1

## How to answer
`ok` accepts every recommendation and assumption. Otherwise: `1B`, `A2: <correction>`, `scope: <correction>`. If a scenario is wrong, say its number.
```

## Sheet rules
Limits and shape checks (counts, one topic per rule, plain words in titles and options, numbers in options) live in "Lint", the one home.

| Rule | Detail |
|---|---|
| Diff first | Every rule the change touches is a diff row with the literal text; `Kind` is `rewrites`, `adds`, `supersedes` or `removes`; `Today` of `adds` is `(none)`; sweep conflicts (K01, K11, K14) are rows, never questions |
| Scope | "What does not change" has at least one line |
| Assumed | Each `Decided in conversation:` and `Preferences:` item is an assumed line, never a decision |
| Decisions | Real alternatives only. Each has a title, `rule <ID>` (or `mechanism`), `Today:`, `Why it matters:`, at least two options with their consequence, exactly one `(Recommended)`, `Example:`; `Interacts with:` optional |
| Mechanism | A rollback, switch, configuration key, environment variable, table, column or endpoint the change needs is a decision of the sheet, surveyed here; docs never adds one |
| Order | Protected rule and rule owner items first |
| Recommendation | Cites the stated preference it follows, or says "no stated preference" |
| Owner | When the approver is not the owner of a touched section, an item asks whether the owner agreed; the CHANGELOG records `decided by <owner>, written by <approver>` |
| Blind spots | Before writing, check failure paths, requests in flight during the deploy, consumers of the data, tenant variation, safety, privacy, cost and latency, audit, rollback and systems being migrated; ask only where a real alternative exists. A rollback not obvious from the pack is an assumed line, or a decision when the alternatives differ in cost |

## Lint
`gate.py --sheet <slug>`, once, after writing (`sheet-2.md` and every `sheet-short-*.md` too). Titles and options use plain words; IDs and code names only in `Today:`, `Why it matters:`, `Example:`. More than 8 decisions: the sheet recommends splitting the change.

| Code | Check | Level |
|---|---|---|
| S1 | Every decision has Today, Why it matters, Example, two options or more and exactly one Recommended | error |
| S2 | Every rule ID the pack marks touched or conflicting is a diff row | error |
| S3 | No two decisions on the same rule ID and scope words; at most 8 decisions and 8 assumed lines | error |
| S4 | No `plain_words` term in a decision title or option | warn |
| S5 | A decision with a comparison word (above, below, more than, at least, after, before) names a number or a category in its options | warn |
| S6 | Every `Interacts with:` target exists | error |
| Q3 | A mechanism term in `decisions.md` or in the rows of the entry's `IDs:` that is not in `sheet.md`, `sheet-2.md` or a `Reply` line (run by `gates.sh docs`) | error |

## Answers
| Reply | Meaning |
|---|---|
| `ok` | every recommendation and assumption accepted |
| `1B` | option B of decision 1 |
| `A2: <correction>` | assumption 2 corrected |
| `scope: <correction>` | "What does not change" corrected |

Docs checks the combination of the answers along every `Interacts with:` line before writing. An unclear answer, or one that opens a decision the sheet does not hold, gets one `sheet-2.md` (same format, only those items) and `Route: user: sheet-2.md`; an open TRD-only design choice is a `sheet-2.md` item too. One follow-up, hard stop: after its reply docs never writes another sheet, and an item still open (a TRD-only decision or a gate-red unclear rule included) becomes a `Q-` row with the recommended default, visibly open. A short sheet's reply is the short C5's approval.

## decisions.md
`changes/NNN-<slug>/decisions.md` (template `docs/templates/change-decisions.md`), written by docs `apply`, the only home of `DEC-` rows; promote copies them once into the CHANGELOG entry under `Decisions:`.
```markdown
# Decisions · 012-payment-timeout

Reply 1: "ok, but 1B"
Reply 2: "the rollback is a config change"

| ID | Question | Decision | Rejected alternative | Why | Rules |
|---|---|---|---|---|---|
| DEC-01 | How long to wait for a slow provider | 60 s | 20 s and try again | fewer false failures matter more here | CHK-02 |
```
`Reply 1:` is the user's message verbatim, `Reply 2:` only after the follow-up. One DEC row per answer that chose between real options, plus the protected rule decision and the owner's agreement.
