# Maintaining the kit

The kit is the source of the rules; projects receive them through `/ai-kit update`. A rule improved inside one project and never brought back here is lost to every other project.

## Principles
| ID | Principle |
|---|---|
| M01 | Rules are proven in a real project before they enter the kit. A candidate that was never measured goes to "Candidates" below, not into the skills |
| M02 | Every rule lives in one place in the kit and is cited by ID elsewhere. The catalog in `rules/` says where it lands |
| M03 | Skill files stay lean: `SKILL.md` holds phases and rules, details live in `reference/` behind IDs, examples are marked illustrative |
| M04 | Nothing in `kit/` names a stack. Stack knowledge lives only in `stacks/` |
| M05 | Everything is in English, tables over prose, no em dash |
| M06 | Every new rule has a text-level part (works in any language), a recipe part when it needs syntax (`stacks/`), and review as the fallback when no tool exists |

## Bringing an improvement back from a project
1. Write down what happened and what it cost (time, tokens, rounds); that becomes the "Why" of the rule.
2. Add or change the rule in the matching `rules/` file, with the next free ID.
3. Change the skill, template or script that enforces it in `kit/` (or `installer/`, `stacks/`).
4. If it changes a script, add or update a test in `tests/` and run `python -m unittest discover -s tests`.
5. Commit with Conventional Commits (`feat(prd-flow): ...`, `fix(scripts): ...`, `docs(rules): ...`) and add a line to `CHANGELOG.md`.
6. In each project: `git pull` here, `./install.sh`, then `/ai-kit update`.

## Adding a stack recipe
Copy the section layout of `stacks/README.md` "Recipe format". Every command in a recipe must have been run in a real project of that stack. Add the recipe to the table in `stacks/README.md` and in the root `README.md`.

## Evaluating the skills
The skills are interactive, so the evaluation is a set of headless runs, one per scenario and per version:
1. Pick 4 to 6 scenarios that cover the cases: a question (C1), a stale PRD (C4), a rule change end to end (C5), a protected rule (a per-tenant branch), a refactor (C6), and for the creators a small repository from scratch.
2. Run each scenario in its own worktree with `claude -p` (prompt through stdin), once without the skill, once with the current version, once with the candidate; record time, cost and the final answer.
3. Grade each answer against written expectations (the right case, the right IDs, no edit before confirmation, the gate green).
4. Keep the candidate only when it is at least as good on quality and not worse on cost. In the source repository this is how the worker route was measured (-48% time, -53% cost) for about US$18 of runs.

### Efficiency is the goal (M07)
A change to a skill, template or script is better only when it does at least one of these without worsening the others: fewer tokens, less wall time, better outputs, fewer errors. Every round is graded on the scorecard of `eval/METRICS.md` (headline KPIs, hard gates, supporting metrics, how a round runs, adoption), computed by `eval/run.py` per run and compared across rounds with `python eval/rounds.py <folder>:<arm> ...` (never with ad hoc scripts). The summary below is kept for reference; `eval/METRICS.md` wins when they differ.

| ID | Metric | Fields | Better |
|---|---|---|---|
| M1 | Tokens and cost | `tokens_total`, `tokens_main`, `tokens_subagents`, `cost_usd`, `cost_main_usd`, `cost_subagents_usd`, `context_peak`, `cache_hit_rate`, `output_share`, `tokens_per_task` | lower (cache hit rate higher) |
| M2 | Tasks completed successfully | `tasks_done` over `tasks_planned`, `hidden_passed` over `hidden_total`, `completed` | higher |
| M3 | Total time | sum of `wall_min` per arm | lower |
| M4 | Time per run | `wall_min`, `main_min`, `agent_min`, `cold_starts`, `min_to_docs`, `min_to_code`, `min_per_task` | lower |
| M5 | Errors and waste | `error_rate`, `error_kinds`, `gate_runs_main`, `gate_runs_sub`, `gate_fail_ratio`, `rereads` | lower |
| M6 | Implementation versus plan | `plan_coverage`, `plan_drift`, `first_pass_rate`, `review_rounds`, `blind_findings_total`, `accept` | coverage, first pass and accept higher; the rest lower |
| M7 | Output quality | `prd_fidelity`, `conflict_found`, `contradiction_left`, `gap_recorded`, `traceability`, `single_source` | per field direction in `eval/README.md` |
| M8 | Protocol compliance | `docs_dispatched`, `protocol_adherence`, `docs_first` | true or 1.0 |

Rules of a round:
- **Like for like.** A cheaper run that did less (no code, a skipped review or TRD) is not a win: compare `cost_per_accept` and `tokens_per_task`, and read M2 and M8 before M1.
- **Repetitions.** The scenario that decides (today S5) runs at least 2 reps; a single run swung a round by US$2 to 3 when the model chose another route (LS27). Report the spread.
- **Adoption.** Against the base arm: M2, M7 and M8 not worse (hard gates); on the deciding scenario `cost_usd` and `wall_min` within +10%; `tokens_main` per run at most 3.5M; every metric outside the noise band is a win or a tie in at least as many cases as it is a loss. A failed rule becomes the work list of the next round, recorded as a lesson in `rules/09-lessons.md` with the numbers.
- **Cause before fix.** A regression is explained from the transcripts (which agent, which turns, which error kind) before anything is changed; the fix cites the metric it should move and the next round checks it.

The scenarios live in `eval/scenarios/`: S1 to S4 cover the basic cases; S5 (a conflict phrased in other words in another section), S6 (an incoming spec document that conflicts with a live rule) and S7 (a dimension the decisions record does not answer) cover the confrontation and gap handling. `eval/arms-flow.json` runs S5 to S7 on the small fixture with the previous skill (arm GATE) and the current one (arm FLOW), one repetition each, so cost and time are compared on the same runs; the metrics `conflict_found`, `contradiction_left` and `gap_recorded` grade them. Generated HTML is no longer a candidate: it is adopted, with its build and a quality check against a real PRD.

## Releasing
The kit has no version numbers beyond commits: `/ai-kit` records the short commit in each project's manifest. Note user-visible changes in `CHANGELOG.md`, newest first.

## Candidates (not yet proven)
| Candidate | Idea | What would prove it |
|---|---|---|
| Path-scoped rules | `.claude/rules/*.md` with `paths:` frontmatter load only when matching files are touched; testing rules could load only when a test file is edited, PRD writing rules only under `docs/prd/` | Measure session context and rule compliance with and without, on the same tasks; more useful now that layer folders can scope rules by path |
| Format hook | A PostToolUse hook formats the edited file, non-blocking (`commands.fix_file {file}`) | Lint-fix rounds and tokens per task with and without, in `eval/` |
| Code intelligence | A language server for go-to-definition and references in large legacy code, where the Claude Code version supports it | Tokens and tool calls to locate callers versus Grep, in `eval/` |
