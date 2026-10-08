# Subagents (SA)

The main thread is the orchestrator: it classifies, confronts, interviews, approves, dispatches and commits. Workers do the heavy reading and writing, communicate only through files in a state folder, and return a short fixed-format report. The weight of an agent is the context it resends on every call, times the number of calls.

## Roles and contracts

| ID | Rule | Why | Lands in |
|---|---|---|---|
| SA01 | The orchestrator classifies, confronts, interviews, approves, dispatches and commits. It does not do the heavy reading or writing | Its context is the one that lives longest | skill SKILL.md "C5 route" |
| SA02 | A worker never talks to the user. Anything missing comes back as a gap in the return, never as an assumption | Assumed rules become wrong code that a review later has to find | `.claude/agents/prd-flow-*.md`; R04 |
| SA03 | A defined agent (`.claude/agents/prd-flow-<role>.md`) is dispatched by `subagent_type` with a prompt of the slug, the absolute state folder, the Python interpreter and the task card (or a one-line request). Its briefing is its system prompt; never paste briefings into the prompt | The briefing is cached in the definition and needs no read to start; pasting it multiplies tokens | skill SKILL.md "C5 route"; `.claude/agents/prd-flow-*.md` |
| SA04 | Handing work to a subagent: paste only the rule rows it must implement (its contract) and point to files for everything else: PRD file, TRD file, files it owns, commands to run. Never paste whole documents | The contract is small and exact; the rest is reachable by path | AGENTS.md "Handing work to a subagent"; global block |
| SA05 | Workers write their output to `.claude/prd-flow/state/<slug>/` (outside git). The orchestrator reads only the return | Files are the handoff medium; the orchestrator's context stays small | `.claude/agents/prd-flow-*.md`; CE19 |
| SA06 | Every return has the same shape: `Done:` one line, `Files:` paths written, the requested content, `Gaps:` list or "none". At most 30 lines; executor and reviewer at most 20 | Predictable, cheap to read, gaps impossible to hide | `.claude/agents/prd-flow-*.md` "Return" |
| SA07 | Delivery ledger: each executor appends at most 8 lines to `deliveries.md` (`Creates`, `Changes`, `Leaves for`). A dependent task reads those blocks instead of the code | The next task learns the interface without reading the implementation | `prd-flow-executor.md`; agent-plan.md "Creates / consumes" |
| SA08 | A gap in a return is resolved (question to the user, or a new task) before any task that depends on it starts | A gap carried forward becomes a wrong implementation | execution.md E05 |
| SA09 | The interview runs in the main thread. Workers prepare the pre-interview; they never ask | Only the main thread can talk to the user | R04 |
| SA10 | Without the Agent tool, run the worker section in the main thread with the same briefing and budget | The procedure must not depend on the tool being present | skill SKILL.md |
| SA11 | Workers edit docs with Write and Edit only; no Python or shell script writes markdown or HTML. Running the checker script is fine | Script-written docs were slower and error prone | WS07; `.claude/agents/prd-flow-*.md` |

## Parallelism, models and ceilings

| ID | Rule | Why | Lands in |
|---|---|---|---|
| SA12 | No worker opens a subagent. Parallelism belongs to the main thread, by waves | Nested agents multiply context and hide cost | execution.md E12 |
| SA13 | A wave runs tasks with disjoint `Owns` in parallel; tasks touching a big file form a serial chain | Parallel writers on one file conflict; parallel test runs on shared paths break each other | execution.md E04 |
| SA14 | Workers run on `sonnet` by default. `opus` only when the plan marks the task with a written reason (new safety decision, agent prompt, big file, serial chain) | Most tasks are contract-sized; the strong model is for judgment | execution.md E13; agent-plan.md "Model" |
| SA15 | Ceilings per agent: executor, fixer, surveyor, docs agent, reviewer and recheck stop at the ceilings of `review.md` V08, and a plan task prompt carries its ceiling. On the ceiling, report what was done and what is left | An agent without a ceiling once ran 150 calls and 300k tokens, costing more than the rest of the route | review.md V08; `.claude/agents/prd-flow-*.md` |
| SA16 | An agent that hit its ceiling, or passed about 150k tokens, is not resumed. A new agent starts with a handoff of at most 10 lines: files touched, red tests, next step | Resuming a bloated agent resends the bloat on every call | execution.md E14 |
| SA17 | Replaced by SA31: an agent's work is continued by a new agent with the pack, not by a resume | The resume needed a ToolSearch that rewrote the prompt cache (LS28) | execution.md E07 |
| SA18 | An agent the user interrupted is not resumed. First save what it left with `git --no-pager diff` into a patch in the state folder | Its work is otherwise lost or silently mixed with the next agent's | execution.md E07 |
| SA19 | Brake: an agent that hits its ceiling twice, or a wave that takes more than twice the previous one, stops the execution and goes to the user with what is left and the cost so far. Never run for hours without reporting | Runaway loops were the single largest waste observed | execution.md E17 |
| SA20 | Cost log: at the end of each wave append one line to `state.md`: wave, agents dispatched, review rounds, most expensive agent (tokens and minutes) | The baseline to tell whether a change to the process made it cheaper | execution.md E11 |

## Commits and files

| ID | Rule | Why | Lands in |
|---|---|---|---|
| SA21 | The main thread commits per task, with the exact file list and message the executor returned, after checking the diff of those files. Workers never commit or push | One owner of history; parallel workers committing collide | execution.md E05 |
| SA22 | A plan task names its files, entry symbols and tests, so the worker reads only the plan header ("Plan execution rules") and its own section | Rereading the whole plan per worker is the hidden cost of big plans | execution.md E15 |
| SA23 | A plan task's `Owns` includes out-of-area tests the change will break (search who imports the changed symbols). A task that discovers this midway stops and comes back, and each stop costs a resume | Ownership discovered late breaks the parallel wave | agent-plan.md |
| SA24 | Replace the old path with the new one instead of keeping both in parallel, unless a rollback switch requires both | A double path makes every test be touched twice | `prd-flow-docs.md` |
| SA25 | Test output goes to a file; only `FAILED` and `ERROR` lines and the summary come back into context | Full test logs are thousands of lines | execution.md E16; TS |
| SA26 | Moving code is done by script (line ranges or AST); the agent decides the map and fixes imports, never retypes a function body | Retyping is slow and introduces transcription bugs | AR12; execution.md E19 |

## Agent management (prd-flow, plan of 2026-10-08)

| ID | Rule | Why | Lands in |
|---|---|---|---|
| SA27 | **Spawn rule by residency:** inline only what the main must hold (the user's answers, a return, a short command); work that would leave more than about 8k tokens or 3 files the main does not need goes to an agent. Spawn only for another model, for reads kept out of the main, or for parallel work; one owner per role in the dispatch map | A token in the main is resent on every later call: 20k read at call 10 of 50 cost about 800k tokens on the strongest model (efficiency-audit C2, C5) | SKILL.md "C5 route"; `prd-flow-*.md` |
| SA28 | **Thin main with a contract.** Allowed: `repo.md`, one INDEX Grep, the surveyor's confrontation, agent returns, its state files, `git commit` with a file list, one `gate.py --rules`, `promote.py` and the close call. Forbidden: PRD, TRD or source reads before the surveyor, edits under `docs/` or the source folders, reading diff content, debugging the gate, agent-only references. Each violation is counted (`main_violations`) | LS24 and LS27: the main did the docs phase inline and took US$8.10 against US$4.42 dispatched (audit A3, A8, A12) | SKILL.md "Main card"; `eval/METRICS.md` |
| SA29 | **Bounded input and output.** Every dispatch names its pack (state files, exact paths or symbols) and nobody explores beyond it; results go to state files and the return is at most 20 lines, which the main never reopens | Agents spawned without a pack explored the whole repository and returned long text (efficiency-audit C4, C6) | `prd-flow-*.md`; SA06 |
| SA30 | **Loop cap:** at most 2 reruns per step; the third failure returns the ERROR lines as a gap instead of looping | r2: 47 gate runs inside agents in a format loop (AUDIT A9) | `prd-flow-*.md`; execution.md E17 |
| SA31 | **No resume and no mid-run tool loading:** an agent's work continues in a new agent with the pack; the main never calls ToolSearch during a C5 | The SendMessage resume needed a ToolSearch that rewrote 69k to 85k tokens of cache at US$10 per million (AUDIT A4, LS28) | SKILL.md "C5 route"; execution.md E07 |
| SA32 | **Roles are defined subagents:** `.claude/agents/prd-flow-<role>.md` carries the briefing as its system prompt, a pinned model and the minimum tools (surveyor and reviewer read only; executor without web tools); the main dispatches by `subagent_type` | A defined agent starts with no briefing read, so compliance does not depend on the main reading rules it argued away (LS27; efficiency-audit S4) | `kit/.claude/agents/prd-flow-*.md`; SA03 |
| SA33 | **Models by role:** surveyor and docs agent on the strongest model at high effort; executor and reviewer on the fast model; a scoped re-check that only confirms a fix, and the closing checks, on the cheapest | Judgment steps decide the quality; a fast-model agent costs about a quarter of the same work in the main (efficiency-audit S5) | agent definitions; SA14; WF51 |
| SA34 | **Granularity by the critical path:** a task is at least one file and its test; split only when the pieces run in parallel and each is at least about 10 tool calls of work; sequential pieces of one area are one task; a one-rule change is one executor task | Each task is an agent with a cold start of about 23k tokens: a plan of 1 task spawned 5 to 6 agents (efficiency-audit C3, C5) | agent-plan.md "Granularity by the critical path" |
| SA35 | **Context affinity:** tasks that read the same large files, or the same TRD area, go to the same executor; parallel width comes from independent areas | N parallel agents each rereading one big file pay it N times | agent-plan.md "Context affinity" |
| SA36 | **Waves are computed, not reasoned:** `gate.py --step plan` prints the wave table from `Depends on` and `Owns`, critical path first, at most 4 executors per wave dispatched in one background message, and fails when two tasks of one wave share a file in Owns | A hand-built wave plan collided on files and polled agents (efficiency-audit S1) | `gate_waves.py`; agent-plan.md |
| SA37 | **Task card in the prompt:** the executor prompt carries its task section (contract IDs, Owns, read list with symbols, tests, commit line), at most 25 lines; the rest by path | A card in the prompt saves the Read turn of the plan and bounds what the agent reads | agent-plan.md "Format of a task" |
| SA38 | **Shared prompt prefix:** agents of one role share the leading text (stable paths, no timestamps) and the task line comes last | Siblings then hit the same cached prefix | agent definitions; SKILL.md "C5 route" |
| SA39 | **Interfaces before parallel work:** names shared between tasks come from the plan's `Creates / consumes` and the producer's `deliveries.md` block, never from the producer's code | Parallel tasks otherwise guess each other's symbols | agent-plan.md; SA07 |
| SA40 | **One reviewer per wave** on the combined wave diff and the rule IDs; a second round only after a Critical or High fix, scoped to the fix diff | A reviewer per task multiplied cold starts and rereads (AUDIT A5) | review.md V03 |
| SA41 | **Checkpoint:** past about 120k tokens in the main, or with more than 2 waves left, the main writes `state.md` and continues in a fresh session with `/prd-flow resume <slug>` | The main's context is resent on every call | execution.md E01; SKILL.md "State" |
| SA42 | **Execution session on the fast model:** after the plan is approved, execution may continue in a fresh session on the fast model where the main only dispatches, commits and closes. Adopted only if the measured arm keeps quality | Dispatch, commit and close need no judgment, so the strongest model is wasted there (decision D5) | execution.md E02; `eval/arms-big.json` |
