# prd-gate · repository adapter

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
| pack_budget_lines | 120 |
| plan_budget_kb | 60 |

`html`: the hand-maintained reading version (one tab per PRD, built by `/prd-create` from `docs/templates/prd.html`). The gate checks that every rule row has the same words there. `none` only for a repository that explicitly opts out.

## Commands

Always through `scripts/gates.sh`; the stack commands behind each target are in `ai-kit.json` ("commands", "tests").

| Purpose | Command |
|---|---|
| Related tests of a change (while working) | `scripts/gates.sh related [files]` (ratchet, then mirror tests and importers; only failures and the summary are printed, the log goes to `.claude/prd-gate/state/_tests/`) |
| One test file, no coverage | `scripts/gates.sh one <file>` |
| Baseline before the first code task | `scripts/gates.sh baseline <slug>` |
| Full suite, once at the end, against the baseline | `scripts/gates.sh compare <slug>` |
| Lint, verify only | `scripts/gates.sh lint` |
| Lint, repair | `scripts/gates.sh fix`, then `lint` |
| Import and cycle check | `scripts/gates.sh imports` |
| Structure ratchet | `scripts/gates.sh ratchet` |
| Move code by line range | `python scripts/move_lines.py <source> <start> <end> <destination> [--at LINE]` |

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

Findings-only agents in `.claude/agents/`. The planner assigns one per task; `none` is valid.

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

## Variants and tenants (impact K03, K04; interview D02, D03)

| Item | Where it is documented | Notes |
|---|---|---|
| Variants (platforms, channels, engines) | `<docs/prd/... section>` or `none` | `<for example: web and mobile>` |
| Tenants or customers | `<docs/prd/... section>` or `none` | `<per-tenant behavior is configuration, never a branch on the name>` |

## Extra interview dimensions

Domain dimensions added after D15 of `reference/interview.md`.

| ID | Dimension | Guiding question |
|---|---|---|
| D16 | `<for example: Pricing>` | `<does the change affect what the customer pays?>` |

## Consumers in sibling repositories (impact K08)

| Repository | Local path | What to check |
|---|---|---|
| `<backend>` | `<C:/Projects/backend>` | `git -C <path> grep -n "<field>" origin/<branch> -- src` (DTO validation, enums) |

## Change routing (planner)

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
