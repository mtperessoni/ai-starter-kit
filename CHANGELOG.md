# Changelog

User-visible changes to the kit, newest first. Projects receive them through `/ai-kit update`.

## Faster related tests

Measured in a consumer (16 cores, Windows): `related` cost 22 to 27 s for 1 to 7 changed files and 141 s for a 317-file branch, while the whole suite took 66 s; the selection scan alone took up to 72 s.

- `related_tests.py` builds one import index per call (each test file read once, only its import lines kept) instead of scanning every test for every changed module: 54 to 72 s down to 2.9 s on a 317-file change, with the same selection (a test keeps the old algorithm as its reference).
- `gates.sh related` calls `related_tests.py` directly (no `--help` probe) and leaves `tests.always` out; `verify` passes `--with-always`, so the structure guards run once at the slice closing. New flag `--with-always` on `related_tests.py`.
- `related` with no files covers the uncommitted and untracked files only (`--base REF` keeps the merge-base scope). A selection over half of the test files runs the whole suite instead and says so: the runner gets no file list and collects its configured suite, so its testpaths, markers and ignores decide what runs.
- Runner templates accept `{python}` (`tests.runner`, `tests.parallel_runner`, `commands.test`, also in `baseline`): the interpreter `gates.sh python` resolves. `stacks/python.md` defaults to `{python} -m pytest` (`one` on a small file: 2.0 s against 3.3 s with `uv run`). Templates without it work as before; an installed project adopts it by editing its `ai-kit.json`.
- `AGENTS.md` template, test step: iterate on the one test file being edited, `related` once at the slice closing, the whole suite once per delivery, files read with Read and Grep (0.3 s a call against 2.4 s through the shell).

## Faster runs

The test wrapper added delay to every agent test run: measured in a consumer on a 5-test file (0.05 s per test), the runner alone took 1.8 s and `gates.sh one` 3.4 s; a new worktree cost 30 to 110 s before its first useful test. Rules: TS55, TS56, SA67, WF84.

- `scripts/gates.sh` reads the whole config in one Python call per target (was one call per key, five for `one`); `compare` and `rerun` fold the deselect list into the same call.
- `run_probe.py` wraps only the long targets (`offline`, `compare`, `rerun`, `baseline`, `integration`, `full`, `build`), not `one` or `related`.
- `related` no longer runs the ratchet first; the ratchet runs at the end of `lint-files` (the default path is `related`, `fix-files`, `lint-files`) and stays in `gates.sh ratchet`, `verify` and `close`. `offline` still accepts file arguments.
- New: the offline guarantee belongs in the test runner's own configuration (root conftest sets the offline flag, drops the database URL and skips the integration folder unless the run names that tier), coverage only on the whole suite, measure the runner's startup (TS55, `stacks/python.md`, `stacks/README.md`). The default path iterates with the runner on the changed test files; `gates.sh one` stays available. Repository files are read with Read and searched with Grep, not shell `cat`, `sed -n`, `head`, `tail` or `grep`.
- New: `compare` runs in parallel, and a test that fails only in parallel is an isolation defect fixed first (TS56).
- New: lanes, one or two long-lived worktrees per person warmed once and reused slice after slice; parallel executors still get their own worktree, at most 2 (SA67, WF84).
- New key `tests.no_tests_exit_codes` (`[5]` for pytest): a `related` chunk that collects nothing no longer turns a green run red.
- `related` stops being slower than the whole suite. Measured in a consumer on 16 cores: the whole suite in parallel took about 60 s, while `related` took 16 s for a one-file change (two runner calls and an eval tier collected only to be deselected) and 99 s for an eight-file change (over the cap it fell back to the owning folder, which was `src/`, in one process). New keys: `tests.parallel_runner` runs a selection of `tests.parallel_from` files or more, and any selection over `tests.related_max_files`, in parallel, keeping every importer instead of the folder fallback; `tests.runner_args_file` hands the selection to one runner call as `@file`. The Python stack says which folders belong in `tests.related_exclude`: only those with no offline test. Without the new keys a project behaves as before.

## Harness-native subagents

The kit restated things Claude Code already does for subagents, and two of those rules made runs worse: a token ceiling that replaced a working agent with a cold one (rereads, leftovers turned into new lanes, the risk of two agents on one task) and a closed tool list that sent even a short read of the chief through a dispatch. Checked against the Claude Code sub-agents, tools and worktrees documentation. Rules: CR08, CR09, CR10, CR12 (amended).

- Removed: the per-agent ceilings and the 150k hand-back (`run.md` V08, the "Ceiling" failure rows, DP03 replace, `Interrupted: yes`); the agents now carry `maxTurns` and a long or stopped agent is continued with SendMessage, the harness compacting its context.
- Removed: "pass `model` on every dispatch"; `.claude/settings.json` sets `env.CLAUDE_CODE_SUBAGENT_MODEL` to `sonnet`, an agent file's `model` wins.
- Removed: "never open another subagent" (nesting is the harness's default); the minutes in a return (the harness reports duration and tokens); "one command per call" (strong models are cheaper with composite commands); "foreground only, timeout under 600 s" (the harness moves a timed-out command to the background; the no-orphan rule stays).
- prd-flow chief: every harness tool; agents still do the heavy reading and every edit, and the chief never redoes their work.
- Kept, because the harness does not do them: the guard hook, the no-orphan rule and `reap`, disjoint file ownership, the post-tool hook, the preamble meter and the telemetry. The tool-call budgets of the one-shot `prd-create` and `trd-create` workers also stay: they bound an exploration that returns once, the harness has no per-dispatch turn limit for a general agent, and they never replace an agent with a cold one.
- The prd-flow chief offers a fresh session past about 150k tokens (was 120k), the same number as CR11 and the post-tool hook.
- History rows SA15, SA16, SA19, SA48, SA54, RV08 and WF52 now say which core rule replaced or amended them.

## Global block: no stall in subagents, one retry for proxied output

- `global/CLAUDE.md` opens with the scope of the rules that ask for the user's yes, a report or a question: they bind the main thread; a subagent returns the decision as a gap instead of waiting.
- `rtk`: an output that looks cut or wrong is rerun once with `rtk proxy` or replaced by the Grep and Read tools, never retried as is (CR17).
- `scripts/gates.sh reap` where it exists, otherwise the agent stops its own process by PID; the checkpoint is at about 150k tokens, the post-tool hook's number (CR11).

## Slimmer prd-flow gate and flow (K4b)

`gate.py` keeps G0, G1 and G8 as errors, G15 and G22 under `--change`, G23 and G28 as warnings, D4 and P17 as warnings, G5, G29 and G32 only under `--html`. Removed: G2, G3, G9, G11, G12, G14, G16 to G21, G24 to G27, G30, G31, Q1 to Q5, S0 to S6, P1 to P10, and the modes `--pack`, `--rules`, `--sheet`, `--trace`, `--final`, `--snapshot`, `--fix`; modules `gate_interview.py`, `gate_budget.py`, `gate_remote.py`, `gen_index.py`, `prd_sweep.py`. G4 (em dash) moves to the stack linter recipe. `gate_rules.py` and `state_record.py` stay trimmed because `promote.py` (size L archive, no longer runs `--final`) still reads them. Config keys `forbid_em_dash`, `pack_budget_lines`, `plan_budget_kb` are gone. prd-flow: the surveyor runs only for rule changes (`full`, `short`), the chief may run gates and git, one return format, a task is one line, no deliveries ledger, `Self-check:`, `Red:`, dispatch ledger or `state.md` sections of other agents; the executor has no grep-all-docs step and no hard-coded runner; `prd-flow-docs` runs on sonnet. `scripts/close_gate.py` must drop its `docs --final` step.

## Read before edit, done means stop

Audit of 2026-10-15 (`eval/audit-2026-10-15-paper/FINDINGS.md`): 409 edits were refused in two days, 93% of them after the agent had read the file with `cat`, `sed` or `grep`, which the harness does not count as a read; failing test streaks reached 4 to 6; 10 to 18% of executor calls came after the last product edit. Rules: CR23 (new), CR08 and CR16 (amended).

- `global/CLAUDE.md` "Editing": read with the Read tool before editing, batch independent reads, one pass of changes per file, Write the whole file after a full Read when most of it changes.
- `global/CLAUDE.md` "Executing" and "Tests": a subagent prompt carries the done condition and the agent stops verifying there; a test that fails the same way twice is reported as a gap.
- `prd-flow-docs` runs on sonnet (CR09); the surveyor keeps opus for conflict judgment.
## Core rules, slice K4a: the per-commit gates of the scripts and templates are gone

The core rules (CR01 to CR22, [rules/core.md](rules/core.md)) made these gates unnecessary; each cost work on every commit or task and none prevented a measured defect (`proposals/audit-rules-cost-2026-10-14.md` section 5). The prd-flow skill and agents are a separate slice. Rule: MAINTAINING M09 and M14.

- Ratchet: `duplicate_names`, `crowded_dirs`, `no_prd_id`, `long_feature_maps` and `invariant_gaps` are deleted, and so are the `limits.feature_map_lines`, `limits.id_header_lines`, `limits.files_per_dir` and `id_pattern` keys. The allowlist is a list of files per check, not counts: a file may change size; a listed file that no longer violates only warns. `banned_names`, `long_modules`, `long_tests`, `no_feature_map`, `generated_without_marker` and `skill_md_bytes` stay.
- `scripts/commit_trailers.py`, `gates.sh trailers` and the CI trailers job are deleted; `gates.sh red`, `watch`, `prd-sweep`, `settings-check` and `context` are deleted; `gates.sh close` runs lint, the docs gate and the compare result (no trailers, no retro; `gates.sh retro` still runs on request).
- Guard hook: a redirect, `cat >` or `tee` is denied only when its target is under `source_dirs` of `ai-kit.json` or `docs/`; git-destructive, stdin interpreter, heredoc and kill-by-name denials are unchanged.
- `verify.py`: the default ref finds `changes/<slug>/plan.md` as well as `changes/NNN-<slug>/plan.md` (a slug without a number was never matched).
- Templates: `docs/code-structure.md` AR02 without name uniqueness, AR06 without the ID header, AR07 without the per-commit map duty, AR23 as review, AR24 parameters 7, AR03 class limit exempts declarative classes; `AGENTS.md` and the constitution drop the trailer, `Request:`, `Assumed:`, `Red:`, `Rules:` and promote duties and the "Every module and test cites" line. Stack recipes: `max-params` 7 and one per-test timeout config line each. MAINTAINING M09 extended.

On update: run "Migration to the core rules gates" of `/ai-kit update` (U6k): drop the removed allowlist keys, turn counts into file lists, delete the trailers job from `ci.yml` and the three deleted scripts.

## Preamble diet and its meter

Audit of 2026-10-15 (`eval/audit-2026-10-15-paper/FINDINGS.md` H01): every session started at about 83k tokens and every subagent at about 55k before doing anything, about a third of all tokens processed. The template `CLAUDE.md` and `AGENTS.md` said the same rules twice. Rule: CE18 (amended).

- Template `CLAUDE.md` keeps the project line, the constitution index, the product rules flow and `@AGENTS.md`; template `AGENTS.md` has one "Working rules" section and the code structure, with no sentence repeated. Together 10.6 KB instead of 17.0 KB.
- New `scripts/preamble.py` and `scripts/gates.sh preamble`: the fixed context by part (repository instructions with their imports, agent and skill descriptions, the user's global file, the memory index) against the new `ai-kit.json` `preamble` budgets; the doctor reports each part over budget.
- `/ai-kit update` gains a "Preamble diet" step: one home per rule, daily commands only, short agent and skill descriptions, large task-specific sections moved to `docs/`.
## Post-tool hook: lint after edit, failing streak, checkpoint

Audit of 2026-10-15 (`eval/audit-2026-10-15-paper/FINDINGS.md` H02, H06, H08): lint was a manual call, failing test streaks reached 4 to 6, orchestrators ran at 216k to 667k context. The paper's harness puts post-edit diagnostics and stuck detection inside the loop. Rule: TM18 (new).

- New `scripts/post_tool_hook.py`, registered in `.claude/settings.json` on `PostToolUse` and `PostToolUseFailure`. It never blocks; it adds text next to the tool result: the lint findings of an edited code file (`commands.lint_file`), a warning at 3 consecutive failing test runs of one agent and a hand-back at 5, and one checkpoint per session when the main thread passes 150k tokens.
- New `ai-kit.json` `post_tool` section (`lint_after_edit`, `lint_timeout_s`, `streak_warn`, `streak_stop`, `checkpoint_tokens`); the doctor checks the registration and the hook's error log.

## Core rules: one slice per delivery, fewer and clearer rules

Run of 2026-10-14 (LS35): a widened scope with no estimate ran 3 hours of execution with 19 subagents and no PR; about 40% of the calls were re-orienting, every lane left leftovers that became new lanes, and three High findings were design gaps found after the code. The rules that would have stopped it existed but were buried among 434 IDs. Rule: [rules/core.md](rules/core.md) (CR01 to CR22) is the set in force and wins over the domain files; MAINTAINING M14 keeps it small.

- `global/CLAUDE.md` rewritten around the core rules: an estimate before the first dispatch or edit; one vertical slice per delivery (about 30 files or 2 hours, its own PR); defects shipped as small fixes before any restructuring; a design review before the plan for size L; one code path behind a flag at the edge; the session that executes a slice writes the code, subagents only for review, an independent slice (at most 2) or heavy reading; a running total of minutes with a report at each slice end and at 1.5 times the estimate; no lane for leftovers without the person; tests related to the touched files before handing back, with a per-test timeout; TRD and maps once per delivery.
- Template `CLAUDE.md`, `AGENTS.md` and constitution: principle V is now "Bounded Delivery"; the TRD and area maps are updated once per delivery; executors run the related tests of their files, not only their own new test; the subagent return is 15 lines with the minutes used; the 50-call ceiling is gone, an agent hands back past about 150k tokens.
- Not in this release: the per-commit gates the core rules make unnecessary (exact counts and uniqueness in the ratchet, per-edge import allowlists, module ID headers, trailers, docs-gate bookkeeping codes, prd-flow card and sheet format checks) still run; they are removed in the next releases (`proposals/audit-rules-cost-2026-10-14.md` section 5).

On update: replace the managed block of `~/.claude/CLAUDE.md` with `global/CLAUDE.md`; in the repository, apply the `CLAUDE.md`, `AGENTS.md` and constitution lines above where the project kept the kit wording.

## Rule as data: the rows land with the code, the commit body is the record

An A/B of the docs flow (`proposals/plan-rule-as-data.md`) showed the docs agent, promote and the bookkeeping gate cost more than they protected: promote left stale values behind ("today: 60 s") and the change gate failed 36% of runs on bookkeeping. Rule: the approved PRD rows are written in the commit of the task that implements them, and the commit body (`Request:`, `Decided:`, `Assumed:`, `Red:`, then `Rules:`) is the record. Amended: the docs rules DS and the workflow rules WF that named promote, Planned or a CHANGELOG line ([rules/](rules/README.md)).

- Gate (S3, S4, S6): six change-gate errors (unique IDs, complete row, cited ID exists, changed rule has a test, no em dash added, INDEX current); G7 and the hand-edited INDEX IDs column are gone (`gen_index.py`, `gate.py --fix`); the default gate checks no HTML (only `gate.py --html`, run by `/docs-html`); `gate.py --history <ID>` prints a rule's history from git.
- Flow (S1, S2, S7, S8, S10): no docs `apply`, no promote, no `pending code` marker or TRD `Planned` section for size S and M; `CHANGELOG.md` is frozen (kept, never appended) and `decisions.md` is for size L only; implementation always goes to the executor agent; size L keeps `plan.md` and `decisions.md`, the rows still land with the code.
- Promote (S1, D4): `promote.py` only archives `changes/NNN-<slug>` for size L when there is no CHANGELOG entry and no state record; it still reads a CHANGELOG entry or state record that already exists, so a `pending code` marker already in a PRD keeps closing. No new change adds one. `close_gate.py` no longer expects promote's output for S and M.
- Baseline (S9): ANSI stripped before the summary match; the suite copy lives under `<repo>/.ai-kit/tmp`.
- Eval (S11): `docs-flow-eval` ships in the kit and `MAINTAINING.md` M07 points to it.
- Tests: the ones pinning G7 and the promote-for-every-change route were inverted or rewritten (see the commit body).

On update: run "Migration to rule as data" (U6h of `installer/ai-kit/reference/update.md`): the frozen note under the title of `docs/prd/CHANGELOG.md`, the constitution sentence, the CLAUDE.md and AGENTS.md lines; existing markers, CHANGELOG entries and open change folders stay as they are. The eval found that without the note a reader concludes no decision was recorded (4.5 of 5; 5 of 5 with it).

## Orchestration rules for every session, with or without prd-flow

Audit of the 2026-10-13 sessions (LS34): the slow part was the orchestration pattern, not prd-flow. One Opus session ran audit to 100 dispatches at 540k tokens of context per turn; 47 one-finding tasks in 12 waves, each wave reviewed twice; the cross-repo defects surfaced only in a final review that cost 47 minutes more; two "stuck" agents were foreground evals on a 580 s timeout. Rules: new SA60 to SA66, amended SA40 (one review per delivery) and SA41 (checkpoint for every orchestrator) ([rules/02-subagents.md](rules/02-subagents.md)).

- `global/CLAUDE.md`: new section "Orchestrating a delivery" (one phase per session, scope in three lines before the first dispatch, area-sized tasks, item map, one cross-repo review per delivery, evals and long suites only in the background from the orchestrator). It is the always-loaded home, since prd-flow now runs only on `/prd-flow`.
- prd-flow: `run.md` "Review", `write.md` "Plan" (`Review: once after the last wave`, area-sized cards, the Item, Task, Test map), SKILL.md wave end, `prd-flow-reviewer.md` description.

## prd-flow runs only when the person types it

prd-flow was a mandatory gate the model started on its own for every behavior change, so small, already clear changes paid the whole flow. It now runs only on an explicit `/prd-flow`. Rule: amended WF01 ([rules/07-workflow.md](rules/07-workflow.md)).

- `kit/.claude/skills/prd-flow/SKILL.md`: `disable-model-invocation: true`, and the description says it runs only when the user types `/prd-flow`.
- `kit/CLAUDE.md` "Product rules flow", `kit/AGENTS.md` "Workflow" step 1 and the constitution template "Development Workflow" item 1: no longer route every change through prd-flow. Without it, a rule change is still confirmed by the person and updates PRD and TRD in the same delivery as the code.

## prd-flow lite: same guarantees, a fraction of the transport

Audit of 2026-10-09 (`eval/AUDIT-prd-flow-end-to-end-2026-10-09.md`, LS33): a plain session beat prd-flow because prd-flow moved understanding through cold agents and copies. The docs phase wrote 394k output tokens against 123k for all executors, a real C5 dispatched 89 agents and took 2 h 20 min to the first code, 3 executors stayed alive about 766 min and one session held 3.7 GB of task output. Plan `proposals/plan-prd-flow-lite.md`. Rules: new SA58, SA59, WF83, IN20, IN21; amended SA05, SA07, SA15, SA22, SA37, SA44, SA53, SA54, SA55, SA56, CE27, CE29, RV03, RV08, RV10, WF21, WF26, WF27, WF38, WF39, WF41, WF43, WF44, WF47, WF51, WF57, WF61, WF68, WF70, WF72, TS34, TS45, TS51, TM03 ([rules/](rules/README.md)). Every orchestration rule is kept (chief, parallel waves, warm resume, review cap, batch verification, reap); what goes is transport.

- Retired: the references `classification.md`, `impact.md`, `interview.md`, `prd-writing.md`, `trd-planned.md`, `agent-plan.md`, `execution.md` and `review.md` (nine references become five: `dispatch.md`, `survey.md`, `sheet.md`, `write.md`, `run.md`, plus `repo.md`; the map is `proposals/lite-reference-map.md`); the rendered state record (`rules.md`, `approved-rules.md`, `answers.md`, `state_record.py render`); the `interview.md` file; the gate checks Q4 and P11 to P16; `brief.md` and the TRD Planned section for size M; the three docs commits (one `docs(prd)` commit now); the `general-purpose` dispatch fallback; the agent frontmatter `hooks:` blocks (the guard is registered in `settings.json`, SA56).
- Added: `gates.sh prd-sweep` (the surveyor starts from a script: literal rows, citing rows, candidates by INDEX terms, CHANGELOG history, tests, callers; surveyor calls 37 to 118 down to about 20 to 35), `gates.sh cleanup` (reap by PID tree, this session's task outputs, loose run files, stale state folders; run at the start and end of every case, last in `close`, and from a `SessionEnd` hook), `gates.sh watch` (per-wave watchdog that wakes the chief when an agent has been silent 10 minutes), `guard_hook.py` registered in `settings.json` for every subagent, `ai-kit.allowlist.json`, task cards with `Why:`, the decisions record with the user's reply verbatim.
- Changed: surveyor model by mode (`query` and `light` on sonnet, `full` and `short` on opus); `promote.py` and the gate read the approved set from the `IDs:` line of the CHANGELOG entry; gate output to agents is errors only plus one warnings line; a fix goes to the warm executor and the recheck to the warm reviewer; subagents never use `run_in_background`; ceilings of 80 calls for surveyor `full` and docs `apply`; hook commands carry the interpreter resolved at install; `ai-kit.json` drops from 58 to 115 KB to under 10 KB.
- Evaluation: `eval/` gets the `PLAIN` and `LITE` arms beside `FLOW`; the plain arm is mandatory in every round (MAINTAINING.md).
- Targets on the next real C5 of size M: at most 12 agents (was 45 to 89), docs output under 0.6 of code output (was 1.2 to 3.2), first executor under 15 min after the answer (was 40 min to 2 h 20 min), no agent past 150k, nothing left alive or on disk (was 3.7 GB). Not yet re-measured.

On update: run the prd-flow lite migration (`reference/update.md`, U6g): remove the eight retired reference files, and the `hooks:` block of the five agents; copy `ai-kit.allowlist.json` and move an `allowlist` key of `ai-kit.json` into it; merge the `guard_hook.py` `PreToolUse` entry and the `SessionEnd` cleanup entry into `.claude/settings.json`; replace hook commands that probe the interpreter by the kit's, with `__AIKIT_PYTHON__` filled by the interpreter resolved as in install; a state folder with `approved-rules.md` keeps the old route until its change closes.

## one-pass interview: one decision sheet, no orphan agents

Lessons of the runs of 2026-10-09 (LS32): the interview and docs cost 2.06M tokens against 1.72M for the code, 14 of 19 interactions came before any code, and heredoc orphans left about 230 stuck agent-minutes. Rules: WF10, WF14, WF15, WF42, WF43, WF47, WF67 to WF69, WF75 to WF82, CE12, CE27, CE29, WS08 to WS10, SA56, SA57, TS54, TM17, IN19 ([rules/](rules/README.md)); meta-rules M08 to M13 in MAINTAINING.md.

- Interview: the surveyor writes `pack.md` and `sheet.md` only; the chief prints the sheet verbatim and ends the turn; the user answers in the chat in free text by number (`ok` takes the recommended defaults); docs `apply` writes `answers.md`, `rules.md` and `decisions.md` once; one follow-up sheet at most, then open items become visible `Q-` rows. The 16 dimensions, round 0, the separate change question, the question lint (Q6 to Q9) and the modes `rules`, `prd-plan` and `trd-plan` are gone. What the user already said in the conversation reaches the surveyor as `Decided in conversation:` and `Preferences:` and becomes assumed lines, never decisions.
- Gates: `gate.py --sheet <slug>` runs the sheet lint S0 to S6; Q3 checks that every sheet item has an answer and that no mechanism (env var, flag, key, table, endpoint, column) appears that the sheet or the answers do not hold; `--questions` is an alias for one release. `promote.py` writes one CHANGELOG entry per slug.
- Orphans: `scripts/guard_hook.py` is a blocking hook declared in the frontmatter of the five `prd-flow-*` agents (not global); `gates.sh reap` kills leftover session processes by tree, never by image name; the telemetry hook writes `agent_stuck` and `gates.sh verify` prints `stuck agents`. One interpreter (`gates.sh python`), commits from a message file with `git commit -F`, one command per call, long commands in the background.
- Tools: `gates.sh fix-files`, `lint-files` (executors format and lint their own files) and `move`; `scripts/next_change_number.py` reserves the change number across parallel slugs; `scripts/settings_check.py` and new doctor checks read the harness settings.
- One home per rule: the orchestration rules live once (SKILL.md, `dispatch.md`, `interview.md`, `review.md`, `execution.md`); the full suite starts once as `compare` during the last review; Medium findings ride along in a fix without counting a round.

On update: in `repo.md` Gate config drop `question_lint` and add `sheet_labels` (the localized section and field labels of the sheet, default English); add to `ai-kit.json` `commands.fix_file`, `commands.lint_file`, `tests.summary_regex`, `tests.fast_flags`, `tests.test_dirs` and `tests.related_exclude`; the new scripts `guard_hook.py`, `reap.py`, `next_change_number.py` and `settings_check.py` are copied by the update, and the guard hook is declared in the `hooks:` frontmatter of the five prd-flow agents (nothing to merge into `.claude/settings.json`). A state folder from an old run finishes on the old route only if it already has approved rules; otherwise run the survey again. Deferred (D1 of the plan): the PRD pending marker and the TRD Planned section stay, because promote, `--hold` and the TRD path gate read them. The eval round of the plan (wave 4) was not run, so the targets (at most 2 touchpoints before code, no stuck agent minutes) are not yet measured.

## run speed: one baseline, verification per batch, no polling

Lessons of a 432 minute run (LS31). Rules: TS43 to TS53, SA48 to SA55, CE29, RV18, WF65 to WF74, DS46, IN17, IN18, TM14 to TM16 ([rules/](rules/README.md)).

- Tests: `gates.sh baseline <slug>` (a background Bash of the chief) runs once per plan commit in a git worktree, cached by commit and lockfile hash, with a lock and a no-progress watchdog; `gates.sh close` fails when it was never started. `related` is exact (full dotted import path, capped, args file), skips an unchanged selection and always adds `tests.always`; `gates.sh red <test>` proves the red step; `gates.sh python` prints the one interpreter `gates.sh` resolves (`commands.python`). Verification is per batch (TS53): executors run only their own new test, the chief runs one `gates.sh verify <slug>` per wave while the reviewer reads the diff, the findings go into one batched fix and close reuses the verification. Gates are reminders (warnings) run once per phase, including the plan gates P12 to P17.
- Gates: `gate.py --docs <slug>` (and `gates.sh docs`) runs the docs checks in one cached process; `--final --change <slug>` and `--snapshot <slug>` keep older drift out of a close; `--questions` lints prepared questions (Q6 to Q9); the plan gate checks alignment and `Reached from:` (P11 to P17); `promote.py` reads markers from `repo.md`, takes `--hold` and fails on a delivered rule without Source.
- Protocol: new `reference/dispatch.md` (premise rule, background by default, resume with SendMessage, dispatch ledger, delta re-survey, cross-repo mode with `.ai-kit/repos.json`); round 0 confirms the domain model; the state record is `rules.md` plus `delta.md` with `interview.md`, `approved-rules.md` and `decisions.md` rendered from it; one batched fix per review round; executor self-check and `Red:` line.
- Hooks: no guard hook (the hooks spawn a process per tool call, about 4,374 in the run); SA51 and SA53 are behavior guidance in the agent files (Edit and Write to edit, Read and Grep to read, never `git stash`, `reset` or `checkout` in a shared tree). Every hook launches from `CLAUDE_PROJECT_DIR`, honors `commands.python` and fails open.
- Telemetry: events carry `repo`, agent fields, `bg`, `timeout`, `wait_ms`, `dur_ms`; new retro detectors `poll_calls` (a sleep inside a loop only), `bg_alive_at_return`, `no_timeout`, `baseline_in_agent`.
- Install and update verify `tests.failure_regex` on a real failure line and check `rg` on PATH.

On update: add to `ai-kit.json` `commands.python` `""`, `tests.baseline_deselect` `[]`, `tests.baseline_idle_seconds` `300`, `tests.always` `[]`; add `plain_words`, `plan_strict` (`no`), `question_lint` (`warn`) and `shared_files` (empty) to the `repo.md` Gate config; merge the launcher hooks into `.claude/settings.json` keeping the project's own (replace a hook that runs `python scripts/telemetry_hook.py`) and remove the guard hook entry (`agent_guard_hook.py`) if present; (G5) add the junit flag to an installed `tests.runner` for the stack (pytest `--junitxml=reports/junit.xml`, the jest or vitest junit reporter) and, for node, `tests.baseline_deselect_flag`. Project-owned values to set by hand: `tests.baseline_deselect` (a test that hangs offline), `tests.always` (the structure tests), `tests.junit_xml` per stack (`reports/junit.xml` for python and node), and a mangled `tests.failure_regex` fixed from the recipe (for example `^FAILs+(S+)` to `^FAIL\s+(\S+)`); optional, after a rendered preview, `html_mode: generated`.

## docs-html: the HTML leaves the change flow

prd-flow, prd-create and trd-create write markdown only; a new `docs-html` skill rebuilds the PRD and TRD reading pages when someone wants them (DS45).

- New skill `.claude/skills/docs-html/` (its `reference/html.md` moved from prd-create). It runs `scripts/gates.sh html` and the strict `gate.py --html`, then commits the pages alone. Generated mode only.
- New TRD reading page `docs/trd/trd.html`, built by `build_trd_html.py` from `docs/trd/` and `docs/flow.md` with the same template (`repo.md` key `trd_html`).
- The docs agent no longer builds the HTML in `prd-plan`, `c4` or `merge`; `promote.py` no longer rebuilds it; the prd-create `html-writer` step is gone (the `index-writer` commits).
- Gate: a stale page is a WARNING by default and in CI (G29 PRD, G32 TRD); `--html` makes it an ERROR. `html_mode: hand` is no longer checked row by row (G6 and G10 removed): one G5 warning until migrated.
- `docs/templates/prd.html` gains slots for the page labels; the PRD page renders byte for byte as before.

On update: run the "Migration to docs-html" table of `installer/ai-kit/reference/update.md`; add `trd_html` to the `repo.md` Gate config; then offer `/docs-html` once.

## prd-flow gate: localized rule tables

A project whose PRD is not in English passes `--trace` with the same rules it passed before.

- `repo.md` Gate config `via_header` (default `Change via`): the last header column of a rule table. Only rows of those tables are rules for G3, `--trace` and `--status`; IDs in other tables (open questions, glossaries) need no test.
- G11 accepts a bare file name or a partial path in Source when it matches the last whole path segments of a tracked file.

On update: add `via_header` to the `repo.md` Gate config, filled with the header the project's PRD rule tables use; replace the prd-flow scripts.

## prd-flow v6: the main thread is a chief

The main thread of prd-flow, prd-create and trd-create coordinates and executes no task. Rules: SA43 to SA47, WF64, LS29 ([rules/](rules/README.md)).

- Chief: asks the user, dispatches agents and routes their returns; reads only `state.md` and `repo.md`, runs no script, gate, test or git command, and never fixes or verifies an agent's work. Every case starts with the surveyor.
- Return contract: every agent ends with `Status`, `Files`, `Commit`, `Route`, `Next`; each failure has an owner role and mode (gate red, promote or close error, review finding, ceiling).
- prd-create and trd-create: a `scoper` worker (plus an `interviewer` for greenfield PRDs) takes the reads and the outline from the main thread; the last writer commits.
- Agents commit their own work; the executor `close` mode runs `promote.py` and `scripts/gates.sh close`. No script was added.
- State: `state.md` has one writer per section and deliveries are one file per task (`deliveries/<task>.md`).
- `CLAUDE.md` and `AGENTS.md` of the kit say the main thread coordinates and no longer tell it to run `promote.py` or the closing gate.

## prd-flow v5

The rule-change flow is cheaper to run and harder to skip: the roles are defined subagents, the main thread keeps a thin contract, waves and promotion are computed by scripts, and a new rule that contradicts a live one must be resolved in the same change. Rules: SA27 to SA42, CE23 to CE28, DS44, WF58 to WF63, LS28 ([rules/](rules/README.md)).

- Agents: `.claude/agents/prd-flow-{surveyor,docs,executor,reviewer,recheck}.md` carry the briefing, the pinned model and the minimum tools; `reference/workers/` is gone and one docs agent replaces writer-prd, writer-trd and the planner. No agent is resumed and no tool is loaded mid-run.
- Main thread: a thin card with an allowed and a forbidden list, counted as `main_violations`; the interview and the single `gate.py --rules` run at step 4; step 6 is skipped when `--applied` is green and nothing outside the tables changed.
- Plan: granularity by the critical path, context affinity, waves and the Owns overlap check printed by `gate.py --step plan`, a task card of at most 25 lines, one reviewer per wave, a checkpoint to a fresh session, and an optional execution session on the fast model.
- Conflicts and rewrites: sweep K14 and gate Q5 fail until each conflict is resolved; a rewritten rule keeps its ID.
- Scripts: `promote.py <slug>` fills Source from the `Source: <ID> <path[::symbol]>` lines of `deliveries.md` and archives the change; `scripts/gates.sh close <slug>` runs the suite against the baseline, lint, trailers, the final gate and the retro in one call; `gates.sh html`.
- Telemetry targets: 30 main calls, 0 inline reads, 2 main gate runs, parallel factor 1.5 (`kpi_*` keys of `ai-kit.json`).
- Evaluation: `eval/arms-big.json` (arms GATE, FLOW, FLOW-FAST; S5 at 3 reps, S6 to S8 at 1) and the scorecard of `eval/METRICS.md`.

On update: add the five agent files, delete `.claude/skills/prd-flow/reference/workers/`, take the new `reference/`, `scripts/` and `ai-kit.json` `telemetry` keys (shown as diffs), and add `prd_section_budget_lines` to the Gate config of `repo.md`.

## prd-flow v4

The `prd-gate` skill is now `prd-flow`, and the rule-change flow checks conflicts, gaps and the interview itself instead of trusting the conversation. Rules: WF35 to WF52, DS32 to DS43, PC13, PC14, IN14 to IN16, TM13 ([rules/](rules/README.md)).

Migration: `/ai-kit update` moves `prd-gate` to `prd-flow` (shows the list first; moves your `repo.md` and the state folder; replaces the old name in the files the kit manages). Hand-made `prd.html` files keep working (`html_mode: hand`) until you accept the generated version after a preview.

On update: move `.claude/skills/prd-gate/repo.md` to `.claude/skills/prd-flow/repo.md`, delete `.claude/skills/prd-gate/`, move `.claude/prd-gate/state/` to `.claude/prd-flow/state/`, replace `prd-gate` with `prd-flow` in CLAUDE.md, AGENTS.md, the constitution, `.claude/settings.json`, `.gitignore`, `ai-kit.json`, `docs/prd/README.md`, `docs/trd/` and `docs/templates/` (each as a shown diff), rewrite the manifest paths, add the new `repo.md` sections (Rule owners, Shared PRDs) and Gate config keys, add `.github/CODEOWNERS`, and propose contract snapshots when a sibling consumer is listed.

Workflow
- C0 only when `docs/prd/INDEX.md` does not exist; a new product, module or incoming spec in a repository with PRDs is a C5 of size L, swept against every existing PRD.
- Rules that come only from documents are `*(proposed)*` and go through confrontation and interview before they count; `--final` fails on a leftover one.
- New sweeps: K11 (rules in other sections that interact, found by meaning, with `Checked:` and `Conflicts:`), K12 (history of the rule in the CHANGELOG), K13 (rule owner and shared PRD), and remote branches for ID and change-number collisions.
- Assumed defaults are shown to the person in one block and confirmed; dimensions are `doc`, `assumed`, `open` or `n/a`.
- The PRD is confirmed (rule diff plus a summary of the non-table changes) before the TRD is written.
- R09: any behavior not covered by the approved rules, from anyone, goes through the short C5 before code. Ceilings of agents have one home (V08).
- `decisions.md` per change records the trade-offs decided and the alternatives rejected; rule owners are named when a change touches their section; commits carry `Rules:` or `Case: none (...)`.
- C1 answers say whether each rule is verified in code.

Gate
- `--rules` fails Q3 when the interview record is not closed; `--rules --applied` fails Q4 when the PRD differs from the approved rows.
- `--trd` (G23 to G26: cited paths and symbols exist, IDs match, size budget), `--status` (state per rule), `--sibling` (G28, shared PRDs identical), G27 (remote collisions), G30 (proposed rule left at `--final`).
- `gate.py` is split into modules named after their responsibility; `repo.md` Gate config gains `proposed_marker`, `html_mode`, `html_template`, `trd_budget_lines`, each with a default.

PRD and TRD formats
- Optional `Example` column in rule tables (`<given> → <expected outcome>`).
- TRD "Planned" is a slim table (file, changes or creates, symbols, IDs) with no values; the TRD has no History section; large TRD files split into parts; amendments are folded into their sections on promotion.

HTML
- `prd.html` is generated from the markdown by `build_prd_html.py` (tabs, toc, callouts, Example column, diagrams, decisions tab, light and dark, phone width); G29 fails when it is out of date.

Scripts
- `scripts/commit_trailers.py` and `gates.sh trailers`, run in CI on pull requests; the ratchet counts invariant gaps (`allowlist.invariant_gaps`, shrink-only); the retro reports the most-read docs (`doc_reads`); a CODEOWNERS template owns `docs/prd/**` by the rule owners.

Installer
- Update migrates `prd-gate` to `prd-flow` and, after a preview, a hand-made HTML to the generated one; install fills CODEOWNERS and proposes contract snapshots when a sibling consumer is listed.

Eval
- Scenarios S5 to S7 (conflict in another section, incoming spec, unanswered dimension) and `eval/arms-flow.json` compare the old and the new skill on the same runs, with the metrics `conflict_found`, `contradiction_left` and `gap_recorded`.

## Unreleased

Adoption in an existing repository: the kit installs without losing the project's docs language, TRD heading, gates script or structural test.

- prd-gate repo.md Gate config: `language` (default English) for the PRD, TRD, interview and gate output, read by R03 and `reference/workers.md`; `planned_heading` (default `Planned`) read by G8 and G20.
- `scripts/gates.sh` delegates to `scripts/gates.project.sh` when it exists: targets the kit does not define, and targets in `ai-kit.json` `commands.project_targets` (default `[]`), run there with their arguments.
- `scripts/ratchet.py`: `ai-kit.json` `ratchet.skip` (default `[]`) names checks to skip (`long_modules`, `long_tests`, `banned_names` or its alias `generic_names`, and the others `--init` prints); install.md says to skip the checks a project's own structural test already covers.
- prd-gate `reference/impact.md`: rows K01, K05 and K06 restored (K06 pointed at K01's text).
- prd-gate G3: the Source and Change via checks apply only to tables whose last header column is "Change via", so open-question tables no longer warn once per row.
- prd-gate G6: text inside markdown code spans (for example `<fileKey>`) is no longer stripped as an HTML tag, so it matches the escaped placeholder in the HTML.
- `docs/templates/prd.html`: explicit grid tracks (`minmax(0,1fr)`), so wide tables, mermaid diagrams and long tokens wrap or scroll inside their box and the page never exceeds 100% width.
- On update: add `language` and `planned_heading` to the `repo.md` Gate config table, filled from the project's existing docs (language of the prose, the TRD heading in use) and not from the defaults when they differ; add `commands.project_targets: []` and `ratchet: {"skip": []}` to `ai-kit.json`; copy `scripts/gates.sh` and `scripts/ratchet.py`; when the project has its own gates script or structural test, rename it to `scripts/gates.project.sh` and list its targets in `project_targets`, or list the overlapping checks in `ratchet.skip`; copy `docs/templates/prd.html` into the project's `prd.html` only by proposing the CSS diff.

Run telemetry: every run leaves summarized artifacts and a retrospective names what was slow, expensive, looping or wasteful.

- Hooks record tool calls, subagents, compactions and waits to `.ai-kit/runs/<context>/` (git-ignored); `gates.sh` test and build targets go through `run_probe.py` for time, memory and disk; `gates.sh retro` writes `retro.md` with findings only past the thresholds of `ai-kit.json` `telemetry`.
- prd-gate: step 1 runs `gates.sh context <slug>`; E20 runs the retro after the full suite and the final report lists the findings or says the run stayed within every threshold.
- Rules TM01 to TM12 in `rules/11-telemetry.md`.
- On update: copy `scripts/telemetry_hook.py`, `scripts/run_probe.py` and `scripts/retro.py`; merge the kit's hooks into `.claude/settings.json` keeping the project's own; add the `telemetry` section to `ai-kit.json` with the defaults; add `.ai-kit/runs/` to `.gitignore`.

AI readiness in any layout and any language: feature folders become a recommendation, every other technique applies to any folder structure (layers, legacy code, modules, mixes or anything else), and the kit gains the readiness techniques it was missing.

- Layout declared in `ai-kit.json`: `layout`, `areas` (product area to globs), `map_dirs` (folders that carry a `CLAUDE.md`), additive with `feature_root`. The ratchet checks IDs on area files and maps on map folders, and fails on an area or map folder that points nowhere. Configs without the new keys behave as before.
- Rules AR01, AR02 to AR07, AR10, AR11, AR13, AR19, DS15, TS16, PC09, CE07 rewritten layout and language agnostic; new AR20 to AR28 (layout optional, extract on touch, greppable wiring, crowded folders, complexity, dead code, duplicates, gradual typing, generated files), TS37 to TS42 (time budget, flaky list, snapshots, parallel-safe tests, builders, characterization tests), CE22 (search noise), DS30 (schema and contract snapshots), DS31 (pattern to copy), PC11, PC12, IN11 to IN13. MAINTAINING M06: every rule has a text-level part, a recipe part and review as fallback.
- `related_tests.py`: mirror names from `tests.mirror_patterns` (`OrderServiceTest`, `order.service.spec` and the like), `tests.match_symbol` for languages whose imports name namespaces or autoload, namespaced imports with backslashes, wall time against `tests.related_budget_seconds`, slowest tests from `tests.junit_xml`, a warning when snapshot files change.
- `ratchet.py`: `crowded_dirs` (`limits.files_per_dir`) and `generated_without_marker` (`generated_patterns`); generated files skip the other checks. `new_failures.py` lists `tests.flaky` failures without counting them.
- New `scripts/hotspots.py` and `scripts/contract_drift.py`; `gates.sh` gains `setup`, `hotspots`, `contracts`.
- trd-create: N4 is now the incremental readiness plan (`reference/readiness.md`) in the current layout; the move to feature folders is N5, optional. New `docs/ai-readiness.md` checklist and `docs/templates/folder-CLAUDE.md`. Install detects the layout, asks where a new area goes, writes `.ignore` and `.claude/settings.json` (the kit's `.claude/settings.json` now carries the gate permissions next to the telemetry hooks); doctor reports readiness per area.
- Every stack recipe gains Layout, Test naming, Generated files, Framework exemptions, Snapshots, Contracts and Setup, plus the linter rules for AR22 and AR24 to AR27.
- Candidates, not rules: a formatting PostToolUse hook, path-scoped rules, a language server for navigation; each to be measured in `eval/`.
- On update: add the new `ai-kit.json` keys with their defaults (`layout`, `areas`, `map_dirs`, `generated_patterns`, `contracts`, `limits.files_per_dir`, `commands.setup`, the new `tests` keys, the `crowded_dirs` and `generated_without_marker` allowlists seeded by `python scripts/ratchet.py --init`); when `feature_root` points at the whole source folder of a layer codebase, propose `layout`, `areas` and `map_dirs` instead and re-run `--init`; copy the new scripts, templates and `docs/ai-readiness.md`; propose `.ignore`, `.claude/settings.json`, the "This repository's layout" section of `docs/code-structure.md` and the new AGENTS.md lines as a diff; fill the recipe's new sections.

Living truth plus change deltas: every fact has one living home; a change folder holds intent, plan and state, never truth.

- The kit no longer depends on spec-kit: `/speckit-*` and `specs/` are gone from CLAUDE.md, AGENTS.md, the constitution, the skills and the rule catalog.
- Change folders `changes/NNN-<slug>/` by size (S, M, L) with `brief.md`, `design.md` and `plan.md`; finished ones are archived to `changes/archive/`.
- Order of authority: constitution, PRD, TRD, code; an active plan governs only the order of work.
- The plan's `Constitution check` replaces spec-kit's Constitution Check and Complexity Tracking.
- Rules WF26 rewritten, WF27 to WF34 added; IN10 added.
- `gate.py` gains `--trace` (every rule cited by a test, shrink-only allowlist), `--change` (brief IDs exist, P1 slices owned by a task) and `--final` (no `planned` leftovers on the base branch, run by CI on pushes to it).
- Fix: `gate.py` G5 compared an absolute HTML path with repo-relative diff paths and fired on every PRD table change; G10 compared the header row of a new table with the HTML. Agents had been patching the gate by hand in 3 of 8 evaluation runs.
- `eval/`: an unattended evaluation that compares flows on a small and a large synthetic service (hidden tests, PRD fidelity judge, blind code review, tokens, subagents, errors, time, reviews), with the decision rule in `eval/README.md`.
- On update: create `changes/archive/` (with a `.gitkeep`); leave a legacy `specs/` untouched as history; add `untested_rules` to the `allowlist` of `ai-kit.json`, seeded by `gate.py --trace` so today's untested rules are listed and shrink-only; propose the new sections of AGENTS.md (Directory map, Workflow, order of authority), CLAUDE.md (Constitution intro) and the constitution (Development Workflow step 2, Governance, header comment) as a diff; fill the repo.md "Spec-kit" and "Legacy specs" lines.

Container and disk hygiene, after a day of agent work filled a Windows disk (tens of GB of background task output, a 49.5 GB Docker disk file with 19 GB in use) and a first fix still leaked.

- `scripts/docker_hygiene.py` and `scripts/clean_task_outputs.py`; `gates.sh` gains `build`, `guard`, `sweep`, `docker-clean`, `clean-outputs`. `integration`, `full` and `build` refuse on low disk or over the image caps, and clean up from an `EXIT` trap, so a failed or interrupted run cleans up too.
- The sweep removes test-labelled containers, volumes and networks older than `DOCKER_STALE_MINUTES`, so a run killed before its teardown is cleaned by the next one, and a run still going in another session keeps its stack.
- The build cache is bounded by size (`--max-used-space`), never by age: `--filter until=24h` kept everything built that day, and `--keep-storage` is now a floor, not a ceiling.
- A cap over all images (`TOTAL_IMAGE_CAP_GB`) catches third-party pulls; a warning names the Docker Desktop disk file when it passes `DOCKER_DISK_WARN_GB`, with how to compact it.
- Labels come from a new optional `docker` section of `ai-kit.json`; without it every Docker target does nothing.
- Rules TS27 to TS36; AGENTS.md "Disk and container hygiene"; testing template "Containers"; the Python recipe's "Containers" section; the global block's "Docker and disk"; install detects Docker and doctor reports drift.
- On update: copy the two scripts and `gates.sh`; when the project uses Docker, add the `docker` section and wire the recipe's "Containers" section (labels, `purpose` from the environment, session sweep, guards before builds, failing teardown); propose the AGENTS.md section and the testing.md rows as a diff; refresh the global block.

## 2026-10-04

First release, extracted from the production AI service where the rules were built and measured.

- `/ai-kit` installer with install, update and doctor modes; `install.sh` and `install.ps1` for the global skill and block.
- Skills `prd-create`, `trd-create`, `prd-gate` and `adr`.
- Docs system: PRD by section with rule rows and an HTML reading version, TRD by feature, invariants, testing guide, end-to-end flow, ADRs, templates.
- Stack-free scripts: `gates.sh`, `ratchet.py`, `related_tests.py`, `new_failures.py`, `move_lines.py`, with end-to-end tests.
- Stack recipes for Python, Node, Go, JVM, .NET, Rust, Ruby and PHP, plus a generic path.
- CI with the offline gate, the docs gate, the ratchet, a secret scan and an automated Claude review.
- Rule catalog with every rule, its reason and where it lands.
