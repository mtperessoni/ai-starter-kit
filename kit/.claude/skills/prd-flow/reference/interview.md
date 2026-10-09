# Interview (C5): the decision sheet

Read by the surveyor (writes `sheet.md`) and by docs `apply` (writes the records). The chief prints `sheet.md` and never reads this page. IDs, texts and paths in the examples are illustrative: always read the real line.

| Who | Does |
|---|---|
| surveyor `full` | Writes `pack.md` and `sheet.md` (format below) |
| chief | Prints `sheet.md` as its message, verbatim, and ends the turn; passes the user's reply verbatim to docs `apply` |
| docs `apply` | Writes `answers.md`, `rules.md`, `decisions.md`, PRD, TRD Planned and plan; at most one follow-up `sheet-2.md` |

## Format of `sheet.md`
Headings and labels come from `repo.md` Gate config `sheet_labels` (prose in the `language` of the repository; the `Kind` tokens stay English).

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

| Block | Rule |
|---|---|
| Diff | `Kind` is `rewrites`, `adds`, `supersedes` or `removes`; `Today` of an `adds` row is `(none)` |
| Scope | "What does not change" is mandatory, at least one line |
| Item | Title, `rule <ID>[, <ID>]` (a mechanism decision says `mechanism` instead), `Today:`, `Why it matters:`, at least two options with their consequence, exactly one `(Recommended)`, `Example:`; `Interacts with:` is optional |

## Sheet rules
| Rule | Detail |
|---|---|
| Diff first | Every rule the change touches is a diff row with the literal text; conflicts of the sweep (K01, K11, K14) are rows (`rewrites` or `supersedes`), never separate questions |
| Assumed | At most 8 lines. Whatever the chief passes as `Decided in conversation:` or `Preferences:` is an assumed line, never a decision |
| Decisions | Real alternatives only, at most 8; more means the sheet recommends splitting the change |
| Mechanism | A rollback, switch, configuration key, environment variable, table or endpoint the change needs is always a decision of the sheet; docs never adds one |
| Context | IDs and code names are allowed in context lines (`Today:`, `Why it matters:`, `Example:`); titles and options use plain words |
| Order | Protected rule and rule owner items first |
| One topic | Two items never decide the same rule and scope |
| Recommendation | Cites the stated preference of the user it follows, or says "no stated preference" |
| Numbers | A rule that depends on a number or a category names it in the option |
| Owner | When the confrontation named an owner and the approver is not the owner, an item asks whether the owner agreed; docs records `decided by <owner>, written by <approver>` |

## Answers
| Reply | Meaning |
|---|---|
| `ok` | Every recommendation and every assumption accepted |
| `1B` | Option B of decision 1 |
| `A2: <correction>` | Assumption 2 corrected |
| `scope: <correction>` | "What does not change" corrected |

| Rule | Detail |
|---|---|
| Follow-up | An unclear answer or one that opens a new decision gets one `sheet-2.md` with only those items; after its reply an item still open becomes a `Q-` row with the recommended default, visibly open |
| Not understood | Answer with today's rule and an example; never the same question in new words |
| Combinations | Docs checks the combination of answers per `Interacts with:` before writing |

## Records
| File | Content |
|---|---|
| `answers.md` | `## Reply 1` (the user's message verbatim), `## Reply 2` only after the follow-up, then `## Resolution`: `\| Item \| Answer \| From \|`, one row per sheet item (`1`..`N`, `A1`..`An`, `scope`); Answer is the option letter, `accepted`, the correction words, `default` or `open Q-<ID>`; From is `Reply 1`, `Reply 2` or `ok` |
| `rules.md` | The approved rows, written once from sheet plus answers, replaced in place (one row per ID) |
| `approved-rules.md` | Rendered from `rules.md` with `<python> .claude/skills/prd-flow/scripts/state_record.py render <state> [<change>]`, never edited by hand; `gate.py --rules` and `--applied` read it |
| `decisions.md` | `changes/NNN-<slug>/decisions.md`, from `docs/templates/change-decisions.md`: `\| ID \| Question \| Decision \| Rejected alternative \| Why \| Rules \|`, one `DEC-NN` row per answer that chose between real options; the only home of DEC rows; promotion copies them once into the CHANGELOG entry |

### `approved-rules.md`
A heading per PRD file; each row exactly as the PRD will hold it: `| ID | Rule | Source | Change via | Example |`, the rule text starting with `*(approved YYYY-MM-DD, pending code)*`, Source `planned`. A `*(proposed)*` row is never put here.

```markdown
# Approved rules · <slug> · <YYYY-MM-DD> · <approver>
## docs/prd/product/04-checkout.md
| CHK-02 | *(approved 2026-10-04, pending code)* Payment waits at most 20 s for the provider, then shows "try again" and keeps the cart. | planned | config | Provider answers after 45 s → the customer sees "try again" and the cart is intact |
## Conflicts
| ID | Resolution | Note |
|---|---|---|
| CHK-05 | compatible | retry reuses the same timeout, so 20 s holds |
## Supersedes
- CHK-07: Payment shows a spinner until the provider answers.
```

| Rule | Detail |
|---|---|
| Conflicts | Every ID of the pack's `Conflicts:` line has a row; Resolution is `rewritten`, `superseded` or `compatible` (the Note says why) |
| `rewritten` | The same ID is a row under its file heading with the new text; the old text goes literally to the CHANGELOG; an ID is never reused for another rule |
| `superseded` | Listed under `## Supersedes` as `- ID: old text`, never as a table row |
| Short C5 | A dated section `## YYYY-MM-DD`, then `### <prd file>.md`; a re-approved ID replaces its earlier row |

## Sheet lint (`gate.py --sheet <slug>`, and Q3 in `gate.py --rules`)
| Code | Check | Level |
|---|---|---|
| S1 | Every decision has Today, Why it matters, Example, at least two options and exactly one Recommended | error |
| S2 | Every rule ID the pack marks as touched or conflicting (K01, K11, K14) is a row of the diff table | error |
| S3 | No two decisions name the same rule ID with the same scope words; at most 8 decisions, at most 8 assumed lines | error |
| S4 | No `plain_words` term in a decision title or option line (context lines may carry IDs and code names) | warn |
| S5 | A decision whose text has a comparison word (above, below, more than, at least, high, low, after, before) names a number or a category in its options | warn |
| S6 | A decision listed in another's `Interacts with:` exists | error |
| Q3 | Every sheet item (`1`..`N`, every `A<n>`, `scope`) has a row in `answers.md` `## Resolution`; a mechanism term (environment variable, switch, flag, configuration key, table, endpoint, column) in `rules.md` or `decisions.md` that is not in the sheet or the answers is an error | error |
