<!-- ai-kit:start (managed by ai-starter-kit install; edit the kit, not this block) -->
## Working with subagents
- A subagent prompt carries the contract (the rule rows or IDs it must satisfy) and file paths; never whole documents pasted in.
- A subagent writes its work to files and returns at most 20 lines: Done / Files / Tests / Gaps. The main thread does not reread what it wrote.
- A subagent never opens another subagent. Parallelism only from the main thread, in waves with disjoint file ownership.
- Ceiling per agent: about 50 tool calls or 30 minutes, then report what is done and what is left. An agent that hit its ceiling or passed about 150k tokens is replaced by a new one with a handoff of at most 10 lines.
- Model: sonnet by default; opus only with a written reason.
- Review: at most 5 rounds per delivery; from round 2, only the previous findings against the fix diff. An open Critical at round 5, or a round worse than the previous one: stop and ask me. Say `review: N/5` every round.
- Brake: an agent that hits its ceiling twice, or a wave twice as slow as the previous one, stops and reports cost and what is left.

## Tests
- While working, run only the related tests: the mirror test of the touched module and the tests that import or use it. The full suite runs once, at the end of a delivery, compared against a recorded baseline of failures.
- Test output goes to a file; only failures and the summary come back into context.
- Write the failing test first.

## Docker and disk
- Build an image only when a test must prove services start together; otherwise a throwaway database container or in-process fakes. Ask whether a cheaper test exists before building.
- When the repository has `scripts/gates.sh`, build and run integration only through it (`build`, `integration`, `full`): it guards disk and image caps and cleans up on every exit.
- A one-off container is `--rm`; an image pulled only for it is removed in the same step. Remove spike images when the spike ends.
- Never start a background command with unbounded output; long runs go to a file, in the background, with a timeout longer than the run, so they are not killed mid-stack.
- Before ending a session that used Docker, leave nothing of yours running or dangling. Delete only what is clearly yours; other projects' images and volumes are listed for me, never removed.

## Editing
- Move code by script (line ranges or AST), never retype a function body.
- Edit markdown and HTML with Write and Edit directly, never through ad hoc scripts.
- Count and list with the Grep tool rather than the shell.
- No push and no pull request without my explicit request.
<!-- ai-kit:end -->
