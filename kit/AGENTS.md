# AI agent instructions: <project>

<One paragraph: what it is, stack, package manager.>

`.specify/memory/constitution.md` is binding and it wins over this file when they disagree. `CLAUDE.md` carries the index of its principles; read the full principle your change touches before writing code.

Order of authority: the constitution, then the PRD (`docs/prd/`) on behavior, then the TRD (`docs/trd/`) on structure, then the code. An active plan in `changes/` governs only the order of work; nothing under `changes/archive/` or a legacy `specs/` is read to learn current behavior. See "Finding things" below.

## Commands

```bash
<install>                          # Install dependencies (locked)
<dev>                              # Dev server
scripts/gates.sh related [files]   # While working: the ratchet, then the tests related to the change
scripts/gates.sh one <file>        # One test file, offline, no coverage threshold
scripts/gates.sh baseline <slug>   # Before the first code task: record today's failures
scripts/gates.sh compare <slug>    # ONCE, at the end of a delivery: the full suite, new failures only
scripts/gates.sh lint              # Lint, format check, types, structure linter rules: verifies, as CI does
scripts/gates.sh fix               # Repairs; then run lint
scripts/gates.sh imports           # Import check (cycles)
scripts/gates.sh ratchet           # Structure ratchet (docs/code-structure.md)
scripts/gates.sh docs              # PRD, TRD and HTML consistency
```

The stack commands behind each target are in `ai-kit.json`.

### Testing while working
- Run only the related tests: `scripts/gates.sh related` finds the mirror test of each changed module and every test that imports it, runs them, and prints only failures and the summary. Add lint of the touched files.
- The full suite runs once, at the end of a delivery, compared with the recorded baseline of failures. A failure unrelated to what you touched waits for the end.
- Redirect test output to a file and read only the failures and the summary.
- The full gate sets its own environment (no network, no database for the unit tier); never rely on your shell's variables to make it offline. See `docs/trd/testing.md`.

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

- `<src>/app/`: entry, route assembly and dependency wiring
- `<src>/features/<f>/`: one folder per product feature. Each has a `CLAUDE.md` map (up to 20 lines), a public entry, `domain/` (pure rules, no IO), services with IO, and `tests/`
- `<src>/infra/`: shared code (persistence, providers, observability, config, auth)
- `tests/integration/`, `tests/eval/`, and unit tests beside the code in `<src>/features/<f>/tests/`
- `changes/NNN-<slug>/`: one folder per change in flight (`brief.md` for size M and L, `design.md` for size L, `plan.md`). Holds intent, plan and state, never truth
- `changes/archive/`: finished changes, moved there with `git mv` when promoted. History only, never read for current behavior
- `docs/prd/`, `docs/trd/`, `docs/adr/`, `docs/code-structure.md`, `docs/flow.md`

## Workflow

Living truth plus change folders, in this order. Do not skip steps.

1. `/prd-gate` classifies the request; a rule change updates PRD and TRD and produces the plan
2. The change folder by size, decided at classification: **S** no folder or only `plan.md`; **M** `brief.md` and `plan.md`; **L** `brief.md`, `design.md` and `plan.md`. The plan header carries a `## Constitution check`
3. Implementation test first, one task per agent, one commit per task
4. Gates before merge: lint, type check, full suite green, coverage not decreasing, ratchet green
5. Promote: what is durable goes to its living home (PRD, TRD, ADR, schema or contract) and the folder is archived with `git mv changes/NNN-<slug> changes/archive/NNN-<slug>`

## Finding things

Load only what the task needs. Every step below is one Glob, Grep or ranged Read.

1. **Product rules.** `docs/prd/INDEX.md` lists every PRD file (one per section) with the rule IDs it defines. `Grep "<ID>" docs/prd` finds a rule; the same ID in a test docstring finds its tests. A human-reading HTML, if any, is never read for work.
2. **Where it lives in the code.** `docs/trd/README.md` lists the feature maps. `docs/trd/<feature>.md` gives the files, the entry points by symbol name, the tests and what must not break.
3. **Repo rules by kind of change** are in `docs/trd/invariants.md`; **how to test** is in `docs/trd/testing.md`.
4. **Big files** (listed in `.claude/skills/prd-gate/repo.md`): Grep for the symbol, then Read that range. Never read them whole.
5. **History of an area:** `git log --oneline -- <paths from its TRD file>`.

Keeping it true:

- A code change that moves a file, an entry point or a test of a feature updates `docs/trd/<feature>.md` and the feature's `CLAUDE.md` in the same commit. Names only, never line numbers or default values.
- A change to product behavior updates the PRD file that owns the rule ID and moves the superseded wording to `docs/prd/CHANGELOG.md`: the PRD body holds only what is valid today.
- The `prd-gate` skill runs this flow and checks it with `.claude/skills/prd-gate/scripts/gate.py`.

## Handing work to a subagent

Paste the rule rows it must implement (its contract) and point to files for everything else: the PRD file, the TRD feature file, the files it owns and the commands to run. Never paste whole documents. It returns at most 20 lines (Done, Files, Tests, Gaps), writes longer output to files, never opens another subagent, and stops at about 50 tool calls or 30 minutes to report.
