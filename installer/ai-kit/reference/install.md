# install

## Steps
| Step | Does | Leaves |
|---|---|---|
| I1 | K01 and K02. `Glob` the project root and two levels down for manifests and configuration: package manifests, lockfiles, test configs, linter configs, CI files, `Makefile`/`justfile`/`Taskfile.yml`, `CLAUDE.md`, `AGENTS.md`, `.specify/`, `docs/`, `.claude/`. Detect monorepo workspaces | file list |
| I2 | Read `<kit>/stacks/README.md` and only the matching recipes. Read the project's own scripts (package scripts, Makefile targets, CI steps): they win over the recipe | stack profile |
| I3 | Source layout: the source folders, whether code is organized by feature (folders per product area) or by layer (`controllers/`, `services/`, `models/`), the entry point, the test folders. Large trees: one Explore agent with these questions, answers only | layout |
| I4 | Run each candidate command once with output to a file (`.claude/prd-gate/state/_install/`), read the summary: test runner on one existing test file, lint verify, type check, import check, the whole unit tier once (its failures become the first baseline). Write down the failure line format to derive `tests.failure_regex` | verified commands |
| I5 | Questions, one round of at most 4 (K07): the project's one-line description; the domain principles of the constitution (offer 2 or 3 drawn from the README, the code and the existing docs, recommended first); the variants and tenants (platforms, channels, customers) if any; the reviewers wanted (risk classes: security, data contracts, safety, compliance). Base branch and CI platform are detected, asked only when ambiguous | answers |
| I6 | Plan table (K03): every file with create, merge, replace or skip; commands for `ai-kit.json`; linter rules to add; the branch name. Wait for yes | approval |
| I7 | Copy the payload from `<kit>/kit/` following `ownership.md`. Kit-owned files are copied byte for byte. Never copy `gitignore.kit` as a file: append its lines to `.gitignore` | files |
| I8 | Fill the project-owned files (table below). No `<...>` or `{{...}}` placeholder may remain outside `docs/templates/` | filled files |
| I9 | Structure enforcement from the recipe: add the linter rules for AR03, AR04, AR05, AR09 at the kit's limits with a baseline of today's violations (shrink-only); in Python, write `tests/test_architecture.py` as the recipe says. Run `python scripts/ratchet.py --init` and put its output into `ai-kit.json` `allowlist`. Update `docs/code-structure.md` "Checked by" when a rule ends as "review" | enforcement |
| I10 | Reviewers: for each risk class chosen in I5, copy `docs/templates/reviewer-agent.md` to `.claude/agents/<risk>-reviewer.md` and fill it: the principle it guards, 4 to 7 checks specific to this code (read the relevant folders by symbol), severities, 3 examples. Register them in `repo.md` "Reviewers" | agents |
| I11 | Verify (below). Fix what fails; what cannot be fixed becomes a line in the report | results |
| I12 | Write `.ai-kit/manifest.json` (`ownership.md`). Commit `chore: install ai-starter-kit <version>` (one commit; the PRD and TRD come later in their own commits) | commit |
| I13 | Report and next steps (below) | report |

## Filling the project-owned files
| File | Fill with |
|---|---|
| `ai-kit.json` | `source_dirs`, `feature_root` (the features folder, or the source folder when code is organized by layer), `code_extensions` limited to the stack's, `test_patterns` and `ignore` from the recipe, `commands` and `tests` from I4 |
| `.claude/skills/prd-gate/repo.md` | `base_branch`; `change_via` adapted (drop `prompt` when there are no prompts, add the consumers that exist); Layout; Big files (from the ratchet's `long_modules`); Reviewers (I10); Protected rules (from the constitution); Variants and tenants (I5); Consumers in sibling repositories (ask only if a contract leaves this repository); Change routing (how config and env changes are deployed here); Evidence of real sessions (logs, audit tables) |
| `CLAUDE.md` | Project line, the constitution index (one line per principle), the gate rule, the code structure summary with this repo's folders, `@AGENTS.md` |
| `AGENTS.md` | Overview and stack, Commands (the `scripts/gates.sh` targets), Critical constraints (the kit's generic ones plus the domain ones from I5), Directory map from I3, Workflow, Finding things, Handing work to a subagent |
| `.specify/memory/constitution.md` | Domain principles from I5 (each with what it forbids and how it is enforced), Technology Constraints from I2, ratification date |
| `.github/workflows/ci.yml` | The recipe's CI setup step in place of the placeholder; branches that deploy (from existing deploy workflows) in `push.branches` |
| `.github/workflows/claude-review.yml` | Project line; one section per constitution principle with its checks |
| `.gitleaks.toml` | The recipe's ignore paths |
| `docs/flow.md` | Leave the template; trd-create writes it |

## Verify
All must pass, or be reported:
- `scripts/gates.sh lint`
- `scripts/gates.sh ratchet` (green right after `--init`)
- `scripts/gates.sh imports`
- `python scripts/related_tests.py <one existing source file>` prints its mirror test and importers; `scripts/gates.sh related <that file>` runs them and prints only failures and the summary
- `scripts/gates.sh baseline install` records the baseline; `scripts/gates.sh compare install` reports zero new failures
- `python .claude/skills/prd-gate/scripts/gate.py` only reports that `docs/prd/INDEX.md` does not exist yet (expected until prd-create)
- A search for U+2014 over the files written (the Grep tool with the pattern `\x{2014}`) finds no em dash

## Report
In at most 20 lines: stack detected, files created and merged, commands verified, linter rules and baseline sizes, reviewers created, what failed, the commit. Then the next steps:
1. Add the global block once per machine if `install.sh` did not: `<kit>/global/CLAUDE.md` into `~/.claude/CLAUDE.md`.
2. `/prd-create` to write the PRD from the code (or by interview in a new project).
3. `/trd-create` to map the code and add the feature `CLAUDE.md` files; in a layer-organized codebase it proposes the restructuring plan.
4. From then on, every change goes through `/prd-gate`.
