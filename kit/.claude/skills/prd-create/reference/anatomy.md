# PRD anatomy

IDs, texts and paths in the examples are illustrative: always read the real code and documents.

## Layout
```
docs/prd/
  INDEX.md            entry for agents: every file, its section, its ID ranges, its TRD
  README.md           overview for people: what the product is, how to read, what weighs most, decisions
  CHANGELOG.md        superseded wording, literal, newest first
  prd.html            reading version, one tab per PRD (path in repo.md `html`; built only by /docs-html)
  <prd-a>/            one folder per PRD, kebab-case (for example `checkout`, `outcome-run`)
    01-summary.md
    02-glossary.md
    ...
  <prd-b>/
```

## How many PRDs
| Signal | Decision |
|---|---|
| Two flows run independently, with different actors or triggers (a live conversation versus a batch analysis) | Two PRDs |
| A module has its own users, its own release cadence or its own consumers | Its own PRD |
| One journey with several steps | One PRD, one section per step |
| Admin, configuration or back-office that governs another flow | A section of that PRD, or its own PRD when it has its own journey |

A new context in a repository that already has PRDs starts in `/prd-flow` (C5, size L), not here. A section file stays within `prd_section_budget_lines`; past it, split by subsection.

Each PRD has a short name and a number for prefixes when helpful (`R1-`, `Q2-`).

## Sections of a PRD
Keep this order. Numbers are two digits; a section split by subsection uses `NN-MM`.

| # | File | Content | Format |
|---|---|---|---|
| 01 | `01-summary.md` | What this PRD covers, who triggers it, what it delivers, in at most 15 lines | prose |
| 02 | `02-glossary.md` | Every domain term a reader needs | `\| Term \| Meaning \| Name in code \|` (symbol and file) |
| 03 | `03-scope.md` | In scope, out of scope, neighboring systems | two lists |
| 04 | `04-end-to-end-journey.md` | The journey as numbered steps in product language, plus one mermaid flowchart with the failure exits | list + mermaid |
| 05..N | `NN-<step>.md` | One file per step of the journey (`Step 1 · <name>`), in journey order | anatomy below |
| N+1 | `NN-states-and-failures.md` | The states of the main entity and how each one is reached; every failure and what the user experiences | `\| State \| How it is reached \| What the user sees \| Final? \|` + rule table |
| N+2 | `NN-audit-cost-and-privacy.md` | What is recorded, costs, personal data handling | rule table |
| N+3 | `NN-configuration.md` | Everything that changes behavior, grouped by where it changes (config, env, request) with the effect of changing it | `\| Field \| What it controls · default · effect of changing \| Source \| Change via \|` |
| N+4 | `NN-tenant-matrix.md` (when tenants exist) | What differs per tenant, customer or variant | matrix |
| N+5 | `NN-problems-of-the-current-structure.md` | Design choices that cause several risks, each pointing to the decision that solves it | `\| Level \| Problem \| Evidence \| Change via \|`, IDs `S<prd>-NN · high\|medium\|low` |
| N+6 | `NN-spec-versus-code.md` | Where specs or docs say one thing and the code does another | `\| Topic \| The spec or doc says \| The code does \|` |
| N+7 | `NN-risks.md` | Risks with severity, scenario and mitigation | `\| R<prd>-NN · high \| ... \|` |
| N+8 | `NN-open-questions.md` | Every decision not yet made, with the adopted default | `\| Q<prd>-NN \| Question \| Default adopted \| Blocks \|` |

Amendments approved later (by prd-flow) take the next number with subsections: `NN-00-overview.md`, `NN-01-<topic>.md`. At promotion they are folded into the step sections, as defined in prd-flow `reference/write.md` "Promotion" (P3).

## Anatomy of a step section
```markdown
## 07. Step 3 · Payment

<What this step is and why it exists, in 3 to 6 lines of product language.>

<How it works, with one concrete example: "A customer pays a 120.00 cart with a card that the provider declines → ...".>

> [!IMPORTANT]
> <Something a reader must not miss: an approved amendment, a dependency.>

> [!CAUTION]
> **<A verified defect in one line> *(checked in code)***
>
> <What happens, with the evidence by file and symbol.>

| How it ends | Variant | What the user experiences | Final state | Reaches <consumer>? |
|---|---|---|---|---|

| ID | Rule | Source | Change via | Example |
|---|---|---|---|---|
| PAY-01 | <one behavior, in product language> | src/features/payment/charge.py::charge_cart | code | A 120.00 cart, card declined → cart kept, "payment declined" shown |
```

The outcome table is optional; the rule table is mandatory for a step.

## Rule rows
| Item | Rule |
|---|---|
| ID | `<PREFIX>-NN`, prefix of 2 to 6 uppercase letters per section, optional sub-prefix (`C-PAY-01`); numbers start at `01`, permanent, never reused |
| One behavior per row | A row that needs "and also" is two rows |
| Product language | What the user or the system experiences: limits, order, states, failures, who sees what. Technical terms only in backticks and explained |
| Variant tags | `[WEB]`, `[MOBILE]` (from `repo.md` variants) at the start when the rule holds for one variant only |
| Numbers | Say the value and where it is configured: "after 30 s (`PaymentConfig.timeout`)"; never cite a default as if it were the rule when it is configurable |
| Source | `path/to/file.ext` or `path::symbol`; several files separated by `;`; `planned` without code |
| Change via | One value from `repo.md` `change_via` |
| Example | Optional fifth column, defined in prd-flow `reference/write.md` "Rule rows" |
| Markers | `*(proposed)*` (rule from documents only, Source `planned`), `*(approved YYYY-MM-DD, pending code)*`, `*(superseded: <link>, valid until deploy)*`, `*(checked in code)*` in callouts. `--final` fails on a proposed rule (G30) |
| Risks, problems | `\| R1-04 · high \| <scenario> \| <mitigation> \|`; level is `high`, `medium` or `low` |

## README.md (overview for people)
Two parts, in this order, mirrored as the first and last tabs of the HTML:

**Overview:** 00 what the product is (stack in one line, who calls it, the PRDs and what each covers) · 01 how to read this document · 02 the journey and the scopes (one mermaid diagram across PRDs) · 03 what weighs most today (the 5 to 8 heaviest problems and risks, with IDs) · 04 how to change a rule (`/prd-flow`, PRD then TRD then plan then code) · 05 principles that limit changes (from the constitution) · 06 state per spec (which specs are done, in progress, pending) · 07 how this document was made (mode, base commit, date, what was checked).

**Open decisions:** how to use this tab · decide now (open questions that block work, ranked by risk) · product decisions · documentation hygiene (divergences between docs).

## INDEX.md
```markdown
# PRD index

Entry point for agents. Load only the section you need; for a rule, `Grep "<ID>" docs/prd`. The TRD of the area says where the rule lives in the code. Superseded text: [CHANGELOG.md](CHANGELOG.md). Human reading version: [prd.html](prd.html), never read it for work.

## PRD 1 · <name> (<one line of scope>)
| File | Section | IDs | TRD |
|---|---|---|---|
| [01-summary.md](<prd-a>/01-summary.md) | Summary |  |  |
| [07-payment.md](<prd-a>/07-payment.md) | Step 3 · Payment | PAY-01..12 | [payment](../trd/payment.md) |
```
The IDs column uses ranges (`PAY-01..12`) and lists, separated by commas. The TRD column is filled by trd-create.

## CHANGELOG.md
```markdown
# CHANGELOG

Superseded PRD text, removed from the body so it describes only the rules in force; the newest change comes first, and every excerpt is copied exactly as it was.
```
A prd-flow entry also carries a `Decisions:` block (rows copied from the change's `decisions.md`) and, after a fold, "folded into <files>".

## Quality bar before the read-back
- Every journey step has a section and every section with behavior has a rule table.
- Every Source exists (one `Grep` per symbol) and has a caller outside the tests, or the rule says it is not wired.
- Every number is tied to where it is configured.
- Every defect found is in a CAUTION callout and in open questions or risks.
- The glossary covers every term used in a rule.
- Every rule with a number, a branch or a failure path has an Example.
- In M3 and M4, every rule not proven by code is `*(proposed)*` with Source `planned`.
- The gate is green.
