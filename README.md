# AI Starter Kit

[![CI](https://github.com/mtperessoni/ai-starter-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/mtperessoni/ai-starter-kit/actions/workflows/ci.yml)

**Make any repository AI-driven in one command.** The kit installs a PRD and TRD that act as the single source of truth for product behavior, a gate that sends every change through them, subagents that work in parallel cheaply and talk through files, tests that run only for what changed, and a code structure an agent can navigate without reading whole files. It adapts itself to the project's stack.

Every rule here was built, measured and corrected in a production AI service, then extracted so new projects start where that one ended.

## Why

AI agents in a real codebase fail in predictable ways: they read whole files to find one rule, they rediscover the domain on every task, they implement from the code instead of from a decision, they run the whole test suite after every edit and then spend hours fixing tests unrelated to their change, and review loops never end.

What the rules in this kit changed, measured in the source repository:

| Change | Result |
|---|---|
| Orchestrator conducts, workers write files, the orchestrator reads only their short returns | End-to-end time -48%, cost -53%, main context peak from 196k to 76k tokens, same quality |
| PRD split into one small file per section, with an index, instead of two files of 64k and 165k characters | An agent loads the one rule it needs |
| Related tests only while working, the full suite once at the end against a baseline | Tasks that took 13 to 14 minutes because each ran the full suite stopped doing it |
| Code restructured by feature, size limits enforced by a ratchet | Modules over 500 lines from 18 to 1; a 4,056-line class became 23 collaborators |
| Review capped at 5 rounds, re-review scoped to the previous findings | The loop that had consumed 3.6 of 8.8 agent hours in one delivery stopped |

## How it works

```mermaid
flowchart LR
    I["/ai-kit install<br/>adapts the kit to the stack"] --> P["/prd-create<br/>PRD from code, docs or interview"]
    P --> T["/trd-create<br/>code map, CLAUDE.md per feature"]
    T --> G{"/prd-gate<br/>every change"}
    G -->|question| A[Answer with rule IDs and sources]
    G -->|bug or approved rule| X[Plan, then agents implement test-first]
    G -->|rule change| R[Confront, interview, PRD, TRD, plan, then code]
    X --> V[Related tests per task, review capped, full suite once]
    R --> V
    V --> M[Promote to PRD, TRD, ADR; archive the change folder]
```

Every fact has one living home, and everything else cites it by ID. A change gets a folder `changes/NNN-<slug>/` sized by risk; it holds intent, plan and state, never truth. At the end what is durable is promoted to its living home and the folder moves to `changes/archive/`.

| Size | When | Folder holds |
|---|---|---|
| S | Bug, approved rule, stale PRD, refactor | Nothing, or only `plan.md` |
| M | Rule change with an evident design | `brief.md` (why, scope, slices, success criteria as rule IDs) and `plan.md` |
| L | Rule change with a new data model, contract, integration, technical unknown or feature area | `brief.md`, `design.md` and `plan.md` |

| Fact | Living home |
|---|---|
| Behavior, edge cases, targets | `docs/prd/` |
| Code structure, invariants | `docs/trd/` |
| Structural decision | `docs/adr/` |
| Data model, API contract | The real artifact, linked from the TRD |
| Principles | `.specify/memory/constitution.md` |

Order of authority: constitution, PRD, TRD, code. An active plan governs only the order of work. `gate.py --trace`, `--change` and `--final` check that every rule has a test, every brief cites real rules, and nothing half-promoted reaches the base branch.

| Skill | What it does |
|---|---|
| `/ai-kit` | Global. `install` detects the stack, copies and adapts the kit, configures the linter with a day-one baseline, verifies every command by running it. `update` brings kit improvements without overwriting the project's edits. `doctor` reports drift |
| `/prd-create` | Writes the PRDs: one folder per independent flow, one small file per section, rule rows with source and change via, glossary with code names, journey, configuration, risks, open questions, and the HTML reading version |
| `/trd-create` | Writes the technical map: one file per feature, invariants with their proof, the testing guide, the end-to-end flow, and a `CLAUDE.md` of at most 20 lines in every feature folder |
| `/prd-gate` | The gate for every change. Classifies the request, loads only the rule and the map it needs, checks the doc against the code, and for a rule change runs confront, interview, PRD, TRD, plan, then subagents implement |
| `/adr` | Records architecture decisions with at least two honest negatives and two real alternatives |

## Quick start

Requirements: [Claude Code](https://claude.com/claude-code), git, Python 3.10 or later (for the kit's scripts, whatever the project's stack), bash (Git Bash on Windows).

```bash
# 1. Once per machine
git clone https://github.com/mtperessoni/ai-starter-kit.git
cd ai-starter-kit
./install.sh            # Windows PowerShell: ./install.ps1
```

```text
# 2. In each project, inside Claude Code
/ai-kit install         # detects the stack, shows the plan, adapts, verifies, commits on a branch
/prd-create             # the PRD, from the code (or by interview in a new project)
/trd-create             # the code map and the feature CLAUDE.md files

# 3. From then on
/prd-gate <any change or question about behavior>
```

To bring kit improvements into a project later: `git pull` in the kit, `./install.sh` again, then `/ai-kit update` in the project.

## What lands in a project

```
CLAUDE.md                       constitution index, the gate rule, code structure summary
AGENTS.md                       commands, critical constraints, finding things, handing work to subagents
ai-kit.json                     stack commands, structure limits, ratchet allowlist
.ai-kit/manifest.json           kit version and the files it owns
.specify/memory/constitution.md binding principles: the project's own plus the kit's process principles
.claude/skills/                 prd-create, trd-create, prd-gate (with repo.md, the project adapter), adr
.claude/agents/                 one findings-only reviewer per risk class of the domain
docs/prd/                       INDEX.md, README.md, CHANGELOG.md, prd.html, one folder per PRD
docs/trd/                       README.md, one file per feature, infra.md, invariants.md, testing.md
docs/code-structure.md          AR01 to AR14: where and how code lives
docs/flow.md, docs/adr/         the one end-to-end diagram; decision records
changes/, changes/archive/      change folders in flight (brief, design, plan) and the finished ones
docs/templates/                 PRD section, TRD feature, feature CLAUDE.md, HTML shell, reviewer agent
scripts/                        gates.sh, ratchet.py, related_tests.py, new_failures.py, move_lines.py,
                                telemetry_hook.py, run_probe.py, retro.py
.claude/settings.json           the telemetry hooks, merged into the project's own
.ai-kit/runs/                   run telemetry (git-ignored)
.github/workflows/              CI and the automated Claude review on every pull request
.gitattributes, .gitleaks.toml  LF everywhere; secret scan
```

## Run telemetry
Hooks record every tool call, subagent, compaction and wait of a run in `.ai-kit/runs/<change>/` (git-ignored), and `scripts/gates.sh` adds the time, memory and disk of each test and build. Outputs are never stored and secrets are redacted. At the end of a delivery `scripts/gates.sh retro` writes `retro.md`: findings only for what passed a threshold of `ai-kit.json` `telemetry` (slow calls, heavy subagents, loops, big outputs, memory, disk), none when the run stayed within all of them. The final report lists them. Rules: [rules/11-telemetry.md](rules/11-telemetry.md).

## The rules, in short

The full catalog, with the reason for each rule and the file that enforces it, is in [rules/](rules/README.md).

| Area | The rule that matters most |
|---|---|
| Source of truth | Behavior lives in the PRD as rule rows with permanent IDs; a rule change goes PRD, TRD, plan, code, after the person asking sees the current rule and confirms ([WF](rules/07-workflow.md)) |
| Lazy loading | Small files, an index, maps by symbol name; agents read the markdown one section at a time and never the HTML ([CE](rules/01-context-economy.md)) |
| Subagents | One-line prompts pointing to a briefing section; outputs written to a state folder; returns of at most 20 or 30 lines; no nested subagents; ceilings of calls and minutes ([SA](rules/02-subagents.md)) |
| Tests | Test first; only the mirror test and the importers of what changed while working; the full suite once at the end against a baseline, so agents never chase failures they did not cause ([TS](rules/04-testing.md)) |
| Review | At most 5 rounds per delivery, scoped re-review, stop and ask on an open Critical ([RV](rules/03-review.md)) |
| Structure | One folder per PRD area, size limits, unique descriptive file names, the PRD ID in every module and test, a `CLAUDE.md` map per feature, enforced by a shrink-only ratchet ([AR](rules/05-code-structure.md)) |
| Writing | Everything in English, tables over prose, no em dash, no comments without a critical why ([WS](rules/08-writing-style.md)) |

## Stacks

The kit itself is stack-free. `/ai-kit install` reads the matching [recipe](stacks/README.md) for commands, test runner, linter rules and CI setup, prefers the project's own scripts, and verifies each command by running it.

| Recipe | Ecosystems |
|---|---|
| [python](stacks/python.md) | uv, Poetry, pip; pytest; ruff, mypy |
| [node](stacks/node.md) | npm, pnpm, yarn, bun; Vitest, Jest; ESLint, TypeScript; any framework |
| [go](stacks/go.md) | go test; golangci-lint |
| [jvm](stacks/jvm.md) | Gradle, Maven; JUnit; Checkstyle, detekt, ArchUnit |
| [dotnet](stacks/dotnet.md) | dotnet test; analyzers, NetArchTest |
| [rust](stacks/rust.md) | cargo test; clippy |
| [ruby](stacks/ruby.md) | RSpec, Minitest; RuboCop, packwerk |
| [php](stacks/php.md) | PHPUnit, Pest; PHPStan, PHPMD, deptrac |
| [generic](stacks/generic.md) | Anything else: the installer researches, asks and verifies |

## FAQ

**Does a `CLAUDE.md` in every folder help? Is it loaded by Claude Code?**
Yes, lazily. Root and parent `CLAUDE.md` files load at session start; a subfolder's `CLAUDE.md` loads only when Claude reads, writes or edits a file in that folder, and reloads after `/compact`. The kit puts one short map (at most 20 lines) in each feature folder, not in every folder, and never `@`-imports them from the root, which would load them eagerly.

**Why keep both markdown and HTML for the PRD?**
People read the HTML (tabs per PRD, filters by where a rule changes, diagrams). Agents read only the markdown, one section at a time. The gate checks that both carry the same words.

**Can a project have several PRDs and TRDs?**
Yes. One PRD folder per independent flow, one TRD file per feature folder, nested by package in a monorepo.

**Do I need spec-kit?**
No. The kit never installs it and no text of the kit depends on it. The change folders under `changes/` replace `spec.md`, `plan.md` and `tasks.md`, and the plan's `Constitution check` replaces spec-kit's Constitution Check and Complexity Tracking. The constitution stays at `.specify/memory/constitution.md` for compatibility. A project that keeps spec-kit marks it `kept` in `repo.md`: its `spec.md` then cites PRD rule IDs and defines no requirements of its own, `tasks.md` is not used, and a legacy `specs/` stays untouched as history.

**What if the codebase is organized by layer, not by feature?**
`/trd-create` maps what exists and writes a structure-only refactor plan: code moved by script, never retyped, the ratchet lowered wave by wave.

## Repository layout

| Path | Content |
|---|---|
| [kit/](kit/) | The payload copied into each project |
| [installer/ai-kit/](installer/ai-kit/) | The global `/ai-kit` skill |
| [stacks/](stacks/) | Adaptation recipes per ecosystem |
| [rules/](rules/) | The rule catalog: every rule, its reason and where it lands |
| [global/CLAUDE.md](global/CLAUDE.md) | The block every machine gets in `~/.claude/CLAUDE.md` |
| [tests/](tests/) | End-to-end tests of the kit scripts against a throwaway project |
| [MAINTAINING.md](MAINTAINING.md) | How to evolve the kit, add a recipe and evaluate the skills |

## Contributing

Improvements found while using the kit in a project come back here first, then reach every project through `/ai-kit update`. See [MAINTAINING.md](MAINTAINING.md).
