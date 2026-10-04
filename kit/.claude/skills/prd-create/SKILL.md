---
name: prd-create
description: Creates the PRDs of this repository, the single source of truth for product behavior. One or several PRDs, each split into small section files (one context per file, for lazy loading) with rule tables (ID, rule, source, change via), a glossary with code names, the end-to-end journey, states and failures, configuration, problems, spec-versus-code divergences, risks and open questions, plus INDEX, README, CHANGELOG and the HTML reading version. Works from existing code (documents what the code does today), from existing documents, or from an interview when there is no code yet; also adds a new PRD to a repository that already has others. Use when someone says "create the PRD", "document the product", "write the requirements", "map the business rules", "new product", "new module", when prd-gate finds no PRD, or right after /ai-kit install. Not for changing an existing rule (prd-gate) nor for the code map (trd-create).
---

# prd-create

The PRD says what the product does and why, rule by rule, in product language, with the code file that implements each rule. Agents read only the markdown, one small section at a time (`docs/prd/INDEX.md` routes them); people read the HTML. Everything is in English. Values specific to this repository are in `.claude/skills/prd-gate/repo.md`.

## Principles
| ID | Principle |
|---|---|
| P01 | **Documents what is, not what should be.** From code, every rule describes today's behavior, defects included. A behavior that looks wrong is written as it is, flagged with a `> [!CAUTION]` "(checked in code)" callout and an open question with the adopted default. Fixing it later is a C5 in prd-gate |
| P02 | **Every rule row is complete:** permanent ID, text in product language, Source (file and symbol, never a line or a default value; `planned` when there is no code), Change via (from `repo.md`) |
| P03 | **One context per file.** A section file holds one step of the journey or one cross-cutting concern, stays under about 300 lines, and is split by subsection (`NN-MM-<slug>.md`) when larger. The INDEX lists every file with its ID ranges |
| P04 | **Explain before the table.** Each section opens with what it is, how it works and a concrete example, in product language, then the rule table. A reader who never saw the code understands it |
| P05 | **Facts from code and documents, intent from the user.** Never ask what the code answers; never invent intent. Unknown intent becomes an open question with the adopted default |
| P06 | **The HTML carries the same words.** Every rule row exists in the HTML with identical text; the gate compares word by word. Agents never read the HTML |
| P07 | **Outline first.** No section is written before the user approves the outline (PRDs, sections, prefixes, sources) |
| P08 | Everything in English; no em dash (U+2014); questions to the user in product language with an example |

## Modes
| Mode | When | Facts come from |
|---|---|---|
| M1 from code | The product exists in code | `mapper` workers over the code, by area |
| M2 greenfield | No code yet | The interview (`reference/greenfield.md`), this conversation |
| M3 from documents | Specs, tickets, an old PRD or HTML exist | `doc-reader` workers, then M1 to check against code if there is code |
| M4 add a PRD | The repository already has PRDs and a new product or module appears | M1, M2 or M3 for the new scope; the existing INDEX, README and HTML gain a PRD |

Modes combine: M3 plus M1 is common (documents for intent, code for facts; their differences go to the "spec versus code" section).

## Route
| Step | Who | Does | Leaves |
|---|---|---|---|
| 1 | this conversation | Slug `prd-create-<scope>`, mode, approver (`git config user.name`), base commit in `state.md`. Batch: `Read repo.md`; `Glob` of source folders, entry points, `specs/`, `docs/`; existing `docs/prd/INDEX.md` if any | state |
| 2 | this conversation | Scope: how many PRDs (one per product scope or user journey that runs independently; `reference/anatomy.md` "How many PRDs"), the sections of each, ID prefixes, areas each section covers. Write `outline.md`; show it as a table; approve with at most 4 questions per round | approved outline |
| 3 | `mapper` per area (M1), `doc-reader` per document set (M3), interview here (M2) | Facts per area | `areas/<area>.md` or `interview.md` |
| 4 | `section-writer`, waves of disjoint files | Journey step sections and their rule tables | section files |
| 5 | `crosscut-writer` | Summary, glossary, scope, end-to-end journey, states and failures, configuration, problems, spec versus code, risks, open questions | cross-cutting files |
| 6 | `index-writer` | `INDEX.md`, `README.md` (overview and open decisions), `CHANGELOG.md`; gate | index files |
| 7 | `html-writer` | The HTML reading version from `docs/templates/prd.html`, one tab per PRD; gate until markdown and HTML agree | HTML |
| 8 | this conversation | Read-back in at most 25 lines: rules per section, the 5 heaviest problems, the open questions to decide now. Commit `docs(prd): <scope> PRD from <source>` | commit |
| 9 | this conversation | Next: `/trd-create` (the code map), then `/prd-gate` for every change | handoff |

Worker: Agent `general-purpose`, `model: "sonnet"`, prompt *"Read `.claude/skills/prd-create/reference/workers.md`, section `<name>`, and run it for slug `<slug>`. Assignment: <areas or files>."* Never paste briefings or documents into the prompt. Waves of at most 4 parallel workers on disjoint files. A gap in a return is resolved before the step that depends on it.

## Context economy
Same budgets as prd-gate: independent reads in one message; code only by symbol; this conversation never reopens worker files; worker returns at most 30 lines; at most 4 questions per round; ceilings of about 40 tool calls per mapper and 50 per writer.

## State
`.claude/prd-gate/state/prd-create-<scope>/` (outside git): `state.md`, `outline.md`, `areas/*.md`, `interview.md`, `writing.md`. Resume with `/prd-create resume <scope>`: read `state.md` and the current step only.

## Files
| File | Who reads it |
|---|---|
| `reference/anatomy.md` | this conversation at step 2; every writer |
| `reference/greenfield.md` | this conversation in M2 |
| `reference/workers.md` | each worker, only its section |
| `reference/html.md` | the `html-writer` |
| `docs/templates/prd-section.md`, `docs/templates/prd.html` | writers |
| `.claude/skills/prd-gate/scripts/gate.py` | run only |

## Final
PRDs created, files and rule counts, commit, the open questions to decide now, next step.
