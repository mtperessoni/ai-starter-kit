# prd-flow · repository adapter

The only repository-specific file of the skill. Every other file of the skill is generic and reads its values from here. Filled by `/ai-kit install`; fill any remaining `<...>`; delete rows that do not apply rather than leaving them empty.

## Gate config

Parsed by `scripts/gate.py`. Keep the two-column table format and the key names.

| Key | Value |
|---|---|
| base_branch | main |
| prd_dir | docs/prd |
| prd_glob | */*.md |
| trd_dir | docs/trd |
| html | docs/prd/prd.html |
| forbid_em_dash | yes |
| change_via | code, config, env, prompt, data, backend, frontend |
| pending_marker | pending code |
| planned_source | planned |
| language | English |
| planned_heading | Planned |
| via_header | Change via |
| pack_budget_lines | 120 |
| plan_budget_kb | 60 |
| proposed_marker | proposed |
| plain_words | flag, key, handler, payload, endpoint, enum |
| plan_strict | no |
| sheet_labels | What changes in the rules, What does not change, Assumed, Decisions, How to answer, Today:, Why it matters:, Example:, (Recommended) |
| shared_files |  |
| html_mode | generated |
| html_template | docs/templates/prd.html |
| trd_html | docs/trd/trd.html |
| trd_budget_lines | 250 |
| prd_section_budget_lines | 200 |

`sheet_labels`: the headings and field labels of `sheet.md` in this order (comma list); the sheet lint reads them, so a repository in another `language` translates them here. `plain_words`: words the user never says; the sheet lint (S4) flags them in a decision title or option. `plan_strict`: `yes` makes the plan alignment checks P11 and P13 to P16 errors instead of warnings. `shared_files`: comma-separated files several tasks tend to touch (settings, allowlists, config modules); the wave gate P17 fails when two tasks of one wave touch the same one.

`prd_section_budget_lines`: lines a PRD section file may have before G31 warns; a section over it splits into smaller section files, so the rows a change reads stay bounded as the product grows.

`proposed_marker`: the word inside `*(proposed)*`, the marker of a rule that comes only from documents. G30 fails `--final` while one is left.

`html_mode`: `generated` (the pages are built by `/docs-html`; the default gate warns when one is stale, G29 and G32, and `gate.py --html` fails) or `hand` (not built nor checked; one G5 warning until `/ai-kit update` migrates it). Absent key means `hand`. No prd-flow step ever touches the HTML.

`html_template`: the template both builds render into (`html` and `trd_html`).

`trd_html`: the TRD reading page, rendered from `trd_dir` and `docs/flow.md` by `/docs-html`. `none` opts out.

`trd_budget_lines`: lines a TRD file may have before G26 warns; an area over it splits into parts (`reference/trd-planned.md`).

`language`: language of the PRD and TRD prose, the interview and the gate output. IDs, code, commits and file names stay English. The installer sets it from the language of the existing docs.

`planned_heading`: the level-2 TRD heading that lists rules not built yet; G8 checks the IDs under it and G20 fails `--final` while it exists. Set it to the project's own word (for example `Planejado`).

`via_header`: the last header column of a rule table (for example `Muda via`). Only rows of tables with this column are rules: `--trace`, `--status` and G3 skip the IDs of other tables, such as open questions.

`html`: the PRD reading page (one tab per PRD), rendered from `docs/prd/` by `/docs-html` and never edited. `none` only for a repository that explicitly opts out.

## Commands

Always through `scripts/gates.sh`; the stack commands behind each target are in `ai-kit.json` ("commands", "tests").

| Purpose | Command |
|---|---|
| Related tests of a change (a diagnostic for a person; agents use `verify`) | `scripts/gates.sh related [files]` (ratchet, then mirror tests and importers; only failures and the summary are printed, the log goes to `.claude/prd-flow/state/_tests/`) |
| One test file, no coverage | `scripts/gates.sh one <file>` |
| Wave verification (chief, once per wave) | `scripts/gates.sh verify <slug>` |
| Baseline, started by the chief after the plan commit (background Bash) | `scripts/gates.sh baseline <slug>` |
| Full suite, once at the end, against the baseline | `scripts/gates.sh compare <slug>` |
| Lint, verify only | `scripts/gates.sh lint` |
| Lint, repair | `scripts/gates.sh fix`, then `lint` |
| Import and cycle check | `scripts/gates.sh imports` |
| Structure ratchet | `scripts/gates.sh ratchet` |
| Python interpreter | the output of `scripts/gates.sh python` |
| Move code by line range (C6 only) | `scripts/gates.sh move <source> <start> <end> <destination> [--at LINE]` |

## Layout

| Item | Value |
|---|---|
| Source folder | `<src>` |
| Layout description | `<free text from ai-kit.json layout>` |
| Feature root | `<src>/features/` (`ai-kit.json` `feature_root`; map: `docs/trd/README.md`) |
| Areas | `<feature folders, or see ai-kit.json areas>` |
| Map folders | `<feature folders plus ai-kit.json map_dirs>` |
| Where a new area goes | `<a new feature folder (recommended), or the place docs/code-structure.md names>` |
| Core features (must not import peripheral ones) | `<names>` |
| Shared code | `<src>/infra/` |
| Change folder | `changes/` (LT01; finished ones in `changes/archive/`) |
| Spec-kit | `none` \| `kept` (LT11) |
| Legacy specs | `specs/` kept as history, or `<none>` (LT07, LT11) |

## Big files (read by symbol only)

| File | Why it is big |
|---|---|
| `<path>` | `<reason, until it is split>` |

## Reviewers

Findings-only agents in `.claude/agents/`. The docs agent assigns one per task in the plan as the lens of the wave reviewer; `none` is valid.

| The task touches | Reviewer agent |
|---|---|
| `<security-sensitive area: auth, payments, personal data>` | `<security-reviewer>` |
| `<architecture seams>` | `<architecture-reviewer>` |
| anything else | none |

## Protected rules

What a request cannot change by itself. Used by `reference/impact.md`.

| Protection | Source | Right path |
|---|---|---|
| `<principle>` | constitution `<numeral>` | `<ADR / constitution amendment / no exception>` |
| Invariant covered by a structural test | `docs/trd/invariants.md` | Changing it is a repository rule change: ADR or constitution amendment |

## Variants and tenants (impact K03, K04)

| Item | Where it is documented | Notes |
|---|---|---|
| Variants (platforms, channels, engines) | `<docs/prd/... section>` or `none` | `<for example: web and mobile>` |
| Tenants or customers | `<docs/prd/... section>` or `none` | `<per-tenant behavior is configuration, never a branch on the name>` |

## Rule owners

Who decides on a section. When a change touches an owned section and the approver is not the owner, the sheet carries an owner item and the change does not proceed until the user states the owner agreed, and the CHANGELOG records `decided by <owner>, written by <approver>`. Delete the rows when nobody owns a section.

| PRD files (glob) | Owner | How they approve |
|---|---|---|
| `<docs/prd/product/04-*.md>` | `<name or role>` | `<in the interview, a PR review, a message>` |

## Shared PRDs

PRD folders kept identical in a sibling repository. `gate.py --sibling` fails G28 when they differ (line endings normalized) and warns when the sibling path is absent locally. Delete the rows when none is shared.

| PRD folder | Sibling repository path | Source of truth |
|---|---|---|
| `<docs/prd/triage-documents>` | `<C:/Projects/backend/docs/prd/triage-documents>` | `<this repository or the sibling>` |

## Consumers in sibling repositories (impact K08)

| Repository | Local path | What to check |
|---|---|---|
| `<backend>` | `<C:/Projects/backend>` | `git -C <path> grep -n "<field>" origin/<branch> -- src` (DTO validation, enums) |

K08 uses `scripts/gates.sh contracts` when snapshots are configured. A row here with no snapshot configured is a prompt for trd-create and `/ai-kit install` to propose configuring them.

## Change routing (docs agent, plan)

| Change via | Plan task |
|---|---|
| code | Agent tasks in the plan format |
| config | `<how config is published: endpoint, approval gate, versioning>`; no code |
| env | Deploy note in `<infra repo>`; applies to every tenant |
| prompt | `<publish path>`; no code |
| backend, frontend | Handoff note to `<repo>` with the rule rows; outside this plan |

## Evidence of real sessions (classification)

| Evidence | Where |
|---|---|
| `<agent calls, request logs, audit table>` | `<table or log event names>` |
