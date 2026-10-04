# Rule catalog

Every rule of the kit, by domain. Each file is one table: `| ID | Rule | Why | Lands in |`. "Lands in" names the file of the target repository (or the skill section) that enforces the rule after the bootstrap, so the catalog doubles as the checklist that nothing was lost.

Read only the file of the domain you need. IDs are stable: a new rule takes the next free number of its prefix.

| File | Prefix | Domain |
|---|---|---|
| [01-context-economy.md](01-context-economy.md) | CE | Token efficiency, lazy loading, budgets |
| [02-subagents.md](02-subagents.md) | SA | Orchestrator and workers, contracts, file-based handoff, caps, models, waves |
| [03-review.md](03-review.md) | RV | Code review with a ceiling of rounds |
| [04-testing.md](04-testing.md) | TS | Test-first, related tests only, full suite once, baseline, offline gates |
| [05-code-structure.md](05-code-structure.md) | AR, CX | AI-readable code layout, size limits, the ratchet, code constraints |
| [06-docs-system.md](06-docs-system.md) | DS | PRD by section, rule rows, CHANGELOG, TRD by feature, invariants, gate |
| [07-workflow.md](07-workflow.md) | WF | Cases C0 to C6, PRD then TRD then plan then code, interview, commits |
| [08-writing-style.md](08-writing-style.md) | WS | Language, punctuation, comments, commits, tables |
| [09-lessons.md](09-lessons.md) | LS | What was measured and why each rule exists |

## Where the rules end up

| Target file | Holds |
|---|---|
| `~/.claude/CLAUDE.md` | The global block: SA, RV, TS and WS rules that hold in any repository ([template](../templates/global-CLAUDE.md)) |
| `CLAUDE.md` | Constitution index, the gate rule (WF01), code structure summary |
| `AGENTS.md` | Commands, critical constraints (CX), directory map, finding things (CE), handing work to a subagent (SA04) |
| `.specify/memory/constitution.md` | Binding principles, domain specific plus the process principles of the kit |
| `docs/code-structure.md` | AR01 to AR14 |
| `docs/prd/`, `docs/trd/` | DS rules applied |
| `.claude/skills/prd-gate/` | WF, SA, RV, TS rules as operating procedure, plus `repo.md` |
| `tests/test_architecture.py` or `scripts/ratchet.mjs` | AR rules marked "ratchet" |
