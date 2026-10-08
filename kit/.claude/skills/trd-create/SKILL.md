---
name: trd-create
description: Creates the TRD of this repository, the technical map that tells an agent where each product feature lives in the code, how it enters the flow, which tests cover it and what must not break, so it loads only the files a task needs. Writes docs/trd/README.md, one file per area (1:1, wherever its files live), the cross-cutting infra map, invariants.md (repository rules by kind of change, each with its proof), testing.md (how to test here), docs/flow.md (the one end-to-end diagram), one CLAUDE.md of at most 20 lines per map folder, and links each PRD section to its TRD in docs/prd/INDEX.md. Works in any layout (feature folders recommended, never required). When the code is not organized by feature, it proposes the AI readiness plan in the current layout and offers the optional move to feature folders. Use after /prd-create, after a large refactor, when someone says "create the TRD", "map the code", "document where things live", "add CLAUDE.md files", "make the repo AI-readable", or when prd-flow finds no TRD. Not for product rules (prd-create, prd-flow).
---

# trd-create

The TRD says **where** behavior lives; the PRD says **what** it is. The TRD never repeats a rule: it cites PRD IDs. It names files and symbols, never line numbers or default values, so it stays true while the code changes. Everything is in English. Values specific to this repository are in `.claude/skills/prd-flow/repo.md`.

## Principles
| ID | Principle |
|---|---|
| T01 | **1:1 with the areas.** One `docs/trd/<area>.md` per area (rule AR13): a feature folder, or an `areas` entry of `ai-kit.json` whose files live wherever the layout puts them. Shared code gets `infra.md`. In a monorepo, `docs/trd/<package>/<area>.md` |
| T02 | **Names, never lines or defaults.** Files, symbols, event and log names; nothing that changes without the map being touched |
| T03 | **Cite, do not copy.** Every row of "Where it lives" lists the PRD IDs it implements; rule text stays in the PRD |
| T04 | **Verified, not assumed.** Every file and symbol named exists (one `Grep` each); every entry point has a caller outside the tests or is marked "not wired" |
| T05 | **Small maps in the folders.** Each map folder (AR07) gets a `CLAUDE.md` of at most 20 lines: a feature folder the feature map, a folder holding several areas the folder map (`docs/templates/folder-CLAUDE.md`), each pointing to the TRDs; loaded only when working there |
| T06 | **Invariants carry proof.** Every line of `invariants.md` names the test or the principle that proves it |
| T07 | Everything in English; no em dash; tables over prose |
| T08 | **Budget and parts.** An area whose file passes `trd_budget_lines` (`repo.md`, default 250) splits into `docs/trd/<area>/<part>.md`, parts mirroring the PRD section groups, plus `docs/trd/<area>/README.md` listing them; `docs/trd/README.md` points to the folder. There is no History section |
| T09 | **Checkable by `gate.py --trd`.** Paths are real tracked files (G23); symbols in `Main symbols` exist in the row's files (G24); IDs in the `IDs` column are cited by the row's files (G25); no file over budget (G26). Paths of files a change will create go in "Planned", never in "Where it lives" |
| T10 | **Planned holds names only.** `\| File \| Changes or creates \| Symbols \| IDs \|`; no parameters, intervals or values (rules or contracts). Tests to write: file and IDs, never expected values (the PRD Example). Contracts live in `design.md`, linked |

## Modes
| Mode | When |
|---|---|
| N1 full | No `docs/trd/` yet; works in any layout (areas = feature folders plus `ai-kit.json` `areas`) |
| N2 one area | A new area appeared, or one map is stale |
| N3 refresh | After a refactor moved files: re-verify every map and fix names; no History section (git log is the history) |
| N4 readiness | The code is not organized by area (logic for one product area spread over many folders, files over the size limits, generic names). Map what exists by area, then write the incremental readiness plan in the current layout (`reference/readiness.md`, PC11) for prd-flow |
| N5 restructure | Optional, offered after N4 with its cost (PC09): move to feature folders (`reference/restructure.md`, prd-flow C6). Never required |

## Route
| Step | Who | Does | Leaves |
|---|---|---|---|
| 1 | chief | Asks the mode; a `scoper` reads `repo.md`, `docs/prd/INDEX.md`, the source tree two levels deep and `docs/code-structure.md`, writes `state.md` (slug `trd-create`, base commit) and returns the facts | state |
| 2 | `scoper` (strongest model), chief asks | Area list from the layout (`docs/code-structure.md` "This repository's layout", `ai-kit.json` `feature_root`, `areas`, `map_dirs`): one row per area with files or globs and PRD sections; writes `features.md`, returns it as a table; the chief asks, at most 4 questions | `features.md` |
| 3 | `feature-mapper`, waves of at most 4 | One area each: files, roles, symbols, IDs, entry into the flow, tests, must-not-break, pitfalls; passes `trd_budget_lines` so it can split into parts (T08) and runs `gate.py --trd` on its files | `docs/trd/<area>.md` or `docs/trd/<area>/`, `CLAUDE.md` of its own folder if it has one |
| 4 | `infra-mapper` | Shared code, configuration, persistence, providers, observability | `docs/trd/infra.md` |
| 5 | `rules-writer` | `invariants.md` from the constitution, `AGENTS.md` and the structural tests, with the patterns to copy (DS31); `testing.md` from `repo.md`, the test configuration, fakes and guards, schema and contract snapshots (DS30). Counts the invariant gaps, proposes a lint rule or test per gap ranked by hotspots and records `allowlist.invariant_gaps`; proposes contract snapshots when `repo.md` lists a sibling consumer | two files |
| 6 | `index-writer` | `docs/trd/README.md`, `docs/flow.md`, the TRD column of `docs/prd/INDEX.md`, the folder maps of `map_dirs`; `gate.py` and `gate.py --trd` | index files |
| 7 | `scoper` in N4, chief asks | N4: the readiness plan (`reference/readiness.md`), then the N5 offer with its cost (`reference/restructure.md`), returned as a table for approval | plan |
| 8 | `index-writer` commits; chief reports | Commits `docs(trd): map <scope>` and, separately, `docs: add CLAUDE.md maps`. Read-back from the returns, at most 20 lines: areas, unwired entry points, hotspots, allowlist size, invariant gaps, snapshots proposed; next `/prd-flow` | commits |

The main thread is a chief: it asks the user, dispatches workers and routes returns by `Status`, `Files`, `Commit`, `Route`, `Next`; it never maps, writes docs or runs scripts; reads only `state.md`. Worker: Agent `general-purpose`, prompt *"Read `.claude/skills/trd-create/reference/workers.md`, section `<name>`, and run it for slug `trd-create`. Assignment: <areas>."* Never paste briefings into the prompt. Each worker writes only its own files.

| Rule | Value |
|---|---|
| Input | Bounded: the exact area folders or globs and its PRD sections, plus a read budget (about 30k tokens); Grep first, then Read by range |
| Output | Its own files; the return ends with `Status` (done, gap, blocked), `Files`, `Commit`, `Route` (none, `user: <question>`, or `<worker>: <handoff>`) and `Next`; the chief never reopens them |
| Reruns | A worker reruns a failing gate twice, then returns `blocked` with `Route` to a fresh worker of its role (error lines) or to the user; no `Route`: sent back once, then the user |
| Model | By role: the `scoper` (area list, cross-area consistency) on the strongest model; `feature-mapper`, `infra-mapper` and the writers on `sonnet` |
| Waves | At most 4 mappers, disjoint files; areas that read the same large files go to one mapper |
| Budgets | Independent reads in one message; code only by symbol; no ToolSearch mid-run; about 50 tool calls per worker |

## Files
| File | Who reads it |
|---|---|
| `reference/workers.md` | each worker, only its section |
| `reference/readiness.md` | the `scoper` in N4 |
| `reference/restructure.md` | the `scoper` in N5 |
| `docs/ai-readiness.md` | the `scoper` in N4 |
| `docs/templates/trd-feature.md`, `docs/templates/feature-CLAUDE.md` | the feature-mapper |
| `docs/templates/folder-CLAUDE.md` | the index-writer |
| `.claude/skills/prd-flow/scripts/gate.py` (`--trd`) | run only |