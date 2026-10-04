# Subagents (SA)

The main thread is the orchestrator: it classifies, confronts, interviews, approves, dispatches and commits. Workers do the heavy reading and writing, communicate only through files in a state folder, and return a short fixed-format report. The weight of an agent is the context it resends on every call, times the number of calls.

## Roles and contracts

| ID | Rule | Why | Lands in |
|---|---|---|---|
| SA01 | The orchestrator classifies, confronts, interviews, approves, dispatches and commits. It does not do the heavy reading or writing | Its context is the one that lives longest | skill SKILL.md "C5 route" |
| SA02 | A worker never talks to the user. Anything missing comes back as a gap in the return, never as an assumption | Assumed rules become wrong code that a review later has to find | workers.md header; R04 |
| SA03 | A worker prompt is one line: read section `<name>` of `workers.md` and run it for slug `<slug>`, plus a one-line request. Never paste briefings into the prompt | The briefing is a file the worker reads once; pasting it multiplies tokens | skill SKILL.md "Workers" |
| SA04 | Handing work to a subagent: paste only the rule rows it must implement (its contract) and point to files for everything else: PRD file, TRD file, files it owns, commands to run. Never paste whole documents | The contract is small and exact; the rest is reachable by path | AGENTS.md "Handing work to a subagent"; global block |
| SA05 | Workers write their output to `.claude/prd-gate/state/<slug>/` (outside git). The orchestrator reads only the return | Files are the handoff medium; the orchestrator's context stays small | workers.md; CE19 |
| SA06 | Every return has the same shape: `Done:` one line, `Files:` paths written, the requested content, `Gaps:` list or "none". At most 30 lines; executor and reviewer at most 20 | Predictable, cheap to read, gaps impossible to hide | workers.md "Return format" |
| SA07 | Delivery ledger: each executor appends at most 8 lines to `deliveries.md` (`Creates`, `Changes`, `Leaves for`). A dependent task reads those blocks instead of the code | The next task learns the interface without reading the implementation | workers.md "executor"; agent-plan.md "Creates / consumes" |
| SA08 | A gap in a return is resolved (question to the user, or a new task) before any task that depends on it starts | A gap carried forward becomes a wrong implementation | execution.md E05 |
| SA09 | The interview runs in the main thread. Workers prepare the pre-interview; they never ask | Only the main thread can talk to the user | R04 |
| SA10 | Without the Agent tool, run the worker section in the main thread with the same briefing and budget | The procedure must not depend on the tool being present | skill SKILL.md |
| SA11 | Workers edit docs with Write and Edit only; no Python or shell script writes markdown or HTML. Running the checker script is fine | Script-written docs were slower and error prone | WS07; workers.md header |

## Parallelism, models and ceilings

| ID | Rule | Why | Lands in |
|---|---|---|---|
| SA12 | No worker opens a subagent. Parallelism belongs to the main thread, by waves | Nested agents multiply context and hide cost | execution.md E12 |
| SA13 | A wave runs tasks with disjoint `Owns` in parallel; tasks touching a big file form a serial chain | Parallel writers on one file conflict; parallel test runs on shared paths break each other | execution.md E04 |
| SA14 | Workers run on `sonnet` by default. `opus` only when the plan marks the task with a written reason (new safety decision, agent prompt, big file, serial chain) | Most tasks are contract-sized; the strong model is for judgment | execution.md E13; agent-plan.md "Model" |
| SA15 | Ceilings per agent: executor and fixer stop at about 50 tool calls or 30 minutes; reviewer at about 40 to 60 calls; a plan task prompt carries "stop at about 80 calls or 45 minutes and report". On the ceiling, report what was done and what is left | An agent without a ceiling once ran 150 calls and 300k tokens, costing more than the rest of the route | review.md V08; workers.md |
| SA16 | An agent that hit its ceiling, or passed about 150k tokens, is not resumed. A new agent starts with a handoff of at most 10 lines: files touched, red tests, next step | Resuming a bloated agent resends the bloat on every call | execution.md E14 |
| SA17 | Otherwise, continue an agent's work by resuming it (SendMessage), not by opening a new one that rereads everything | A fresh agent rereads the same files | execution.md E07 |
| SA18 | An agent the user interrupted is not resumed. First save what it left with `git --no-pager diff` into a patch in the state folder | Its work is otherwise lost or silently mixed with the next agent's | execution.md E07 |
| SA19 | Brake: an agent that hits its ceiling twice, or a wave that takes more than twice the previous one, stops the execution and goes to the user with what is left and the cost so far. Never run for hours without reporting | Runaway loops were the single largest waste observed | execution.md E17 |
| SA20 | Cost log: at the end of each wave append one line to `state.md`: wave, agents dispatched, review rounds, most expensive agent (tokens and minutes) | The baseline to tell whether a change to the process made it cheaper | execution.md E11 |

## Commits and files

| ID | Rule | Why | Lands in |
|---|---|---|---|
| SA21 | The main thread commits per task, with the exact file list and message the executor returned, after checking the diff of those files. Workers never commit or push | One owner of history; parallel workers committing collide | execution.md E05 |
| SA22 | A plan task names its files, entry symbols and tests, so the worker reads only the plan header ("Plan execution rules") and its own section | Rereading the whole plan per worker is the hidden cost of big plans | execution.md E15 |
| SA23 | A plan task's `Owns` includes out-of-area tests the change will break (search who imports the changed symbols). A task that discovers this midway stops and comes back, and each stop costs a resume | Ownership discovered late breaks the parallel wave | agent-plan.md |
| SA24 | Replace the old path with the new one instead of keeping both in parallel, unless a rollback switch requires both | A double path makes every test be touched twice | workers.md "planner" |
| SA25 | Test output goes to a file; only `FAILED` and `ERROR` lines and the summary come back into context | Full test logs are thousands of lines | execution.md E16; TS |
| SA26 | Moving code is done by script (line ranges or AST); the agent decides the map and fixes imports, never retypes a function body | Retyping is slow and introduces transcription bugs | AR12; execution.md E19 |
