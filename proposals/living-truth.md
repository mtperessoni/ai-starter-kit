# Proposal: living truth plus change deltas

Status: candidate on branch `feat/living-truth`, not merged until the evaluation in `eval/` shows it is at least as good as the current flow (PRD, TRD and spec-kit) on quality and not worse on cost (M01).

## Problem
The kit tells every project to run spec-kit (`/speckit-specify`, `/speckit-plan`, `/speckit-tasks`) but never installs it, and spec-kit's `spec.md` holds requirements (FR-xxx) that duplicate the PRD rule rows. Two homes for the same behavior drift apart; a `spec.md` from months ago reads as authority while describing an old intent.

## Principle
Every fact has one living home; everything else cites it by ID. A change folder holds intent, plan and state, never truth: at the end of the change what is durable is promoted to its living home and the folder is archived.

## Rules
| ID | Rule |
|---|---|
| LT01 | Change folder: `changes/NNN-<slug>/` with the next free number, holding `brief.md` (size M and L), `design.md` (size L only) and `plan.md`. Workflow state stays in `.claude/prd-gate/state/<slug>/` as today |
| LT02 | `brief.md` (template `docs/templates/change-brief.md`): Why (at most 5 lines), Scope and Out of scope, Slices table (`Slice`, `Priority` P1/P2/P3, `Rule IDs`, `Independent test`), Success criteria as PRD rule IDs only. It never contains rule text: behavior is written once, in the PRD |
| LT03 | `design.md` (template `docs/templates/change-design.md`), size L only: Unknowns and research (question, finding, source), Decisions, Data model, Contracts, Alternatives considered. Every section names its promotion target: decisions to `docs/adr/`, data model to the real schema or migration plus the TRD, contracts to the real artifact (OpenAPI, schema, proto) plus a link in the TRD |
| LT04 | Size is decided at classification and stated in the case line. **S**: C1, C2, C3, C4, C6, no change folder or only `plan.md`. **M**: C5 with an evident design (no new data model, contract, external dependency or open technical unknown). **L**: C5 with a new data model, contract, external integration, technical unknown, or a new feature area |
| LT05 | The plan header carries `## Constitution check`: one row per principle the change touches (principle, how the plan honors it, or the justified violation). It replaces spec-kit's Constitution Check and `Complexity Tracking` |
| LT06 | The mandatory final task "Promote" also promotes `design.md` (ADRs, schema or contract artifacts, TRD links) and archives the folder with `git mv changes/NNN-<slug> changes/archive/NNN-<slug>` |
| LT07 | Order of authority: constitution, then PRD (behavior), then TRD (structure), then code. An active plan governs only the order of work. Nothing under `changes/archive/` or a legacy `specs/` is read to learn current behavior |
| LT08 | `gate.py --trace`: every PRD rule whose Source is not `planned` is cited by at least one test file (the `test_patterns` of `ai-kit.json`); rules without a test are reported against the shrink-only allowlist `allowlist.untested_rules` of `ai-kit.json` (new untested rule: error; listed one: warning; listed one now tested: error asking to remove it from the list). The file named in Source exists (error) |
| LT09 | `gate.py --change <dir>`: every ID in `brief.md` exists in the PRD; every ID of a P1 slice is in the Contract of at least one task of `plan.md`; `brief.md` holds no rule row (`| <ID> | text | source | via |`); `design.md` without size L in `brief.md` is a warning |
| LT10 | `gate.py --final`: no PRD row with Source `planned` or the pending marker, no `## Planned` section in `docs/trd/`, no folder in `changes/` outside `archive/`. CI runs it on pushes to the base branch |
| LT11 | Compatibility: a repository with a legacy `specs/` keeps it untouched as history; new changes go to `changes/`. When the team keeps spec-kit (`repo.md` "Spec-kit": `kept`), `spec.md` cites PRD rule IDs and defines no FR of its own, and `tasks.md` is not used: the prd-gate plan is |
| LT12 | The spec amendment path (new FRs appended to `specs/NNN-*/spec.md`) is removed from the plan routing |

## Where each fact lives
| Fact | Living home | During the change |
|---|---|---|
| Behavior, edge cases, measurable targets | `docs/prd/` | Row with Source `planned` |
| Code structure, invariants | `docs/trd/` | `## Planned` section |
| Structural decision | `docs/adr/` | `design.md` draft |
| Data model, API contract | The real artifact, linked from the TRD | `design.md` draft |
| Principles | `.specify/memory/constitution.md` | none |
| Why, scope, slices | `changes/NNN-<slug>/brief.md`, archived after merge | |
| Tasks, deliveries | `changes/NNN-<slug>/plan.md`, archived after merge | |

## Open items
- The constitution stays at `.specify/memory/constitution.md` for compatibility; moving it is a separate decision.
