---
name: trd-create
description: Creates the TRD of this repository, the technical map that tells an agent where each product feature lives in the code, how it enters the flow, which tests cover it and what must not break, so it loads only the files a task needs. Writes docs/trd/README.md, one file per area (1:1, wherever its files live), the cross-cutting infra map, invariants.md (repository rules by kind of change, each with its proof), testing.md (how to test here), docs/flow.md (the one end-to-end diagram), one CLAUDE.md of at most 20 lines per map folder, and links each PRD section to its TRD in docs/prd/INDEX.md. Works in any layout (feature folders recommended, never required). When the code is not organized by feature, it proposes the AI readiness plan in the current layout and offers the optional move to feature folders. Use after /prd-create, after a large refactor, when someone says "create the TRD", "map the code", "document where things live", "add CLAUDE.md files", "make the repo AI-readable", or when prd-gate finds no TRD. Not for product rules (prd-create, prd-gate).
---

# trd-create

The TRD says **where** behavior lives; the PRD says **what** it is. The TRD never repeats a rule: it cites PRD IDs. It names files and symbols, never line numbers or default values, so it stays true while the code changes. Everything is in English. Values specific to this repository are in `.claude/skills/prd-gate/repo.md`.

## Principles
| ID | Principle |
|---|---|
| T01 | **1:1 with the areas.** One `docs/trd/<area>.md` per area (rule AR13): a feature folder, or an `areas` entry of `ai-kit.json` whose files live wherever the layout puts them. Shared code gets `infra.md`. In a monorepo, `docs/trd/<package>/<area>.md` |
| T02 | **Names, never lines or defaults.** Files, symbols, event and log names; nothing that changes without the map being touched |
| T03 | **Cite, do not copy.** Every row of "Where it lives" lists the PRD IDs it implements; rule text stays in the PRD |
| T04 | **Verified, not assumed.** Every file and symbol named exists (one `Grep` each); every entry point has a caller outside the tests or is marked "not wired" |
| T05 | **Small maps in the folders.** Each map folder (AR07) gets a `CLAUDE.md` of at most 20 lines: a feature folder the feature map, a folder holding several areas the folder map (`docs/templates/folder-CLAUDE.md`), each pointing to the TRDs. Claude Code loads a subfolder's `CLAUDE.md` only when a file of that folder is read, written or edited, so these maps cost nothing until the agent works there |
| T06 | **Invariants carry proof.** Every line of `invariants.md` names the test or the principle that proves it |
| T07 | Everything in English; no em dash; tables over prose |

## Modes
| Mode | When |
|---|---|
| N1 full | No `docs/trd/` yet; works in any layout (areas = feature folders plus `ai-kit.json` `areas`) |
| N2 one area | A new area appeared, or one map is stale |
| N3 refresh | After a refactor moved files: re-verify every map, fix names, keep History |
| N4 readiness | The code is not organized by area (logic for one product area spread over many folders, files over the size limits, generic names). Map what exists by area, then write the incremental readiness plan in the current layout (`reference/readiness.md`, PC11) for prd-gate |
| N5 restructure | Optional, offered after N4 with its cost (PC09): move to feature folders (`reference/restructure.md`, prd-gate C6). Never required |

## Route
| Step | Who | Does | Leaves |
|---|---|---|---|
| 1 | this conversation | Slug `trd-create`, mode, base commit in `state.md`. Batch: `Read repo.md`; `Read docs/prd/INDEX.md`; `Glob` of the source tree two levels deep; `Read docs/code-structure.md` | state |
| 2 | this conversation | Area list from the layout (`docs/code-structure.md` "This repository's layout", `ai-kit.json` `feature_root`, `areas`, `map_dirs`): one row per area with its files or globs and the PRD sections it implements; show it as a table; approve with at most 4 questions | `features.md` |
| 3 | `feature-mapper`, waves of at most 4 | One area each: files, roles, symbols, IDs, entry into the flow, tests, must-not-break, pitfalls | `docs/trd/<area>.md`, `CLAUDE.md` of its own folder if it has one |
| 4 | `infra-mapper` | Shared code, configuration, persistence, providers, observability | `docs/trd/infra.md` |
| 5 | `rules-writer` | `invariants.md` from the constitution, `AGENTS.md` and the structural tests, with the patterns to copy (DS31); `testing.md` from `repo.md`, the test configuration, fakes and guards, schema and contract snapshots (DS30) | two files |
| 6 | `index-writer` | `docs/trd/README.md`, `docs/flow.md`, the TRD column of `docs/prd/INDEX.md`, the folder maps of `map_dirs`; gate | index files |
| 7 | this conversation | N4: the readiness plan (`reference/readiness.md`); then offer N5 with its cost (`reference/restructure.md`). Present as a table for approval | plan |
| 8 | this conversation | Read-back in at most 20 lines: areas mapped, unwired entry points, hotspots over the limits, the ratchet allowlist size. Commits `docs(trd): map <scope>` and, separately, `docs: add CLAUDE.md maps` | commits |

Worker: Agent `general-purpose`, `model: "sonnet"`, prompt *"Read `.claude/skills/trd-create/reference/workers.md`, section `<name>`, and run it for slug `trd-create`. Assignment: <areas>."* Never paste briefings into the prompt. Each worker writes only its own files.

## Context economy
Same as prd-gate: independent reads in one message; code only by symbol; big files only by symbol; returns at most 30 lines; ceiling about 50 tool calls per worker.

## Files
| File | Who reads it |
|---|---|
| `reference/workers.md` | each worker, only its section |
| `reference/readiness.md` | this conversation in N4 |
| `reference/restructure.md` | this conversation in N5 |
| `docs/ai-readiness.md` | this conversation in N4 (the checklist) |
| `docs/templates/trd-feature.md`, `docs/templates/feature-CLAUDE.md` | the feature-mapper |
| `docs/templates/folder-CLAUDE.md` | the index-writer |
| `.claude/skills/prd-gate/scripts/gate.py` | run only |

## Final
Features mapped, files written, unwired code found, commits, and the next step (`/prd-gate` for changes; the readiness plan in N4, with the restructure offered as N5).
