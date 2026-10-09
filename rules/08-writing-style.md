# Writing style (WS)

| ID | Rule | Why | Lands in |
|---|---|---|---|
| WS01 | Everything in the target repository is in English: docs, PRD, TRD, ADRs, skill files, state artifacts, plan, commit messages, code identifiers, test names, log messages. User-facing product copy follows the product's locale | One language for agents and people; no translation drift between doc and code | constitution; AGENTS.md |
| WS02 | No em dash (U+2014) in code, docs, prompts or commit messages. Use a comma, colon, period, or rewrite | House style, enforced by the gate | AGENTS.md; gate G4 |
| WS03 | Zero comments by default. Comment only a non-obvious and critical WHY (hidden constraint, workaround). Never describe what the code does, never reference a ticket or task | Names carry meaning; comments rot | AGENTS.md |
| WS04 | Commits follow Conventional Commits, in English, with the rule IDs when they apply: `feat(report): stop at 600 s ceiling (RPT-05)` | History is searchable by ID | AGENTS.md; WF21 |
| WS05 | Rule documents (skills, references, constitution, invariants) use tables with stable IDs, one rule per line, an index table at the top; say only what changes behavior | Token cost per read | CE09 |
| WS06 | Examples in reference files are marked illustrative: "IDs, texts and paths in the examples are illustrative: always read the real line" | Agents otherwise copy example values | every skill reference |
| WS07 | Docs are edited with Write and Edit directly. Never generate or edit markdown or HTML through ad hoc scripts. A hand-maintained HTML file is edited only by exact-line Edit, never rewritten whole | Script-written docs were slower and broke formatting | SA11 |
| WS08 | Sheet items are in product language with a concrete example (rule IDs and code names only in context lines); when the user does not understand an item, show today's rule and an example from the PRD rows the sheet cites, never the same question in new words | Users decide on scenarios; a rephrased question repeated a topic 3 to 4 times per run | WF15 |
| WS09 | Never write a prohibition without the allowed way that works on Windows, macOS and Linux (M08): "never `git stash`" names the worktree, "no heredoc" names Write then `git commit -F <file>`, "no sed -i" names Edit | Bare prohibitions made agents improvise: 53 heredocs and 6 orphan processes in the audited run (audit section 9) | MAINTAINING.md M08; agent files |
| WS10 | One home per rule: a runtime file states a rule once and other files link by heading, never restate it or its numbers (M10) | Duplicated rules drifted and an agent followed the stale copy | WF76 |
