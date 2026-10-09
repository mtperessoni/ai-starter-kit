# Readiness plan (N4)

AI readiness of an existing repository, in its current layout (PC11). Nothing moves: the layout stays, the areas come from `ai-kit.json` (`feature_root`, `areas`, `map_dirs`). Checklist: `docs/ai-readiness.md`. The move to feature folders is a separate option (`reference/restructure.md`, N5).

## Rules
| ID | Rule |
|---|---|
| R01 | Behavior does not change and the layout stays; a step that needs either stops and becomes a C5 or an N5 |
| R02 | Waves are ranked by `scripts/hotspots.py` (PC12): commits in the window times lines; a large file nobody changes waits |
| R03 | Characterization tests come before touching untested code (TS42), citing the area |
| R04 | Extract on touch (AR21): a task that changes a file over the limits first extracts the responsibility it touches, by script (AR12), never grows the file |
| R05 | Maps per map folder (AR07): feature map or folder map, each linking the area TRDs (AR13) |
| R06 | Noise exclusion (CE22, AR28): `.ignore`, read denies, generated markers, from `ai-kit.json` `ignore` and `generated_patterns` |
| R07 | Big tests split before the code they prove; builders beside the tests (TS41) |
| R08 | Names and IDs (AR02, AR06): generic names replaced by the responsibility, PRD IDs in the first comment of each module and test |
| R09 | Crowded folders (AR23) split by area or responsibility; the ratchet starts from the current state and no wave raises an entry (X05 of `restructure.md`) |
| R10 | Contracts snapshot (DS30): schema and API snapshots in `contracts`, checked by `scripts/gates.sh contracts` |

## Waves
| Wave | Tasks | Proof |
|---|---|---|
| 1 | Setup and noise: `commands.setup` verified, `.ignore`, settings denies, generated markers, contracts snapshot | `scripts/gates.sh setup`, `contracts`, ratchet |
| 2 | Maps: folder maps for `map_dirs`, feature maps for own folders, area TRDs, patterns to copy (DS31) | gate, map length check |
| 3 | Characterization tests for the top hotspots without tests (R03) | the new tests pass on unchanged code |
| 4 | Hotspot splits by responsibility, by script (R04); big tests split (R07) | import check, types, lint, ratchet lowered |
| 5 | Names, IDs and crowded folders (R08, R09), area by area | related tests per area, ratchet lowered |
| 6 | Full suite once, against the baseline | `scripts/gates.sh compare <slug>` |

## Plan format
Write `changes/NNN-ai-readiness/plan.md` in the prd-flow task format (`.claude/skills/prd-flow/reference/agent-plan.md`): one task per area per wave, each naming the area, its files and its tests, tasks ordered by hotspot rank. Present as a table (ID, result, owns, depends on, model, lens) for approval; execution follows prd-flow `reference/execution.md` in a new session. Close by offering N5 with its cost.
