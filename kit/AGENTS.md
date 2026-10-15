# AI agent instructions: <project>

<One paragraph: what it is, stack, package manager.>

`.specify/memory/constitution.md` is binding and it wins over this file when they disagree. Order of authority: the constitution, then the PRD (`docs/prd/`) on behavior, then the TRD (`docs/trd/`) on structure, then the code. An active plan in `changes/` governs only the order of work; nothing under `changes/archive/` or a legacy `specs/` is read to learn current behavior.

## Commands

```bash
<install>                              # Install dependencies (locked)
<dev>                                  # Dev server
scripts/gates.sh related [files]       # The tests related to the change (mirror and importers)
scripts/gates.sh one <file>            # One test file, offline
scripts/gates.sh fix-files <file>...   # Repair only those files
scripts/gates.sh lint-files <file>...  # Lint only those files
scripts/gates.sh lint                  # Lint, format check, types, structure rules, as CI does
scripts/gates.sh baseline <slug>       # Before the first code task: record today's failures (background)
scripts/gates.sh compare <slug>        # Once, at the end of a delivery: the full suite, new failures only
scripts/gates.sh move <src> <start> <end> <dest> [--at LINE]   # Move lines by script, never retyped
scripts/gates.sh setup                 # Make a fresh clone or worktree ready to test
scripts/gates.sh reap                  # Kill stuck processes of this session by PID tree
```

`scripts/gates.sh` with no target lists every other target (docs, html, verify, close, integration, build, sweep, docker-clean, cleanup). The stack commands behind each target are in `ai-kit.json`.

## Working rules

- Read a file with the Read tool before editing it (a shell read does not count); batch independent reads; one pass of changes per file.
- Tests: failing test first. Before handing back a slice, `related` on the touched files, then `fix-files` and `lint-files`. Every test has a per-test timeout. The full suite runs once per delivery against the baseline; an unrelated failure is reported, not investigated. Test output goes to a file; read only failures and the summary.
- Processes: a subagent runs a long command in the foreground with a timeout under 600 s; only the main thread starts background work, with a timeout longer than the run. No polling loops, no unbounded output. Never kill by image name (`taskkill /IM`, `pkill`, `killall`): `scripts/gates.sh reap`.
- Subagents: by default the session that executes a slice writes the code. A subagent prompt carries the goal, the acceptance items, the done condition and at most about 5 paths; it returns at most 15 lines (done, files, tests, gaps, minutes used), never opens another subagent, and hands back past about 150k tokens. prd-flow agents use `.claude/skills/prd-flow/reference/run.md` "Every agent". Leftovers go back to the person.
- Docker: build or pull only through `scripts/gates.sh build|integration|full`; every image, container, volume and network carries the `repo` and `purpose` labels of `ai-kit.json` "docker"; a one-off container is `--rm`. Clean up with `docker-clean` and `clean-outputs`.
- Telemetry: hooks record each tool call in `.ai-kit/runs/` (git-ignored), silently. `scripts/gates.sh retro` shows where a run went when a person asks; `close` does not run it.
- The full gate sets its own environment (no network, no database for the unit tier); see `docs/trd/testing.md`.

## Critical constraints

Violating any of these breaks the architecture or the safety model. Follow strictly.

1. **NEVER swallow an exception and never fire-and-forget.** Every failure is persisted or logged with its cause. An empty `catch` is a violation.
2. **NEVER hardcode a credential, token, key, model id, prompt or per-customer rule.** It is typed configuration or versioned data. The service refuses to boot on missing or malformed config.
3. **NEVER branch on a customer or tenant name.** Per-tenant behavior is a configuration row resolved at runtime.
4. **NEVER let framework or vendor types cross into the domain layer.** Framework at the edges.
5. **Tests run offline and deterministic.** Fakes by default; tests that need the network or a real model sit behind a marker and never gate a merge.
6. **NEVER use the em dash character.** Use a comma, colon, period or rewrite. Applies to code, docs, prompts and commit messages.
7. **NEVER add comments unless the WHY is non-obvious and critical.** Default is zero comments. No comment references a ticket or a task.
8. **Every side effect logs**, structured, with the correlation ids of the request.
9. **Language**: code, commits and agent files in English; PRD and TRD in `<PRD and TRD language, declared once here>`; UI copy in the product locale.
10. <Domain constraint.>

## Code structure

All code follows `docs/code-structure.md` (rules AR01 to AR28), enforced by `scripts/gates.sh ratchet` and the linter rules behind `lint`.

- **Where:** `<layout of this repository, filled at install>`; feature folders (`<src>/features/<f>/` per PRD area) are recommended, any declared layout works. Start a task with the area's map (`CLAUDE.md`) and its TRD in `docs/trd/`.
- **Size:** module up to 500 lines, function up to 80, class up to 300, test file up to 1,200. One responsibility per file, named after it; never `helpers`, `utils`, `shared`, `common`, `misc`, `state`.
- **Shape:** composition over mixins; explicit state, no shared mutable closures; re-export only in an area's public entry.
- **Tests** sit where the stack expects them, beside the code or its mirrored tree (AR10); mocks target the module of the caller.
- **Moving code:** by script (line ranges or AST), never retyped.

## Directory map

- `<folder>/`: `<its role, the areas with files there and its map>`; one line per real folder, filled at install (layout in `docs/code-structure.md`)
- `tests/integration/`, `tests/eval/`, and unit tests where `docs/trd/testing.md` says
- `changes/NNN-<slug>/`: one folder per size L change in flight (`plan.md` and `decisions.md`, also `brief.md` and `design.md`). Intent, plan and decisions, never truth
- `changes/archive/`: finished size L changes, moved there with `git mv`. History only
- `docs/prd/`, `docs/trd/`, `docs/adr/`, `docs/code-structure.md`, `docs/flow.md`

## Workflow

1. A rule change is shown to the person (today's rule and what would change) and confirmed before the code. The commit that implements it updates the PRD row; its body says what was decided (`Decided:`). Git is the history of a rule.
2. Before the first edit: the goal, what is out of scope and an estimate in minutes, agreed by the person. Size **S** and **M** write no plan files; **L** writes `changes/NNN-<slug>/plan.md` (about 100 lines: decisions, slices, acceptance items) after a design review.
3. One vertical slice per delivery (about 30 files or 2 hours, its own PR), test first, written by the session that executes it; defects ship as small fixes before any restructuring.
4. Gates before merge: lint, type check, full suite green, coverage not decreasing, ratchet green.

## Finding things

Load only what the task needs. Every step below is one Glob, Grep or ranged Read.

1. **Product rules.** `docs/prd/INDEX.md` lists every PRD file with the rule IDs it defines. `Grep "<ID>" docs/prd` finds a rule; the same ID in a test docstring finds its tests. A human-reading HTML is never read for work.
2. **Where it lives in the code.** `docs/trd/README.md` lists the areas; the area map (its `CLAUDE.md`, or its row in a folder map) and `docs/trd/<area>.md` give the files, the entry points by symbol name, the tests and what must not break.
3. **Repo rules by kind of change** are in `docs/trd/invariants.md`; **how to test** is in `docs/trd/testing.md`.
4. **Big files** (listed in `.claude/skills/prd-flow/repo.md`): Grep for the symbol, then Read that range.
5. **Generated files** (`generated_patterns` in `ai-kit.json`) are never edited and not searched. **Schema and contracts:** read the snapshot listed in `contracts`, never the migration history (DS30).
6. **History of an area:** `git log --oneline -- <paths from its TRD file>`.

Keeping it true: a delivery that moves a file, an entry point or a test updates `docs/trd/<area>.md` and the area's map once, in its last slice (names only, never line numbers or defaults). The PRD file that owns a rule is amended in place; `docs/prd/CHANGELOG.md` is frozen and the history of a rule is `gate.py --history <ID>` and the commit bodies. The docs gate (`scripts/gates.sh docs`) errors only on a duplicate rule ID or a cited ID that does not exist; everything else is a review item.
