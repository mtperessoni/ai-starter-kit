# surveyor

Context, freshness and impact, in sequence, for a rule change. Model: `opus` for size L (the confrontation is the step whose miss costs the most), `sonnet` for M. Full or by-size sweep: see `impact.md` "Sweep by size". Short mode (short C5): K01, K02, K11, K12 on the touched rules only, confrontation at most 15 lines.

1. **Batch 1, one message:** `Read .claude/skills/prd-flow/repo.md` (including "Rule owners" and "Shared PRDs"); `Grep` the request's terms in `docs/prd/INDEX.md`; `Read docs/trd/README.md`; `Grep` the terms in the PRD section files to find the rows; `git fetch -q && git rev-parse --short HEAD && git rev-list --count HEAD..origin/<base_branch>`.
2. **Batch 2:** the tables of the sections involved; the TRD feature file; `Grep "<IDs>" docs/prd changes <test folders>` (never `changes/archive/`, LT07); the lines of `docs/trd/invariants.md` for the kind of change; the constitution principle the change touches (title and excerpt).
3. **Freshness:** check the Source of each rule that will change (file and symbol exist, behavior matches). A divergence goes into the pack; an out-of-scope divergence is only noted, with no new call.
4. **Impact:** follow `reference/impact.md` (K01 to K13, trade-offs, protections). Sweep by size per `impact.md` "Sweep by size" (K11 and K12 never skipped for the touched IDs; K08 uses `scripts/gates.sh contracts` when snapshots are configured). A check skipped and discovered during execution becomes an extra round with the user. The confrontation always carries `Checked:` and `Conflicts:`. Write `impact.md` already in the confrontation format from there: it is what the main thread shows the user.
5. **Pre-interview:** for each dimension D01 to D15 of `reference/interview.md` plus the extra ones of `repo.md`, mark the state defined in `reference/impact.md` "Pre-interview states". Put the assumed ones in one block of at most 6 lines at the end of the confrontation.
6. Write `pack.md` in the format below and run `<python> .claude/skills/prd-flow/scripts/gate.py --pack .claude/prd-flow/state/<slug>/pack.md`. ERROR: fix the pack and run again.

Format of `pack.md` (the gate checks the sections and that every rule row is **literal**, copied from the PRD):

```markdown
# Pack · <slug>
Base: <short commit> · Branch: <name> · Behind origin/<base_branch>: <n> (touches the scope: yes|no)
Request: <one line>

## Rules
### docs/prd/product/04-checkout.md
| CHK-02 | <row copied exactly from the PRD> |

## Rows without ID
### docs/prd/product/04-02-limits.md
| 5 | <row copied exactly from the PRD> |

## TRD
- docs/trd/checkout.md

## Invariants
- I-07 <one line>

## Principles
- III <one line>

## Open questions linked
- Q-CHK-04 <one line>

## Changes and tests
- changes/007-checkout/plan.md
- src/features/checkout/tests/test_payment_call.py

## Divergences
- in scope: <PRD says / code does, with file::symbol>
- out of scope: <note>

## Pre-interview
| Dimension | State | Detail |
|---|---|---|
| D02 variants | doc | same config for web and mobile (payment_config.py::PaymentConfig) |
| D04 numbers | assumed | 20 s, from the PaymentConfig default |
```

Return: the confrontation (at most 25 lines, taken from `impact.md`, 15 in short mode), the in-scope divergences, the assumed block and the open dimensions.
