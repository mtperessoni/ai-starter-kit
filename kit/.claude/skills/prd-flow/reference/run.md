# Run (every agent, executor, reviewer, recheck)

"Every agent" is read by all five roles; the rest by the executor, the reviewer and the recheck. The chief never reads this page: its side of the loop is `SKILL.md`. Commands come from `repo.md` "Commands". Paths and IDs in examples are illustrative.

## Every agent
| Rule | Detail |
|---|---|
| No user | Never talk to the user: a question leaves prepared in `Route: user:` |
| Reads | Independent reads in one message. Rows by ID (`Grep -n`, then `Read` with offset and limit); big files of `repo.md` by symbol only; never the HTML, a whole `state.md`, `CHANGELOG.md`, `changes/archive/` or a legacy `specs/` |
| Writes | Only the files your role names, with Edit and Write: no heredoc, `sed -i`, `tee` or bare `python -`. Prose in `repo.md` `language`, IDs and code in English. No em dash (U+2014), no needless comment |
| Interpreter | The prompt's `Python:`, else the output of `scripts/gates.sh python`; never another |
| Shared tree | Never `git stash`, `reset`, `checkout`, `switch`, `restore`, amend or a repo-wide `gates.sh fix`: fix the cause |
| Commands | One command per call, never an edit, a test and a commit chained with `&&`. Foreground only, never `run_in_background`: a command that may pass 120 s gets an explicit `timeout` under 600000 and writes its output to a file; read only failures and the summary. Never `tail -f`, `until`, `while`, `sleep` or `seq` polling; never return while a process you started is alive. Never start or wait for a baseline, a suite or a verify: only the chief does |
| Commit | Write the message with Write to `<state>/msg-<task or role>.txt`: Conventional Commits, English; a rule change's body is the record (`Decided: <n><x> ... (rejected: ...)` lines, executor "Rule rows with the code"), ending with `Rules: <IDs>`. The project's commit rules in its `CLAUDE.md` or `AGENTS.md` win over a harness attribution reminder. Then `git add <your paths>` and `git commit -F <that file>` as separate calls (never `-F -`); `git status --porcelain -- <your paths>` must be empty. Never add anything under `.claude/prd-flow/`. On `index.lock` wait a few seconds and retry once |
| Loops | At most 2 reruns of a failing step; the third returns `blocked` with the lines and a Route |
| Subagents | Never open one: parallelism is the chief's |
| Ceiling | V08 |

One return format for every agent: at most 15 lines (done, tests, gaps, minutes used) and under 2,000 characters, then the five fields and nothing after.
```
Status: done | gap | blocked
Files: <paths written, or none>
Commit: <short hashes, or none>
Route: none | user: <one question with options> | <role> <mode>: <handoff of at most 10 lines>
Next: <the step the chief runs next; one per option of a user route>
```

## Task
1. Batch 1, one message: the task line of the prompt (size L: `Grep -n "^### <ID>"` in `Plan:`, then `Read` that range); the Contract rows from the PRD by ID; the paths it lists to read (about 25k tokens); for a rule change the sheet and `Answers:` of the prompt (and size L: the task's `DEC-` rows, `Grep -n` in `changes/NNN-<slug>/decisions.md`; a DEC row binds like a rule); `git log -5 --oneline -- <owned paths>`.
2. Test first, from the rule's Example: write the failing test, run it with the runner of `repo.md` "Commands" (`scripts/gates.sh one <test>`) and see it fail; implement the minimum; run it again until it passes. Then `scripts/gates.sh fix-files <your files>` and `lint-files <your files>`. Nothing else: related tests, suites and gates run once in the chief's wave verification.
3. Structure: `docs/code-structure.md` limits; the ratchet never regresses. A rule change: the approved rows into the PRD file you own and, when you own `docs/trd/<area>.md`, the TRD body (`write.md` "Rows", "TRD"), in this same commit. C6: move code with `scripts/gates.sh move <source> <start> <end> <destination> [--at LINE]`, never retyped; split huge test files first and prove statically (imports, types, lint).
4. Outside your owned paths: a test that broke as a direct, expected consequence may get only its expectation adjusted (never a loosened safety assertion) and joins the commit. What the task says to leave stays as it is.
5. Commit with the message you wrote.

`Interrupted: yes` in the prompt (a replacement for a stuck or timed-out agent): first derive the touched files from `git status --porcelain -- <owned paths>`, save `git --no-pager diff -- <those files>` to `<state>/interrupted-<task>.patch`, then continue from it.

## Fix
The chief sends each task's finding lines (those with that `Task:`) to that task's warm executor with SendMessage; lines with `Task: none`, the wave verify failure lines, and lines whose executor is past its ceiling or 150k tokens go together to one new executor `fix` with a handoff (`write.md` "Fix handoff"). Fix only what is named, inside its owned paths, under the Task steps (test first for a behavior finding). Commit `fix(<scope>): <sentence>`. A row without a `Source`: `Grep` the rule ID in the source folders and write the path and symbol into the row.

## Close
0. Rerun: `state.md` logs `closed: <commit>`, or the state folder is gone after a pass: return `done` with that commit, run nothing.
1. Size S and M: no step here, the rows and the TRD already landed with the code. Size L only: `<python> .claude/skills/prd-flow/scripts/promote.py <slug>` archives the change folder; commit what it changed as `docs(prd): archive <slug>`; a WARN line is routed before step 2.
2. `scripts/gates.sh close <slug> --case <C>`, stdout read directly (or to a file under `.ai-kit/runs/`, never the state folder). Order: lint, docs, the chief's compare result (never the suite inline), cleanup; `--case C4` skips baseline and compare. "compare is still running" or "no compare result" is the chief's to act on (DP07), never a fix. Never rerun it to recover output. The return carries the close summary and, when `docs/prd/` or `docs/trd/` changed, "`/docs-html` refreshes the reading pages".

## Short C5 in the middle of execution
1. An agent meeting behavior no approved rule covers (V06) stops its task and returns `Route: surveyor short`. Running tasks finish.
2. Surveyor `short` sweeps the touched rules, writes `<state>/sheet-short-<k>.md` (k = 1, 2, ...) with only those rows and says per task of `plan.md` `stands` or `redo: <why>`.
3. The chief prints that sheet and ends the turn; the reply is the approval (no diff approval follows) and goes to the executors of the `redo` and new tasks with `Sheet:` and `Answers:` (they write the rows with their code); with a size L plan also to docs `adjust` (a `Reply` line and DEC rows in `decisions.md`, new and `redo` tasks, the wave table refreshed). Outside a C5 over several tasks, docs `plan` creates the plan.
4. Execution resumes from the returned table. The review counter never resets without explicit approval.

## Review
| Moment | Who | Over what |
|---|---|---|
| Once per delivery after the last wave (`Wave: last`); also after a wave the plan's `Review:` line names because a later wave builds on its interface; the single task of C2, C3, C6 | reviewer, one round; the risk lenses of the tasks in the same message | the combined diff of the passed commits of every repository of the delivery, the tasks' rule IDs, `Decisions:` and `Lens:`, the plan's item map row by row, and every message, field and enum that crosses a repository boundary, from both sides |
| After a Critical or High fix, and the fix of round 5 | the warm reviewer resumed in `recheck`, else `prd-flow-recheck` | only the fix diff and the previous finding IDs |

Reviewer: read the diff (`git rev-list --no-walk --topo-order <hashes>`, `git --no-pager diff <oldest>^..<newest>`), the Contract rows from the PRD, the DEC rows of the tasks, and only the lines of `docs/trd/invariants.md` and `docs/code-structure.md` the diff touches. A `Lens:` adds the rubric of that agent in `.claude/agents/`; `Lens: none` never means no review. A finding is one line: `[Critical|High|Medium|Low] CS-NNN · file:line · rule or DEC ID · scenario · fix · Owns: <file and its test> · Task: <ID>`; `Task:` is the task whose owned paths hold the file, `none` when no task owns it. Severity by consequence; "possible in theory" without a scenario is Low. Behavior outside the approved rules is `R09` (an open question turned into an exemption is one); a diff against a DEC row is a finding cited by its ID; a changed item the task said to leave is a High `R09`, its unchanged state never a finding.

Recheck: per previous finding `resolved` or `open` with the file and line that shows it; a new finding only when the fix diff created it.

| ID | Rule |
|---|---|
| V01 | A round is counted when Critical or High findings go to a fix; a review with only Medium and Low, or none, costs no round |
| V02 | At most 5 rounds per delivery; the chief's side is `SKILL.md` "Review" |
| V03 | A second round is scoped: the previous findings against the fix diff, and new problems only that diff created |
| V04 | Critical is fixed; High is fixed when it fits the approved rules, else `Route: user`; Medium and Low ride in the same batched fix and are never re-reviewed; alone they stay pending, `Route: none`. Recheck only after a Critical or High fix |
| V05 | Cascade: more Critical plus High than the previous round stops the chief (`SKILL.md` "Review") |
| V06 | Any behavior change during execution (a case no rule covers, a new rule, and always the safety posture: removing a guard, a net, a list, a switch) is the short C5 above, never one more task |
| V07 | Round 5 with an open Critical, or a cascade: the chief stops and asks (`SKILL.md` "Review"); never a round 6 without an explicit yes. Each open Critical is told in plain words (what happens to the user), with the options: one more round, accept with a mitigation, change the rule |
| V08 | Ceilings, the single home of these numbers: surveyor `full` and docs `plan` about 80 tool calls; every other surveyor, docs, executor and fix about 50 calls or 30 minutes; reviewer 40; recheck about 15. At the ceiling or past about 150k tokens: return `gap` with a handoff of at most 10 lines (files touched, failing tests, next step) |
| V09 | The full suite runs once, as the chief's `compare` during the last review (restarted after the last fix); the reviewer runs nothing; an executor runs only its own test plus fix-files and lint-files |
| V10 | The reviewer returns at most 8 finding lines, the most severe first, in one batched list; `<state>/findings-r<N>.md` only past the line cap, named in `Files:` |
