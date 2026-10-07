# trd-create workers

Read only the section with your name. You do not talk to the user: anything missing becomes a **gap** in the return. Parallel batches when reads are independent; code only by symbol (`Grep -n`, then `Read` with offset and limit); big files from `.claude/skills/prd-flow/repo.md` never whole. Write with Write and Edit only. Names only, never line numbers or default values. Everything in English, no em dash (U+2014). State: `.claude/prd-flow/state/trd-create/`.

Return, at most 30 lines:
```
Done: <one line>
Files: <paths written>
<the content the section asks for>
Gaps: <list, or "none">
```

## feature-mapper

Maps ONE area wherever its files live: its feature folder, or the globs of its `areas` entry in `ai-kit.json`. Input: the row of `features.md` (folder or globs, PRD sections) and `trd_budget_lines` (`repo.md`, default 250).

Rows must pass `python .claude/skills/prd-flow/scripts/gate.py --trd` (K-54): a path is a real tracked file you saw in the `Glob`; every symbol in `Main symbols` exists in that row's files (`Grep` it); every ID in `IDs` appears in the row's files (a docstring, header or test name); otherwise leave the ID out and list it as a gap.

1. **Batch 1:** `Glob` of the folder or the area globs; the PRD sections' rule tables (`Grep "^| " <section files>`); `Grep` of the PRD ID prefixes in those files (docstrings and headers); the tests of the area.
2. For each file: its role in one line, its main symbols, the PRD IDs it implements. Group files by kind (root, `domain/`, services, agents, adapters) as the folder does.
3. **How it enters the flow:** the path from the external trigger (route, handler, job, event) to the result, by symbols, in at most 10 steps. Verify each entry point has a caller outside the tests (`Grep` the symbol); otherwise mark it "not wired".
4. **Tests:** test files and what each covers, with the IDs they cite; fakes and harnesses used.
5. **Must not break:** the 3 to 8 properties whose breakage hurts most (each with the PRD ID or invariant).
6. **Known pitfalls:** traps a newcomer falls into (a patch that must target the caller module, a path computed from the module location, a lock, an ordering).
7. Write `docs/trd/<area>.md` from `docs/templates/trd-feature.md`, with no History section (K-55). When the file would pass `trd_budget_lines`, split instead: `docs/trd/<area>/<part>.md` per group of PRD sections (parts mirror the section groups of `docs/prd/INDEX.md`), plus `docs/trd/<area>/README.md` listing the parts with their PRD IDs; the index-writer points `docs/trd/README.md` to the folder. Write `<feature folder>/CLAUDE.md` from `docs/templates/feature-CLAUDE.md` (at most 20 lines, pointing to the TRD) only when the area has its own folder; otherwise the index-writer covers it in a folder map.
8. Run `gate.py --trd`; fix every G23 to G26 in your files.
9. Ceiling: about 50 tool calls.

Return: files written, entry points not wired, hotspots over the limits of `docs/code-structure.md` (files and tests), the last line of `gate.py --trd`, gaps.

## infra-mapper

Maps the shared code (`infra/` or its equivalent), configuration and environment. Same steps as the feature-mapper, plus a table of configuration: each setting, where it is read, what it controls (no default values), and how it changes (env, config, data). Writes `docs/trd/infra.md`.

## rules-writer

1. `docs/trd/invariants.md` from `docs/templates/invariants.md`: the repository rules by kind of change (any change; new environment variable; removed variable; new external call; new model call, if any; new table or column with personal data; new migration; new state; new endpoint or dependency; logs and metrics; tests; configuration), each with the next free `I-NN` and its proof: a test file name (structural tests first) or a principle of the constitution. Per kind of change, add the "Pattern to copy" (DS31): an existing file that is the reference implementation. Sources: the constitution, `AGENTS.md` critical constraints, `docs/code-structure.md`, every structural test in the repository.
2. `docs/trd/testing.md` from `docs/templates/testing.md`: the gate targets of `scripts/gates.sh` and what each runs, how to run one file, the test configuration (markers, paths, timeouts, coverage), the guards (network, database), the fakes and harnesses with what each fakes, and the patterns that avoid rework. Add the schema and contract snapshots (DS30): file, command, and the `contracts` entry of `ai-kit.json`; invariants link them. When `repo.md` "Shared PRDs" or its sibling section lists a sibling consumer and no snapshot is configured, propose the snapshots (what to snapshot, the source, the `contracts` entry) in the return; do not configure them (K-74).
3. **Invariant gaps (K-73).** A row whose proof column has no test or lint rule says `gap`. Count the rows containing `gap`; for each, propose the lint rule or test that would prove it (file name and what it asserts), ranked by `scripts/gates.sh hotspots` (the gap in the most-changed files first). Write the count to `ai-kit.json` `allowlist.invariant_gaps` (shrink-only: the ratchet errors when it rises and asks to lower it when it drops). Never mark a row `gap` to hide a missing proof you did not look for.

Return: invariant count by kind, the gap count with the proposals ranked (at most 10 lines), patterns to copy found, contract snapshots found or proposed, hotspots over the limits, gaps.

## index-writer

1. `docs/trd/README.md` from `docs/templates/trd-readme.md`: one row per area (what it covers, TRD link, folder or globs, PRD sections linked); an area split into parts (K-55) links its `docs/trd/<area>/` folder; then the cross-cutting files.
1b. For each folder of `map_dirs`, write its `CLAUDE.md` from `docs/templates/folder-CLAUDE.md` (at most 20 lines, one row per area with its files there, PRD IDs and TRD link).
2. `docs/flow.md`: the one end-to-end mermaid diagram of the system (triggers, features, external systems, failure exits), with a short legend. It is the single overview; other docs link to it.
3. `docs/prd/INDEX.md`: fill the TRD column of every section with the feature maps that implement it.
4. Run `python .claude/skills/prd-flow/scripts/gate.py` and `gate.py --trd`; fix every error in the files you wrote.

Return: files, the last line of each run, gaps.
