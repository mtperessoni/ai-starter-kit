# Arm B contract: rule as data, one commit

You implement one approved rule change end to end. The PRD is the single source of the rules; nothing else mirrors it.

| ID | Rule |
|---|---|
| B01 | One commit holds everything: the PRD rule rows, the code and the tests. Nothing in docs is written before the code |
| B02 | The approved rows are in the sheet answers and in `pack.md`. Write them into the PRD file that owns the rule ID, exactly as approved; a new rule gets the next free ID of its prefix |
| B03 | A value a rule changes (a number, a message) may be restated in narrative sections of the same PRD (summary, glossary, journey, diagram). Find every copy with one Grep of the old value in `docs/prd` and fix it in the same commit |
| B04 | No CHANGELOG line, no INDEX edit (only when a new PRD file is created), no HTML, no `decisions.md`, no `plan.md`, no `state.md`, no `Planned` or `pending code` markers, no promote |
| B05 | TRD: edit `docs/trd/<area>.md` only when a file, folder or entry symbol it names moved, was renamed or is new. A changed value is not a TRD change |
| B06 | Test first: write or change the test that cites the rule ID in its `describe` title or header, see it fail, then the code |
| B07 | Checks, once each at the end: your tests with `bash scripts/gates.sh one <test files>`, `bash scripts/gates.sh lint-files <files>`, and `python <gate_lite.py> --repo <worktree> --base <base>`. Fix and rerun only what failed |
| B08 | Commit with a Conventional Commit message ending in `Rules: <IDs>` |
| B09 | Read by Grep and ranges; never read a whole PRD, TRD or CHANGELOG |
