# Arm rule-as-data-v2: one commit, with the decision record (v1 plus P1 to P5)

You implement one approved rule change end to end. The PRD is the single source of the rules; the commit is the record of why it changed.

| ID | Rule |
|---|---|
| V01 | One commit holds everything: the PRD rule rows, the code, the tests and the generated INDEX. Nothing in docs is written before the code |
| V02 | The approved rows are in the sheet (`sheet.md`, "Becomes") and the scope in `pack.md`. Write the rows into the PRD file that owns the rule ID, exactly as approved; a new rule gets the next free ID of its prefix. A row holds today's rule only: no "today:", "was", "pending" or "planned" wording |
| V03 | A value a rule changes may be restated in narrative sections (summary, glossary, journey, diagram) and in the TRD. Find every copy with one Grep of the old value over all of `docs/` (CHANGELOG and `changes/archive` excluded) and fix it in the same commit. The TRD names files and symbols; when it restates a rule value, replace the value with the rule ID |
| V04 | No CHANGELOG line, no hand edit of INDEX, no HTML, no `decisions.md`, no `plan.md`, no `state.md`, no promote. Run `python <scripts>/gen_index.py --repo <worktree>` before the commit: it rewrites the INDEX IDs column |
| V05 | TRD: also add a row when a new file or entry symbol carries a rule (a new hook, a new module) |
| V06 | Test first. Write or change the test that cites the rule ID in its `describe` or `it` title, run it, see it fail, then write the code. Logic that implements a rule in a hook or component gets its own `.test.ts` beside it (pure function or `renderHook`); a `.test.tsx` is not collected |
| V07 | Checks, once each at the end: your tests (`bash scripts/gates.sh one <test files>`), `bash scripts/gates.sh lint-files <files>`, `bash scripts/gates.sh imports`, and the gate `python <scripts>/gate_lite.py --repo <worktree> --base <base>`. Fix and rerun only what failed |
| V08 | Commit message: a Conventional Commit subject, then this body, then the trailer: |

```
Request: <the request in the user's words, from the sheet title or the prompt>
Decided: <n><letter> <the chosen option in one line> (rejected: <the other option in one line>)
Assumed: <each assumption that shaped the code, in words, one per line; never an ID alone (the sheet is not committed)>
Red: <test file> failed before the code (<n> failing)

Rules: <IDs>
```

One `Decided:` line per sheet decision; `Decided: none` when the sheet had none.

| ID | Rule |
|---|---|
| V09 | Read by Grep and ranges; never read a whole PRD, TRD or CHANGELOG |
