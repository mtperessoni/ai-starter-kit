# Audit: kit and FE test quality and cost (read-only, 2026-10-14)

## 1. Slowest kit modules (measured, `python -m unittest tests.<m>`, Windows)
| Module | Tests | Wall | Why |
|---|---|---|---|
| test_kit_gates_run_speed | 49 | 174 s | Each test builds a temp repo (`git init -q`, line 293), runs `scripts/close_gate.py` via subprocess (lines 112, 368), config_get.py (299), and a `cmd /c mklink /J` (271). About 3.5 s per test, all process spawns. |
| test_kit_scripts | 56 | 59 s | Spawns scripts and bash per test; about 1 s per test. |
| test_kit_related_speed | 25 | 30 s | Same pattern (git repo plus related_tests.py subprocess); 1.2 s per test. |
| test_kit_telemetry_hook | 48 | 18 s | Subprocess launcher tests. 4 FAIL on this machine (LauncherTest: failing_stub_skipped, missing_hook_script, commands_python_from_ai_kit_json, failing_interpreters_on_path). Environment-dependent. |
| test_kit_retro | many | 6 s | Cheap. |
| test_eval_transcript | 56 | 0.25 s | Pure in-process; not slow. |
Sum of the 4 slow modules: about 281 s of a 106 s average full suite, so they dominate. Gates-run-speed alone is 174 s, close to the 280 s ceilings and the 600 s timeouts when the machine is loaded (Defender, parallel agents). Note: test_kit_retro wrote `.ai-kit/runs/none/retro.md` in the kit (git-ignored) as a side effect.
Cause is process spawn cost on Windows (about 50 to 200 ms per python/bash/git start, git init per test), not sleeps (no sleep in these modules).

## 2. Text-oracle tests
- 1113 `def test_` in tests/. 90 `assertIn` on read text across 21 files (Grep), 66 references to SKILL.md / reference/*.md / kit docs / templates across 28 files.
- Most `assertIn` on text check generated report output (test_eval_report.py:260-291, e.g. `"## Hard gates"`, `"LT is adopted"`, a literal table row `"| tokens_total | S | 100 #1 | 300 #3 | 200 #2 |"`).
- Prose oracles on kit docs exist in test_kit_gates_v5.py (12 refs to doc paths), test_kit_tools.py (4), test_gate_html/plan_align (4 each), test_runtime_consistency.py, test_kit_readiness.py. Example at test_kit_gates_run_speed.py:451: `assertEqual(text.count("subprocess.run("), 1)` asserts the source text of a script contains exactly one call.
- Effect: a wording or heading change in a skill or script breaks a test; the agent reruns and edits the literal in the test. Rough estimate, not proven per test: 100 to 150 tests are literal-string oracles.

## 3. Lockstep changes (git log --since=2026-10-01 --numstat)
- 195 commits with file changes; 92 touch tests/ (47%); 90 of those also touch implementation files (98% of test-touching commits). Tests are almost never changed alone.
- Test churn over the period (all `git log -p -- tests`): +1204 / -96 test defs, +2765 / -309 assert lines, skips added 10 and removed 0 (skip/expectedFailure/skipTest present in 13 files, 25 occurrences, mostly platform/env guards).
- Sample (test lines added/removed): 4148a8c sheet lint: 181/245, removed Q6-Q9 dimensions tests and rewrote rules_v4 (-134 lines) while adding new test_gate_sheet.py (+171): behavior replaced, old assertions deleted. 9a17533 verify and drop guard hook: 131/173, telemetry tests rewritten (+53) alongside new test_kit_verify. acf4cc5 prd-sweep: 593/148, new tests +488 and 28 files; test_gate_trd_sibling edited in place (+37 modified). 3524bd2 docs-html: 392/105, removed 31 assert lines in test_kit_scripts and edited test_promote in place. 7cbfee3 eval: 719/84, mostly additive.
- Reading: roughly 60 to 70% added lines are new tests (healthy), but each design pivot (4148a8c, 9a17533, 3524bd2) deletes or edits existing assertions to follow the new behavior. 96 test defs deleted and about 309 assert lines removed in 2 weeks, none replaced by skips. No loosening via skip detected; "loosened" (assertEqual to assertIn) not counted.

## 4. Process-testing vs user-facing
The kit's product is process tooling, so almost everything is meta: gates, verify, related, baseline, retro, telemetry, eval harness (test_eval_* = 14 files), docker hygiene, reap, cleanup, watch. By file name: about 45 of 51 files (about 85 to 90%) test the process itself (speed of gates 3 files, telemetry, retro, eval, guard hook). Only build_prd/trd_html, gate rules, promote resemble user-visible behavior (about 10 to 15%). 3 files are literally named `*_speed` (gates_run_speed, related_speed, eval_run_speed): tests that guard the speed of the test tooling are themselves the slowest tests.

## 5. agora-consulta-fe
- 149 vitest test files in src/**/__tests__/ (unit project only, `include: src/**/__tests__/**/*.test.ts`). No structure/docs/ratchet tests in the vitest suite. `ai-kit.json` `tests.always` is empty. "Structure tests, docs gate" in `verify.py` are run as separate steps (`gates.sh ratchet`, `gates.sh docs`), python scripts, not part of vitest.
- Cold start measured: `gates.sh one <3-test file>` = 29 s wall (exit 0) while vitest reports 2.08 s (collect 1.17 s, prepare 543 ms). Direct `node node_modules/vitest/vitest.mjs run --project unit <file>` = 4 s wall (616 ms reported). So about 25 s per single-file run is wrapper overhead, not vitest.
- Cause candidates visible in config: vitest.config.ts is a multi-project config; the storybook project (storybookTest plugin, playwright browser provider) is loaded even for a unit run (log shows "No story files found src\**\*.mdx" and "Using tsconfig paths for react-docgen"). No pool/isolation overrides (default forks, isolate true). Plus gates.sh bash startup, interpreter resolution, `offline` wrapper and `bash -c` nesting. Passing `--project unit` directly skips storybook init.
- Stray note: one gates.sh invocation was auto-moved to background by the tool; verified no node process remains.

## Gaps
Per-test counts of literal-prose oracles and "loosened" assertions are estimates; telemetry failures not diagnosed; exact split of the 25 s FE wrapper overhead not profiled.
