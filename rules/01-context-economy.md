# Context economy (CE)

Everything an agent reads is resent on every following call of that agent. A file read once in a long session is paid for dozens of times. These rules keep what enters the context small and on purpose.

| ID | Rule | Why | Lands in |
|---|---|---|---|
| CE01 | Load only what the task needs. Every lookup is one Glob, one Grep or one ranged Read | Whole-file reads are the main cost of a session | AGENTS.md "Finding things" |
| CE02 | Independent reads go in one message, in parallel | Fewer turns, each turn resends the context | skill SKILL.md "Context economy" |
| CE03 | Read by ID: `Grep -n` for the ID or symbol, then `Read` with offset and limit | A rule is one line; its file can be hundreds | skill SKILL.md; workers.md header |
| CE04 | Files listed as big in `repo.md` are read only by symbol, never whole | One big file can cost more than the rest of the task | skill repo.md "Big files" |
| CE05 | A human-reading version (HTML, PDF) is never read by an agent | It duplicates the markdown at several times the size | AGENTS.md "Finding things" |
| CE06 | A broad sweep of a large codebase goes to an Explore agent with explicit questions; only the answers come back | The sweep's file dumps stay out of the main context | prd-flow impact.md; prd-create and trd-create workers |
| CE07 | Docs are small and split: one PRD file per section, one TRD file per feature, a `CLAUDE.md` of at most 20 lines per map folder (AR07: feature folders plus `map_dirs`) | An agent loads the one piece it needs | docs/prd/INDEX.md, docs/trd/README.md, AR07 |
| CE08 | Maps name files and symbols, never line numbers or default values | Lines and defaults change without anyone touching the map, and a stale map misleads | DS07, docs/trd/README.md |
| CE09 | Rule docs are tables, one rule per line, stable IDs, an index table at the top. Say only what changes behavior | Prose is reread every call; tables are scanned | WS05; every reference file |
| CE10 | Cross-reference by ID instead of restating a rule | One source per rule; restated rules drift | every doc |
| CE11 | Lazy loading comes from structure (small files, index, symbol maps), never from a custom query CLI, a blocking hook or an extra layer to teach in every prompt | Measured: a custom extractor and native Grep cost the same tokens (about 420 vs 440); the tool only added prompt cost and maintenance | LS05 |
| CE12 | Budgets for messages: context shown to the user at most 6 lines; a rule confrontation at most 40; a round message at most 25; at most 4 questions per round; a worker return at most 30 lines, executor and reviewer at most 20 | Unbounded messages grow every round and are resent | skill SKILL.md "Context economy" |
| CE13 | Depth by case: a question does not hunt divergences. An out-of-scope divergence is noted in one line, never investigated | Investigation is the expensive part; scope creep doubles it | skill SKILL.md, R01 |
| CE14 | Count and list with the Grep tool, not through the shell; patches with `git --no-pager diff` | Shell output proxies (such as RTK) can swallow output and cause retries | skill SKILL.md |
| CE15 | A skill's `SKILL.md` holds phases and rules only; details live in references behind IDs, read only at the step that needs them | `SKILL.md` loads on every invocation | skill layout |
| CE16 | A plan file targets about 30 KB and never grows past 60 KB; a new amendment gets its own plan file with one line in the main plan pointing to it | Every executor reads the plan header and its section, and a big file costs on each read | skill agent-plan.md; gate `--plan` |
| CE17 | A plan with more than 6 tasks, or touching a big file, executes in a new session resumed from the state folder | The planning session already carries the confrontation, interview and writing | skill execution.md E01 |
| CE18 | Keep `CLAUDE.md`, `AGENTS.md` and the global `~/.claude/CLAUDE.md` lean; they load in every session and every subagent | Measured: each real session started at about 76k tokens and each subagent at about 41k before doing anything | LS02 |
| CE19 | The orchestrator never reopens files a worker wrote; it reads the worker's return | Reopening doubles the cost the worker existed to absorb | SA05 |
| CE20 | Never `@`-import feature maps or docs from the root `CLAUDE.md`. Root and parent `CLAUDE.md` files load at session start, and `@` imports load eagerly with them (up to 4 hops); a subfolder's `CLAUDE.md` loads only when a file in that folder is read, written or edited, and reloads after `/compact` | An `@` import turns a lazy map into a fixed cost of every session and every subagent | CLAUDE.md template; AR07 |
| CE21 | A subagent prompt names the feature `CLAUDE.md` and TRD paths it needs instead of relying on automatic loading | Whether subagents load nested `CLAUDE.md` files the same way is not documented | SA04; prd-flow workers |
| CE22 | Search noise is excluded: generated files, vendored code, lockfiles, minified bundles, large fixtures and snapshots are listed in `.ignore` (honored by the search tool) and denied for reading in `.claude/settings.json`; `ai-kit.json` `ignore` and `generated_patterns` are the source | A match inside a generated or vendored file is a wrong answer that costs a read to discard, and a minified bundle or lockfile read whole can cost more than the rest of the task | install; doctor |
