# Arm rule-as-data-v3: v2 plus the cost rules

Everything in `rule-as-data-v2.md` (V01 to V09) holds; read it first. v3 adds the rules below, which cut context and turns without removing any check. Run by the dedicated `docs-eval-executor` agent, not `general-purpose`.

| ID | Rule |
|---|---|
| X01 | Plan before the first edit: from `pack.md` and the sheet, list the files you will touch and what changes in each, in at most 10 lines of your own notes. Then read only those files, by range |
| X02 | Every shell output is bounded: `git status --short`, `git diff --stat`, never a full diff or a recursive listing; pipe long outputs to `| tail -40` or to a file and Grep it. Never `cat` a file: use Read with a range |
| X03 | One write per file when you can: a new file is one Write; several changes in one existing file go in as few Edits as their distance allows. Never send more than 8 Edits in one message |
| X04 | Tests run as `node ./node_modules/vitest/vitest.mjs run --project unit --coverage.enabled=false <files> 2>&1 | tail -25` (the gate wrapper adds about 10 s per call). Lint and types once, at the end, on your files only |
| X05 | The decision text comes from the sheet; never reread the sheet or `pack.md` once your notes hold what you need |
| X06 | Ceiling: 60 tool calls. Return at most 10 lines: Status, Commit, Files (count by kind), Tests, Gate, Gaps |
