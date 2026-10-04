# Architecture Decision Records

The decisions that shaped this repository, with the reasoning that produced them and the alternatives that lost. An ADR is a record, not a proposal: it explains why the code looks the way it does to whoever inherits it.

## Index

| # | Title | Status |
|---|---|---|

## When a new ADR is required

Write one whenever a decision changes something in the constitution's **Technology Constraints** section (language, framework, persistence strategy, external providers, observability stack, tooling), changes a protected rule (`.claude/skills/prd-gate/repo.md` "Protected rules"), or reverses a decision recorded here. An amendment to `.specify/memory/constitution.md` without an ADR leaves the next reader with a rule and no reason.

Do not edit an accepted ADR to say the opposite: supersede it with a new one and set the old status to `Superseded by NNNN`. The value of this folder is that it preserves what we believed at the time, including where we were wrong.

A decision with one option is a constraint: it belongs in the constitution or in `AGENTS.md`, not here.

Numbering is sequential and never reused. Status is `Accepted`, `Superseded by NNNN` or `Deprecated`.

## Template

```
# ADR NNNN: <title of the decision, not of the topic>

**Status**: Accepted
**Date**: YYYY-MM-DD
**Deciders**: <team or names>

## Context

<The forces at play, the concrete facts, what problem is actually being solved. Reference real evidence: incidents, measurements, constraints of existing systems, deadlines.>

## Decision

<What we decided, stated plainly and actively.>

## Consequences

### Positive
### Negative
### Neutral

## Alternatives considered

<Each alternative with what it was good at and the specific reason it was rejected. No strawmen.>
```

Keep each record between roughly 400 and 700 words. If the negatives read as weak, the ADR is a sales pitch and not a record: rewrite them until they are the objections a reviewer would actually raise.
