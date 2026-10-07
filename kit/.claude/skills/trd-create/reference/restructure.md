# Restructuring plan (N5, optional)

Optional (AR20, PC09): offer it with its cost after the readiness plan (`reference/readiness.md`); the repository may keep its layout. The target tree X02 is the recommended one, and the move can be incremental, one area at a time (C6 per area). When the code is not organized by feature, the maps can only describe the spread. The fix is a structure-only refactor (prd-flow C6): behavior does not change, files move into one folder per PRD area, giant files split, generic names disappear. In the source repository this took modules over 500 lines from 18 to 1 and made related-test runs cheap enough to stop running the full suite per task.

## Rules
| ID | Rule |
|---|---|
| X01 | Behavior does not change. A step that needs a different limit, text or order stops and becomes a C5 |
| X02 | The target tree follows `docs/code-structure.md`: `features/<f>/` per PRD area, `infra/` for shared code, `app/` composes; the entry point stays where build and deploy expect it |
| X03 | Code moves by script, never retyped: the agent writes the map (which symbol or line range goes to which new module) and `scripts/move_lines.py` (or an AST tool of the stack) moves it; the model only fixes imports and calls |
| X04 | Big test files split before running tests. During the split the proof is static: the import check (catches cycles), the type check and lint. Tests run in parts afterwards |
| X05 | The ratchet starts from the current state (`python scripts/ratchet.py --init`) and each wave lowers its allowlist; no wave raises an entry |
| X06 | A public entry (package index) re-exports and has no side effects: mounting routes or importing the engine there closes cycles |
| X07 | After each move, mocks and patches must target the module of the caller; patches of the old monolith silently stop working |
| X08 | Root-level test setup stays at the repository root so tests moved beside the code keep their guards |
| X09 | Paths computed from a module's location are rechecked after the move |
| X10 | The TRD and the feature `CLAUDE.md` maps move in the same commit as the code they describe |

## Plan format
Write `changes/NNN-feature-structure/plan.md` with the prd-flow task format (`.claude/skills/prd-flow/reference/agent-plan.md`), one task per feature or per giant file, in waves:

| Wave | Tasks | Proof |
|---|---|---|
| 1 | Create `features/<f>/` skeletons and public entries; move pure domain files | import check, types, lint |
| 2 | Split giant files into collaborators by responsibility (map first, then script) | import check, types, lint, ratchet lowered |
| 3 | Move services and adapters per feature; fix imports | import check, types, lint |
| 4 | Move and split tests beside the code; root test setup kept | related tests per feature |
| 5 | Maps: TRD and feature `CLAUDE.md` updated; ratchet allowlist lowered to the new state | gate, ratchet |
| 6 | Full suite once, against the baseline | `scripts/gates.sh compare <slug>` |

Present the plan as a table (ID, result, owns, depends on, model, reviewer) for approval; execution follows prd-flow `reference/execution.md` in a new session.
