# AI agent instructions: <project>

<One paragraph: what it is, stack, package manager.>

`.specify/memory/constitution.md` is binding and it wins over this file when they disagree. `CLAUDE.md` carries the index of its principles; read the full principle your change touches before writing code.

Order of authority: the constitution, then the PRD (`docs/prd/`) on behavior, then the TRD (`docs/trd/`) on structure, then the code. An active plan in `changes/` governs only the order of work; nothing under `changes/archive/` or a legacy `specs/` is read to learn current behavior. See "Finding things" below.

## Commands

```bash
<install>                          # Install dependencies (locked)
<dev>                              # Dev server
scripts/gates.sh related [files]   # The ratchet, then the tests related to the change (a diagnostic for a person)
scripts/gates.sh one <file>        # One test file, offline, no coverage threshold
scripts/gates.sh baseline <slug>   # Before the first code task: record today's failures
scripts/gates.sh compare <slug>    # ONCE, at the end of a delivery: the full suite, new failures only
scripts/gates.sh lint              # Lint, format check, types, structure linter rules: verifies, as CI does
scripts/gates.sh fix               # Repairs; then run lint
scripts/gates.sh imports           # Import check (cycles)
scripts/gates.sh setup             # Make a fresh clone or worktree ready to test
scripts/gates.sh hotspots          # Files ranked by recent commits times lines
scripts/gates.sh contracts         # Schema and contract snapshots against their source
scripts/gates.sh ratchet           # Structure ratchet (docs/code-structure.md)
scripts/gates.sh docs              # PRD and TRD consistency (a stale HTML page is only a warning)
scripts/gates.sh html [--check]    # Build (or check) the PRD and TRD reading pages; run by /docs-html, never by prd-flow
scripts/gates.sh trailers [range]  # Every commit that touches source folders carries Rules: or Case: none
scripts/gates.sh integration       # Integration tier: disk and image guards first, cleanup on every exit
scripts/gates.sh build [args]      # The only way to build images: same guards, same cleanup
scripts/gates.sh sweep             # Remove test containers, volumes, networks left by killed runs
scripts/gates.sh docker-clean      # Every labelled leftover; reports other projects' images, never removes them
scripts/gates.sh clean-outputs     # Delete old or oversized background task outputs
scripts/gates.sh context NAME      # Name the run for telemetry (prd-flow does it with the slug)
scripts/gates.sh retro             # End of a delivery: what was slow, expensive, looping or wasteful
scripts/gates.sh reap              # Kill stuck processes of this session by PID tree, never by image name
```

The stack commands behind each target are in `ai-kit.json`.

### Testing while working
- For a person: `scripts/gates.sh related` finds the mirror test of each changed module and every test that imports it, runs them, and prints only failures and the summary. Add lint of the touched files.
- A prd-flow executor runs only its own test, then `scripts/gates.sh fix-files <file>...` and `lint-files <file>...` on its own files; the chief runs one `scripts/gates.sh verify <slug>` per wave.
- Never kill processes by image name (`taskkill /IM`, `pkill`, `killall`); use `scripts/gates.sh reap`.
- The full suite runs once, at the end of a delivery, compared with the recorded baseline of failures. A failure unrelated to what you touched waits for the end.
- Redirect test output to a file and read only the failures and the summary.
- The full gate sets its own environment (no network, no database for the unit tier); never rely on your shell's variables to make it offline. See `docs/trd/testing.md`.

### Disk and container hygiene
- Never start a background command with unbounded output: no `tail -f`, no printing poll loops. Output goes to a file; read its tail or the failure summary.
- Prefer a throwaway database container or in-process fakes over building images; only a test that proves services start together builds images, once per session.
- Every image, container, volume and network carries the `repo` and `purpose` labels (`purpose=test|dev|spike`) under the `label_namespace` of `ai-kit.json` "docker", one tag per image. Stacks started by tests are `purpose=test`.
- Build or pull only through `scripts/gates.sh build|integration|full`; they refuse when the disk or an image cap is short and clean up on every exit. Run long integration runs in the background with output to a file and a timeout longer than the run, so they are not killed mid-stack.
- A one-off container is `--rm` and labelled `purpose=test`; an image pulled only for it is removed in the same step. A spike removes its images, and the third-party images it pulled, when it ends.
- Clean up with `scripts/gates.sh docker-clean` and `clean-outputs`. On Docker Desktop, freed space returns to the host only after Docker Desktop is quit, or after compacting its disk file as admin.

### Run telemetry
- Hooks record every tool call, subagent, compaction and wait as one line in `events.jsonl` under `.ai-kit/runs/`, one folder per change or branch (git-ignored); `gates.sh` test and build targets add `resources.jsonl` (time, memory, disk, tests collected). Tool outputs are never stored; commands are truncated and secrets redacted.
- Nothing to run while working: the hook is silent and never blocks.
- At the end of a delivery, after the full suite, run `scripts/gates.sh retro`. It writes `retro.md` with findings only for metrics past the thresholds of `ai-kit.json` `telemetry`; a run within every threshold has none. Report the findings, or say the run stayed within every threshold.

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
9. **Everything is in English**: code, docs, PRD, TRD, skill artifacts, commit messages.
10. <Domain constraint.>

## Directory map

- `<folder>/`: `<its role, the areas with files there and its map>`; one line per real folder, filled at install (layout in `docs/code-structure.md`; feature folders are recommended, not required)
- `tests/integration/`, `tests/eval/`, and unit tests where `docs/trd/testing.md` says
- `changes/NNN-<slug>/`: one folder per change in flight (`brief.md` for size M and L, `design.md` for size L, `plan.md`). Holds intent, plan and state, never truth
- `changes/archive/`: finished changes, moved there with `git mv` when promoted. History only, never read for current behavior
- `docs/prd/`, `docs/trd/`, `docs/adr/`, `docs/code-structure.md`, `docs/flow.md`

## Workflow

Living truth plus change folders, in this order. Do not skip steps.

1. `/prd-flow` classifies the request; a rule change updates PRD and TRD and produces the plan. Product changes run through prd-flow, whose main thread coordinates the agents (`.claude/agents/prd-flow-*`) and executes no task; the executor `close` mode promotes, commits and runs the closing gate
2. The change folder by size, decided at classification: **S** no folder or only `plan.md`; **M** `brief.md` and `plan.md`; **L** `brief.md`, `design.md` and `plan.md`. The plan header carries a `## Constitution check`
3. Implementation test first, one task per agent, one commit per task. A commit that touches source folders ends with a trailer naming the rule IDs it serves (`Rules: CHK-02, CHK-05`) or, when it serves none, the reason in at most 8 words (`Case: none (dependency bump)`); `scripts/gates.sh trailers` checks it
4. Gates before merge: lint, type check, full suite green, coverage not decreasing, ratchet green
5. Promote: what is durable goes to its living home (PRD, TRD, ADR, schema or contract) and the folder is archived with `git mv changes/NNN-<slug> changes/archive/NNN-<slug>`

## Finding things

Load only what the task needs. Every step below is one Glob, Grep or ranged Read.

1. **Product rules.** `docs/prd/INDEX.md` lists every PRD file (one per section) with the rule IDs it defines. `Grep "<ID>" docs/prd` finds a rule; the same ID in a test docstring finds its tests. A human-reading HTML, if any, is never read for work.
2. **Where it lives in the code.** `docs/trd/README.md` lists the areas. The area map (its `CLAUDE.md`, or its row in a folder map) and `docs/trd/<area>.md` give the files, the entry points by symbol name, the tests and what must not break.
3. **Repo rules by kind of change** are in `docs/trd/invariants.md`; **how to test** is in `docs/trd/testing.md`.
4. **Big files** (listed in `.claude/skills/prd-flow/repo.md`): Grep for the symbol, then Read that range. Never read them whole.
5. **Generated files** (`generated_patterns` in `ai-kit.json`) are never edited and not searched: change the source and regenerate. **Schema and contracts:** read the snapshot listed in `contracts` and linked from the TRD, never the migration history (DS30).
6. **History of an area:** `git log --oneline -- <paths from its TRD file>`.

Keeping it true:

- A code change that moves a file, an entry point or a test of an area updates `docs/trd/<area>.md` and the area's map in the same commit. Names only, never line numbers or default values.
- A change to product behavior updates the PRD file that owns the rule ID and moves the superseded wording to `docs/prd/CHANGELOG.md`: the PRD body holds only what is valid today.
- The `prd-flow` skill runs this flow and checks it with `.claude/skills/prd-flow/scripts/gate.py`.

## Handing work to a subagent

Paste the rule rows it must implement (its contract) and point to files for everything else: the PRD file, the TRD feature file, the files it owns and the commands to run. Never paste whole documents. It returns at most 20 lines with the five fields `Status`, `Files:`, `Commit:`, `Route:`, `Next:`, writes longer output to files, never opens another subagent, and stops at about 50 tool calls or 30 minutes to report.
