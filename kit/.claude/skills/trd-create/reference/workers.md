# trd-create workers

Read only the section with your name. You do not talk to the user: anything missing becomes a **gap** in the return. Parallel batches when reads are independent; code only by symbol (`Grep -n`, then `Read` with offset and limit); big files from `.claude/skills/prd-gate/repo.md` never whole. Write with Write and Edit only. Names only, never line numbers or default values. Everything in English, no em dash (U+2014). State: `.claude/prd-gate/state/trd-create/`.

Return, at most 30 lines:
```
Done: <one line>
Files: <paths written>
<the content the section asks for>
Gaps: <list, or "none">
```

## feature-mapper

Maps ONE feature (or one area in N4). Input: the row of `features.md` (folder, PRD sections).

1. **Batch 1:** `Glob` of the folder; the PRD sections' rule tables (`Grep "^| " <section files>`); `Grep` of the PRD ID prefixes in the folder (docstrings and headers); the tests folder.
2. For each file: its role in one line, its main symbols, the PRD IDs it implements. Group files by kind (root, `domain/`, services, agents, adapters) as the folder does.
3. **How it enters the flow:** the path from the external trigger (route, handler, job, event) to the result, by symbols, in at most 10 steps. Verify each entry point has a caller outside the tests (`Grep` the symbol); otherwise mark it "not wired".
4. **Tests:** test files and what each covers, with the IDs they cite; fakes and harnesses used.
5. **Must not break:** the 3 to 8 properties whose breakage hurts most (each with the PRD ID or invariant).
6. **Known pitfalls:** traps a newcomer falls into (a patch that must target the caller module, a path computed from the module location, a lock, an ordering).
7. Write `docs/trd/<feature>.md` from `docs/templates/trd-feature.md`, and `<feature folder>/CLAUDE.md` from `docs/templates/feature-CLAUDE.md` (at most 20 lines, pointing to the TRD).
8. Ceiling: about 50 tool calls.

Return: files written, entry points not wired, files over the size limits of `docs/code-structure.md`, gaps.

## infra-mapper

Maps the shared code (`infra/` or its equivalent), configuration and environment. Same steps as the feature-mapper, plus a table of configuration: each setting, where it is read, what it controls (no default values), and how it changes (env, config, data). Writes `docs/trd/infra.md`.

## rules-writer

1. `docs/trd/invariants.md` from `docs/templates/invariants.md`: the repository rules by kind of change (any change; new environment variable; removed variable; new external call; new model call, if any; new table or column with personal data; new migration; new state; new endpoint or dependency; logs and metrics; tests; configuration), each with the next free `I-NN` and its proof: a test file name (structural tests first) or a principle of the constitution. Sources: the constitution, `AGENTS.md` critical constraints, `docs/code-structure.md`, every structural test in the repository.
2. `docs/trd/testing.md` from `docs/templates/testing.md`: the gate targets of `scripts/gates.sh` and what each runs, how to run one file, the test configuration (markers, paths, timeouts, coverage), the guards (network, database), the fakes and harnesses with what each fakes, and the patterns that avoid rework.

Return: invariant count by kind, gaps.

## index-writer

1. `docs/trd/README.md` from `docs/templates/trd-readme.md`: one row per feature (what it covers, TRD link, folder, PRD sections linked), then the cross-cutting files.
2. `docs/flow.md`: the one end-to-end mermaid diagram of the system (triggers, features, external systems, failure exits), with a short legend. It is the single overview; other docs link to it.
3. `docs/prd/INDEX.md`: fill the TRD column of every section with the feature maps that implement it.
4. Run `python .claude/skills/prd-gate/scripts/gate.py` and fix every error in the files you wrote.

Return: files, the gate's last line, gaps.
