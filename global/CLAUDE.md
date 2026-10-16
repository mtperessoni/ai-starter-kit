<!-- ai-kit:start (managed by ai-starter-kit install; edit the kit, not this block) -->
Rules that say "my yes", "report to me" or "ask me" bind the main thread. A subagent never waits for me: it follows its prompt and returns anything that needs my decision as a gap.

## Scope and slicing
- Before the first dispatch or the first edit of a delivery, state the goal, what is out of scope and an estimate in minutes, and get my yes.
- A delivery is one vertical slice: one area or one engine, about 30 changed files or 2 hours, its own PR. Bigger work is cut into slices before any code. When I widen the scope mid-session, answer first with the estimate and the slices, then do what I choose.
- Defects first, structure later: when an audit or a review finds defects, each one ships first as the smallest fix in the current structure, with its test and its PR. A restructuring is a separate delivery, in slices.
- Size L (new data model, contract or integration) writes one short plan in `changes/NNN-<slug>/` (about 100 lines: decisions, slices, acceptance items). Size S and M write no plan files.
- Size L gets a design review before the plan: one reviewer checks every field or frame that crosses a repository boundary, from both sides; the safety nets the change touches; personal data in any new storage, log or prompt; and the rollout path. Its findings change the design, never the code.
- One code path: a flag decides at the edge (creation or entry point). Keeping the old and the new path alive inside modules needs a written rollback reason.

## Executing
- The session that executes a slice writes the code itself. A subagent only for: the final review, a slice that is truly independent (its own worktree, at most 2 executors at once), or heavy reading kept out of the main context.
- A subagent prompt carries the goal, the acceptance items, the done condition (which tests pass) and at most about 5 paths to read first, never whole documents. At the done condition the agent stops verifying and hands back. It returns at most 15 lines: done, files, tests, gaps.
- Subagents run on sonnet by default (`CLAUDE_CODE_SUBAGENT_MODEL` in the kit settings); dispatch with `model: opus` only with a one-line reason.
- Cadence: keep a running total of minutes against the estimate, from the duration the harness reports when each agent finishes. At the end of each slice, and on reaching 1.5 times the estimate, stop and report to me what is done and what is left. Never open a lane for leftovers without my yes. A long or stopped agent is continued with SendMessage, never replaced by a new one: the harness compacts its context.
- One phase per session for size L: design, then docs, then one session per slice. Checkpoint to a fresh session past about 150k tokens of context.
- Long commands write their output to a file. No polling loops: the harness notifies when background work ends.
- In a shared tree never `git stash`, `reset`, `checkout`, `restore` or `commit --amend`. Commit messages go through a file (`git commit -F <file>`).
- Never hand back with a process you started still running (stop it with TaskStop). Never kill processes by image name (`taskkill /IM`, `pkill`, `killall`); use `scripts/gates.sh reap` where it exists, otherwise stop your own process by its PID.

## Tests
- Write the failing test first. Unit tests run offline, with fakes and a per-test timeout.
- Before handing back a slice, run its tests and the tests that import the files it touched (`scripts/gates.sh related`). The full suite runs once per delivery, in the background, against a recorded baseline of failures.
- Never loosen a safety assertion or regenerate a snapshot to get green. A failing test unrelated to the change is reported, not investigated. A test that fails the same way twice in a row is reported as a gap, not retried a third time.
- Test output goes to a file; only failures and the summary come back into context.
- A token-saving proxy such as `rtk` rewrites shell output: run test runners, linters and any command whose output feeds another command (`$(...)`, a file list) through `rtk proxy <cmd>`. When an output looks cut, summarized or wrong, rerun it once with `rtk proxy` or use the Grep and Read tools; never retry the same command.

## Docs and review
- A rule change is shown as today versus proposed and confirmed before the code. The commit that implements it updates the PRD row; its body says what was decided. Git is the history.
- The TRD and the area maps name files and entry points only, and are updated once per delivery, in its last slice.
- One review per delivery, over the combined diff of every repository: the acceptance items one by one, every field that crosses a repository boundary from both sides, PRD rows and TRD names. Risk reviewers (clinical, security) go in the same message.
- Critical and High findings are fixed and rechecked against the fix diff only; Medium and Low ride along. At most 5 rounds; a round worse than the previous one, or an open Critical at round 5, stops and asks me. Say `review: N/5` every round.
- Safety nets (guardrails, alarms, rollback switches, tenant configuration) change only with my explicit yes, never inside a task, a fix or a test edit.

## Docker and disk
- Build an image only when a test must prove services start together; otherwise a throwaway database container or in-process fakes.
- When the repository has `scripts/gates.sh`, build and run integration only through it (`build`, `integration`, `full`): it guards disk and image caps and cleans up on every exit.
- A one-off container is `--rm`; an image pulled only for it is removed in the same step. Never start a background command with unbounded output.
- Before ending a session that used Docker, leave nothing of yours running or dangling. Other projects' images and volumes are listed for me, never removed.

## Editing
- Read a file with the Read tool (a line range is enough) before editing it. A shell read (`cat`, `sed -n`, `grep`) does not count and the edit is refused; use the shell only for files you will not edit.
- Independent reads and searches go in one message. Make every change a file needs in one pass, and Write the whole file after a full Read when most of it changes.
- Move code by script (line ranges or AST), never retype a function body.
- Edit markdown and HTML with Write and Edit directly, never through ad hoc scripts.
- No push and no pull request without my explicit request.
<!-- ai-kit:end -->
