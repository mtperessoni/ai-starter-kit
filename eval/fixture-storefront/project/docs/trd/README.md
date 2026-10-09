# TRD

One TRD per feature (rule AR13, `docs/code-structure.md`): where the feature lives in the code, how it enters the flow, which tests cover it and what must not break. The rules are in the PRD ([index](../prd/INDEX.md)); the TRD never repeats them. Load only the file of the task's feature.

| Feature | TRD | Folder | PRD sections |
|---|---|---|---|
| Customer record and the payload sent to the orders service | [customers.md](customers.md) | `src/storefront/features/customers/` | Storefront: [02](../prd/storefront/02-customers.md) |

Cross-cutting:

- [infra.md](infra.md): `src/storefront/infra/` (nothing yet).
- [invariants.md](invariants.md): repository rules by kind of change, each with the test or principle that proves it.
- [testing.md](testing.md): gates, how to run one file offline.
- [../flow.md](../flow.md): the one end-to-end diagram.

Whoever moves a file, an entry point or a test of a feature updates its TRD in the same commit. Symbol names, never line numbers or default values: they live in the code and change without anyone touching the map.
