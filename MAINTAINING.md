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

## Releasing
The kit has no version numbers beyond commits: `/ai-kit` records the short commit in each project's manifest. Note user-visible changes in `CHANGELOG.md`, newest first.

## Candidates (not yet proven)
| Candidate | Idea | What would prove it |
|---|---|---|
| Path-scoped rules | `.claude/rules/*.md` with `paths:` frontmatter load only when matching files are touched; testing rules could load only when a test file is edited, PRD writing rules only under `docs/prd/` | Measure session context and rule compliance with and without, on the same tasks; more useful now that layer folders can scope rules by path |
| Format hook | A PostToolUse hook formats the edited file, non-blocking (`commands.fix_file {file}`) | Lint-fix rounds and tokens per task with and without, in `eval/` |
| Code intelligence | A language server for go-to-definition and references in large legacy code, where the Claude Code version supports it | Tokens and tool calls to locate callers versus Grep, in `eval/` |
| Generated HTML | Build `prd.html` from the markdown by script instead of by hand | Writer time per rule change versus hand edits, with the same reader experience |
