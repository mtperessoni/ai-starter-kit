# TRD

One TRD per area (rule AR13, `docs/code-structure.md`): where the area lives in the code, how it enters the flow, which tests cover it and what must not break. The rules are in the PRD ([index](../prd/INDEX.md)); the TRD never repeats them. Load only the file of the task's area.

| Area | TRD | Folder or files | PRD sections |
|---|---|---|---|
| <What it covers, in one line> | [<area>.md](<area>.md) | `<folder or globs of the area>` | <PRD name>: [07](../prd/<prd>/07-payment.md), [08](../prd/<prd>/08-orders.md) |

An area whose TRD passes `trd_budget_lines` is a folder: its row links `<area>/README.md`, which lists the parts (`<area>/<part>.md`, mirroring the PRD section groups).

Cross-cutting:

- [infra.md](infra.md): `<src>/infra/` (persistence, providers, configuration, observability, auth).
- [invariants.md](invariants.md): repository rules by kind of change, each with the test or principle that proves it.
- [testing.md](testing.md): gates, how to run one file offline, fakes.
- [../flow.md](../flow.md): the one end-to-end diagram.

Whoever moves a file, an entry point or a test of an area updates its TRD in the same commit. Symbol names, never line numbers or default values: they live in the code and change without anyone touching the map. `python .claude/skills/prd-flow/scripts/gate.py --trd` checks the paths, symbols and IDs named here (G23 to G26); CI runs it.
