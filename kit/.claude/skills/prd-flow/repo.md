# prd-flow · repository adapter

The only repository-specific file of the skill. Filled by `/ai-kit install`; fill any remaining `<...>`; delete rows that do not apply.

## Gate config

Parsed by the scripts. Keep the two-column table format and the key names.

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

| Key | Meaning |
|---|---|
| `language` | Prose of PRD, TRD, sheet and gate output; IDs, code, commits and file names stay English |
| `sheet_labels` | Headings and labels of `sheet.md`, in order; translate them for another `language` |
| `plain_words` | Words the user never says; S4 flags them in a decision title or option |
| `plan_strict` | `yes` makes the shared-file wave check P17 an error |
| `shared_files` | Files several tasks tend to touch; P17 when two tasks of one wave touch one |
| `planned_heading`, `via_header` | The TRD heading of rules not built yet (G8, G20), and the last column that marks a rule table (G3) |
| `proposed_marker`, `pending_marker`, `planned_source` | Marker words of rule rows; G30 fails `--final` while a proposed row is left |
| `prd_section_budget_lines`, `trd_budget_lines`, `pack_budget_lines`, `plan_budget_kb` | Size warnings (G31, G26, pack, plan); over budget, split |
| `html`, `trd_html`, `html_template`, `html_mode` | Reading pages built only by `/docs-html`; `generated`: a stale page is reported only by `gate.py --html` (G29, G32), `hand` (default) warns once (G5); `none` opts out |

## Commands

Always through `scripts/gates.sh`; the stack commands behind each target are in `ai-kit.json` ("commands", "tests").

| Who | `scripts/gates.sh` targets |
|---|---|
| A person | `related [files]` (agents rely on `verify`) |
| Executor | `one <file>`, `red <file>`, `fix-files <file>...` then `lint-files <file>...`, `move <source> <start> <end> <destination> [--at LINE]` (C6 only); `close <slug> --case <C>` |
| Surveyor | `prd-sweep --ids <ID>,<ID> --terms "<subject>" --out .claude/prd-flow/state/<slug>/sweep.md`; `settings-check` (deny rules that block files the flow writes) |
| Chief | background: `baseline`, `verify`, `compare`, `watch <slug> [--minutes N]`; foreground: `cleanup [<slug>]`, `reap` |
| Anyone | `python` (the interpreter), `lint`, `fix` then `lint`, `imports`, `ratchet` |

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

Findings-only agents in `.claude/agents/`, assigned per card as `Lens:`; `none` is valid.

| The task touches | Reviewer agent |
|---|---|
| `<security-sensitive area: auth, payments, personal data>` | `<security-reviewer>` |
| `<architecture seams>` | `<architecture-reviewer>` |
| anything else | none |

## Protected rules

What a request cannot change by itself (`reference/survey.md` "Protected rules").

| Protection | Source | Right path |
|---|---|---|
| `<principle>` | constitution `<numeral>` | `<ADR / constitution amendment / no exception>` |
| Invariant covered by a structural test | `docs/trd/invariants.md` | Changing it is a repository rule change: ADR or constitution amendment |

## Variants and tenants (K03, K04)

| Item | Where it is documented | Notes |
|---|---|---|
| Variants (platforms, channels, engines) | `<docs/prd/... section>` or `none` | `<for example: web and mobile>` |
| Tenants or customers | `<docs/prd/... section>` or `none` | `<per-tenant behavior is configuration, never a branch on the name>` |

## Rule owners

Who decides on a section (K13, `sheet.md` "Owner"). Delete the rows when nobody owns one.

| PRD files (glob) | Owner | How they approve |
|---|---|---|
| `<docs/prd/product/04-*.md>` | `<name or role>` | `<in the interview, a PR review, a message>` |

## Shared PRDs

PRD folders kept identical in a sibling repository (G28). Delete the rows when none is shared.

| PRD folder | Sibling repository path | Source of truth |
|---|---|---|
| `<docs/prd/triage-documents>` | `<C:/Projects/backend/docs/prd/triage-documents>` | `<this repository or the sibling>` |

## Consumers in sibling repositories (K08; `scripts/gates.sh contracts` when snapshots exist)

| Repository | Local path | What to check |
|---|---|---|
| `<backend>` | `<C:/Projects/backend>` | `git -C <path> grep -n "<field>" origin/<branch> -- src` (DTO validation, enums) |

## Change routing (docs agent, plan)

| Change via | Plan task |
|---|---|
| code | Agent tasks in the plan format |
| config | `<how config is published: endpoint, approval gate, versioning>`; no code |
| env | Deploy note in `<infra repo>`; applies to every tenant |
| prompt | `<publish path>`; no code |
| backend, frontend | Handoff note to `<repo>` with the rule rows; outside this plan |

## Evidence of real sessions (survey)

| Evidence | Where |
|---|---|
| `<agent calls, request logs, audit table>` | `<table or log event names>` |
