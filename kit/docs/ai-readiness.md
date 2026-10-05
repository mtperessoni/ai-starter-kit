# AI readiness checklist

Techniques that make a repository cheap for an agent to work in. Used by `trd-create`'s readiness plan and by `/ai-kit doctor`. Feature folders are optional (AR20): every row works in any layout unless it says otherwise. Rule text lives in the rules files; here only IDs.

## Navigation and search
| IDs | Technique | Any layout | Checked by | Where |
|---|---|---|---|---|
| CE22 | Search noise excluded and reads denied | yes | install, doctor | `.ignore`, `.claude/settings.json` |
| AR28 | Generated files marked, never edited | yes | ratchet | `generated_patterns` |
| AR22 | Greppable wiring | yes | review, linter | area TRD |
| AR02 | Unique descriptive file names | yes | ratchet | `docs/code-structure.md` |
| AR06 | PRD IDs in first comment of module and test | yes | ratchet | code, tests |

## Size and single responsibility
| IDs | Technique | Any layout | Checked by | Where |
|---|---|---|---|---|
| AR03 | Size limits | yes | ratchet, linter | `ai-kit.json` limits |
| AR23 | Folders under the file cap | yes | ratchet | `crowded_dirs` |
| AR21 | Extract before changing a long file | yes | ratchet, review | legacy areas |
| AR24 | Complexity limits | yes | linter | recipe |
| AR25, AR26 | Dead and duplicated code | yes | linter | recipe |
| AR27 | Typing strictness only up | gradual typing only | type checker | recipe |

## Maps and traceability
| IDs | Technique | Any layout | Checked by | Where |
|---|---|---|---|---|
| AR07 | Short `CLAUDE.md` per map folder | yes, with `map_dirs` | ratchet | map folders |
| AR13, DS15 | One TRD per area | yes | review | `docs/trd/` |
| DS31 | Pattern to copy per kind of change | yes | trd-create | `docs/trd/invariants.md` |
| DS30 | Schema and contract snapshots | yes | `scripts/gates.sh contracts` | `contracts` |
| AR19 | Layout config valid | yes | ratchet | `ai-kit.json` |

## Tests: speed and reliability
| IDs | Technique | Any layout | Checked by | Where |
|---|---|---|---|---|
| AR10, TS16 | Tests findable from the module | yes | `scripts/related_tests.py` (mirror names), review | `tests.mirror_patterns` |
| TS37 | Related run within budget | yes | related_tests.py | `tests.related_budget_seconds` |
| TS38 | Flaky list, shrink-only | yes | new_failures.py | `tests.flaky` |
| TS39 | Snapshots never updated to pass | yes | related_tests.py | `tests.snapshot_patterns` |
| TS40 | Parallel-safe tests | yes | review | `docs/trd/testing.md` |
| TS41 | Builders per subject | yes | ratchet, review | beside the tests |
| IN12 | One-command setup | yes | install | `commands.setup` |

## Legacy adoption
| IDs | Technique | Any layout | Checked by | Where |
|---|---|---|---|---|
| PC11, PC09 | Incremental readiness plan in the current layout | yes | trd-create | `reference/readiness.md` |
| PC12 | Hotspots rank the work | yes | `scripts/gates.sh hotspots` | `scripts/hotspots.py` |
| TS42 | Characterization test before change | yes | review | legacy areas |
| AR20 | Feature folders as an optional move | yes | review | restructure option |

## Agent tooling
| IDs | Technique | Any layout | Checked by | Where |
|---|---|---|---|---|
| IN11 | Layout, ignore and permissions at install | yes | install | `.claude/settings.json` |
| IN13 | Readiness per area report | yes | doctor | this file |
| AR12 | Moves by script | yes | review | `docs/code-structure.md` |
