# Design · <NNN-slug>

Size L only. A draft: every section names where it goes when the change is promoted.

## Unknowns and research
Promotes to: the decisions below, or nothing.

| Question | Finding | Source |
|---|---|---|
| <what was not known> | <what was found out> | <link, file::symbol or experiment> |

## Decisions
Technical decisions only. Product trade-offs go to `decisions.md` (`DEC-NN`) and from there to the CHANGELOG.
Promotes to: `docs/adr/` (one ADR each, via `/adr`).

| Decision | Reason | Consequence |
|---|---|---|
| <what was chosen> | <the forces> | <the cost accepted> |

## Data model
Promotes to: the real schema or migration, plus the TRD of the feature.

<Entities, fields, relations and states, as the code will have them.>

## Contracts
Promotes to: the real artifact (OpenAPI, schema, proto), plus a link in the TRD.

<Endpoints, events or messages: shape, errors, versioning.>

## Alternatives considered
Promotes to: the ADR of the decision it informs.

| Alternative | Why it lost |
|---|---|
| <option> | <specific reason> |
