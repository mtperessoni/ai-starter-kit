---
name: trd-create
description: Creates the TRD of this repository, the technical map that tells an agent where each product feature lives in the code, how it enters the flow, which tests cover it and what must not break, so it loads only the files a task needs. Writes docs/trd/README.md, one file per feature (1:1 with the feature folders), the cross-cutting infra map, invariants.md (repository rules by kind of change, each with its proof), testing.md (how to test here), docs/flow.md (the one end-to-end diagram), one CLAUDE.md of at most 20 lines per feature folder, and links each PRD section to its TRD in docs/prd/INDEX.md. When the code is not organized by feature, it also proposes the restructuring plan. Use after /prd-create, after a large refactor, when someone says "create the TRD", "map the code", "document where things live", "add CLAUDE.md files", "make the repo AI-readable", or when prd-gate finds no TRD. Not for product rules (prd-create, prd-gate).
---

# trd-create

The TRD says **where** behavior lives; the PRD says **what** it is. The TRD never repeats a rule: it cites PRD IDs. It names files and symbols, never line numbers or default values, so it stays true while the code changes. Everything is in English. Values specific to this repository are in `.claude/skills/prd-gate/repo.md`.

## Principles
| ID | Principle |
|---|---|
| T01 | **1:1 with the code's features.** One `docs/trd/<feature>.md` per feature folder (rule AR13). Shared code gets `infra.md`. In a monorepo, `docs/trd/<package>/<feature>.md` |
| T02 | **Names, never lines or defaults.** Files, symbols, event and log names; nothing that changes without the map being touched |
| T03 | **Cite, do not copy.** Every row of "Where it lives" lists the PRD IDs it implements; rule text stays in the PRD |
| T04 | **Verified, not assumed.** Every file and symbol named exists (one `Grep` each); every entry point has a caller outside the tests or is marked "not wired" |
| T05 | **Small maps in the folders.** Each feature folder gets a `CLAUDE.md` of at most 20 lines pointing to its TRD. Claude Code loads a subfolder's `CLAUDE.md` only when a file of that folder is read, written or edited, so these maps cost nothing until the agent works there |
| T06 | **Invariants carry proof.** Every line of `invariants.md` names the test or the principle that proves it |
| T07 | Everything in English; no em dash; tables over prose |

## Modes
| Mode | When |
|---|---|
| N1 full | No `docs/trd/` yet |
| N2 one feature | A new feature folder appeared, or one map is stale |
| N3 refresh | After a refactor moved files: re-verify every map, fix names, keep History |
| N4 restructure | The code is not organized by feature (logic for one product area spread over many folders, files over the size limits, generic names). Map what exists by area, then write the restructuring plan (`reference/restructure.md`) for prd-gate C6 |

## Route
| Step | Who | Does | Leaves |
|---|---|---|---|
| 1 | this conversation | Slug `trd-create`, mode, base commit in `state.md`. Batch: `Read repo.md`; `Read docs/prd/INDEX.md`; `Glob` of the source tree two levels deep; `Read docs/code-structure.md` | state |
| 2 | this conversation | Feature list: one row per feature folder (or per area in N4) with the PRD sections it implements; show it as a table; approve with at most 4 questions | `features.md` |
| 3 | `feature-mapper`, waves of at most 4 | One feature each: files, roles, symbols, IDs, entry into the flow, tests, must-not-break, pitfalls | `docs/trd/<feature>.md`, `<feature>/CLAUDE.md` |
| 4 | `infra-mapper` | Shared code, configuration, persistence, providers, observability | `docs/trd/infra.md` |
| 5 | `rules-writer` | `invariants.md` from the constitution, `AGENTS.md` and the structural tests; `testing.md` from `repo.md`, the test configuration, fakes and guards | two files |
| 6 | `index-writer` | `docs/trd/README.md`, `docs/flow.md`, the TRD column of `docs/prd/INDEX.md`; gate | index files |
| 7 | this conversation | N4 only: the restructuring plan (`reference/restructure.md`), presented as a table for approval | plan |
| 8 | this conversation | Read-back in at most 20 lines: features mapped, unwired entry points, files over the limits, the ratchet allowlist size. Commits `docs(trd): map <scope>` and, separately, `docs: add feature CLAUDE.md maps` | commits |

Worker: Agent `general-purpose`, `model: "sonnet"`, prompt *"Read `.claude/skills/trd-create/reference/workers.md`, section `<name>`, and run it for slug `trd-create`. Assignment: <features>."* Never paste briefings into the prompt. Each worker writes only its own files.

## Context economy
Same as prd-gate: independent reads in one message; code only by symbol; big files only by symbol; returns at most 30 lines; ceiling about 50 tool calls per worker.

## Files
| File | Who reads it |
|---|---|
| `reference/workers.md` | each worker, only its section |
| `reference/restructure.md` | this conversation in N4 |
| `docs/templates/trd-feature.md`, `docs/templates/feature-CLAUDE.md` | the feature-mapper |
| `.claude/skills/prd-gate/scripts/gate.py` | run only |

## Final
Features mapped, files written, unwired code found, commits, and the next step (`/prd-gate` for changes; the restructuring plan in N4).
