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

| Purpose | Command |
|---|---|
| One test file, no coverage | `<for example: uv run pytest path/to/test_x.py --no-cov -q>` |
| Related tests of a change | `<for example: vitest related <files> --run · or the mirror test plus Grep of importers>` |
| Full suite (once, at the end of a delivery) | `<for example: ./scripts/gates.sh offline>` |
| Lint, verify only | `<for example: ./scripts/gates.sh lint>` |
| Lint, repair | `<for example: ./scripts/gates.sh fix>` |
| Import and cycle check | `<for example: python -c "import main" · tsc --noEmit>` |
| Structure ratchet | `<for example: pytest tests/test_architecture.py · node scripts/ratchet.mjs>` |
| Test output to a file | `<command> > .claude/prd-gate/state/<slug>/test.log 2>&1`, then Grep `FAILED\|ERROR` and the summary line |

## Layout

| Item | Value |
|---|---|
| Source folder | `<src>` |
| Feature folders | `<src>/features/<f>/` (map: `docs/trd/README.md`) |
| Core features (must not import peripheral ones) | `<names>` |
| Shared code | `<src>/infra/` |
| Spec folder | `specs/` (spec-kit) or `<none>` |

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
