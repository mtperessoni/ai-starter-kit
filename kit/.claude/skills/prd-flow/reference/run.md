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
| Commands | One command per call, never an edit, a test and a commit chained with `&&`. Foreground only, never `run_in_background`: a command that may pass 120 s gets an explicit `timeout` under 600000 and writes its output to a file; read only failures and the summary. Never `tail -f`, `until`, `while`, `sleep` or `seq` polling; never return while a process you started is alive. Never start or wait for a baseline, a suite or a watch: only the chief does |
| Commit | Write the message with Write to `<state>/msg-<task or role>.txt`: Conventional Commits, English, the IDs cited, last line `Rules: <IDs>` or `Case: none (<reason in at most 8 words>)` when source folders are touched; the project's commit rules in its `CLAUDE.md` or `AGENTS.md` win over a harness attribution reminder. Then `git add <your paths>` and `git commit -F <that file>` as separate calls (never `-F -`); `git status --porcelain -- <your paths>` must be empty. Never add anything under `.claude/prd-flow/`. On `index.lock` wait a few seconds and retry once |
| Loops | At most 2 reruns of a failing step; the third returns `blocked` with the lines and a Route |
| Subagents | Never open one: parallelism is the chief's |
| Ceiling | V08 |

Return: at most 15 lines and under 2,000 characters, then the five fields and nothing after.
```
Status: done | gap | blocked
Files: <paths written, or none>
Commit: <short hashes, or none>
Route: none | user: <one question with options> | <role> <mode>: <handoff of at most 10 lines>
Next: <the step the chief runs next; one per option of a user route>
```

## Task
1. Batch 1, one message: the card (`Grep -n "^### <ID>"` in the plan named by `Plan:` in `## Plan` of `state.md`, then `Read` that range; or `<state>/card.md`); the Contract rows from the PRD by ID; `<state>/deliveries/<ID>.md` of each `Depends on`; the `Read:` list (about 25k tokens); the card's `DEC-` rows (`Grep -n` in `changes/NNN-<slug>/decisions.md`; a DEC row binds like a rule); `git log -5 --oneline -- <Owns>`. `Why:` carries the intent: never read whole PRD sections for it.
2. Test first, from the rule's Example: `scripts/gates.sh red <test>` (record `Red: <exit code>`); implement the minimum; `scripts/gates.sh one <test>` passes. Then `scripts/gates.sh fix-files <your files>` and `lint-files <your files>`. Nothing else: related tests, suites and gates run once in the chief's wave verification.
3. Structure: `docs/code-structure.md` limits; the PRD IDs in the first comment of each module and test; the area map follows; the ratchet never regresses. Owns lists `docs/trd/<area>.md`: update its body (`write.md` "TRD"). C6: move code with `scripts/gates.sh move <src> <start>-<end> <dst> [<line>]`, never retyped; split huge test files first and prove statically (imports, types, lint).
4. Outside Owns: a test that broke as a direct, expected consequence may get only its expectation adjusted (never a loosened safety assertion) and joins the commit. Each `Leave:` item stays as it is.
5. Write `deliveries/<ID>.md`, then commit with the card's message.

`Interrupted: yes` in the prompt (a replacement for a stuck or timed-out agent): first derive the touched files from `git status --porcelain -- <card Owns>`, save `git --no-pager diff -- <those files>` to `<state>/interrupted-<task>.patch`, then continue from it. The task ID comes from the prompt (the chief's ledger).

## Deliveries
`<state>/deliveries/<task>.md`, one per task (never a shared file), at most 16 lines. A dependent task reads it instead of the code; promote reads `Source:`; the reviewer reads `Self-check:` first.
```markdown
## T07 · <result in one line>
Red: 1 (test_call_provider_reads_timeout)
Creates: PaymentOutcome.retry_after
Changes: call_provider(..., timeout=) now reads PaymentConfig
Source: CHK-02: src/features/checkout/payment_call.py::call_provider
Self-check:
- wired: yes, `Reached from:` (POST /checkout) reaches the new symbol
```
One `Source: <ID>: <path::symbol>` line per approved rule of the Contract whose Change via is `code` (rewritten rules included), one ID per line. Rules via config, env, prompt, data or a handoff get none: they stay planned and close by their own route. Self-check keeps only the lines the card's `Lens:` or rules ask for, each `yes`, `no` or `n/a` with evidence; a `no` is fixed before the commit or routed; never a claim that gates ran.

## Fix
The chief sends each task's finding lines (those with that `Task:`) to that task's warm executor with SendMessage; lines with `Task: none`, or whose executor is past its ceiling or 150k tokens, go together to one new executor `fix` with a fix card (`write.md` "Fix card"). Fix only what is named, inside its Owns, under the Task steps (test first for a behavior finding). Commit `fix(<scope>): <sentence>` with the trailer. A missing `Source:` line: `Grep` the rule ID in the source folders, append the line to the implementing task's delivery, no commit.

## Close
0. Rerun: `## Chief` logs `closed: <commit>`, or the state folder is gone after a pass: return `done` with that commit, run nothing.
1. C5 only: `<python> .claude/skills/prd-flow/scripts/promote.py <slug>` (`write.md` "Promotion"). On success commit what it changed in `docs` and `changes` as `docs(prd): promote <slug>`; the tree is clean there before step 3. A WARN line is routed before step 3.
2. Write `## Close` of `state.md` (the promote result) now: a passing close deletes the state folder.
3. `scripts/gates.sh close <slug>`, stdout read directly (or to a file under `.ai-kit/runs/`, never the state folder). Order: lint, trailers, docs, the chief's compare result (never the suite inline), `gate.py --final`, retro, cleanup. Never rerun it to recover output. The return carries the close summary and at most 5 retro findings, or "every threshold held", and "`/docs-html` refreshes the reading pages" when `docs/prd/` or `docs/trd/` changed.

## Short C5 in the middle of execution
1. An agent meeting behavior no approved rule covers (V06) stops its task and returns `Route: surveyor short`. Running tasks finish.
2. Surveyor `short` sweeps the touched rules, writes a sheet of only those rows and says per task of `## Plan` `stands` or `redo: <why>`.
3. The chief prints the sheet; the reply goes to docs `short <YYYY-MM-DD>`: PRD rows, the CHANGELOG entry's `IDs:` extended, a `Reply` line and DEC rows in `decisions.md`, new and `redo` cards, the wave table refreshed. Outside a C5 it creates the change folder and `plan.md`.
4. Execution resumes from the returned table. The review counter never resets without explicit approval.

## Review
| Moment | Who | Over what |
|---|---|---|
| Each wave of a plan with a parallel wave; the single task of C2, C3, C6; a serial plan once after the last wave (`Wave: last`) | reviewer, one round | the combined diff of the passed commits, the cards' rule IDs, `Decisions:`, `Leave:` and `Lens:` |
| After a Critical or High fix, and the fix of round 5 | the warm reviewer resumed in `recheck`, else `prd-flow-recheck` | only the fix diff and the previous finding IDs |

Reviewer: read the verification output the chief names and each delivery's `Self-check:` and `Red:` first; report only what they miss or state wrongly. Then the diff (`git rev-list --no-walk --topo-order <hashes>`, `git --no-pager diff <oldest>^..<newest>`), the Contract rows from the PRD, the cards' DEC rows, and only the lines of `docs/trd/invariants.md` and `docs/code-structure.md` the diff touches. A `Lens:` adds the rubric of that agent in `.claude/agents/`; `Lens: none` never means no review. A finding is one line: `[Critical|High|Medium|Low] CS-NNN · file:line · rule or DEC ID · scenario · fix · Owns: <file and its test> · Task: <ID>`; `Task:` is the card whose Owns hold the file, `none` when no card owns it. Severity by consequence; "possible in theory" without a scenario is Low. Behavior outside the approved rules is `R09` (an open question turned into an exemption is one); a diff against a DEC row is a finding cited by its ID; a changed `Leave:` item is a High `R09`, its unchanged state never a finding.

The wave verify failure lines that map to a card are copied, with their `Task:`, into the same `Route: executor fix` as the findings.

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
| V08 | Ceilings, the single home of these numbers: surveyor `full` and docs `apply` about 80 tool calls; every other surveyor, docs, executor and fix about 50 calls or 30 minutes; reviewer 40; recheck about 15. At the ceiling or past about 150k tokens: return `gap` with a handoff of at most 10 lines (files touched, red tests, next step) |
| V09 | The full suite runs once, as the chief's `compare` during the last review; the reviewer runs nothing; an executor runs only its own test plus fix-files and lint-files. No cost line by hand: the telemetry records every agent and `gates.sh retro` (inside close) reports it |
| V10 | The reviewer returns at most 8 finding lines, the most severe first, in one batched list; `<state>/findings-r<N>.md` only past the line cap, named in `Files:` |
