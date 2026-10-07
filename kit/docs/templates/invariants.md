# Invariants · TRD

What a code change must not break, by kind of change. Sources: `AGENTS.md` "Critical constraints", the [constitution](../../.specify/memory/constitution.md) and the structural tests, cited by file name. The full rule is in the source; here, one line. IDs are stable: a new rule goes at the end of its table with the next free number.

## Any change

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-01 | No em dash (U+2014) in code, docs, prompts or commits | AGENTS.md; prd-flow gate G4 |
| I-02 | Zero comments, except the non-obvious and critical why; no comment cites a ticket | AGENTS.md |
| I-03 | Failing test before the implementation | Constitution, test-first principle |
| I-04 | `scripts/gates.sh lint` green | CI |
| I-05 | No empty catch, no swallowed exception, no fire-and-forget without persisted state | AGENTS.md |
| I-06 | Framework and vendor types do not enter `domain/` folders | AGENTS.md; linter import rule |
| I-07 | The structure ratchet does not regress | `scripts/ratchet.py` |
| I-08 | The area's map(s) and TRD change in the same commit as the code they map | `docs/code-structure.md` AR07, AR13 |
| I-16 | Every call site names its target literally; wiring by framework convention is named in the area TRD | `docs/code-structure.md` AR22 |
| I-17 | A generated file is regenerated, never edited | `docs/code-structure.md` AR28; ratchet |

## New environment variable

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-09 | Env only for what changes per environment (secret, address, route, rollout flag); behavior goes to typed configuration | AGENTS.md |
| I-10 | The key is in `.env.example` with a safe placeholder | `<test that compares settings and .env.example>` |

## Removed variable

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-11 | A removed variable is ignored at boot and no longer a setting | `<test that removed variables are ignored>` |

## New external call

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-12 | Timeout, retry policy and failure state are explicit; the unit suite uses a fake | testing.md "Fakes" |

## Logs and metrics

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-13 | Every side effect logs, structured, with the correlation ids | AGENTS.md |

## Tests

| ID | Rule (1 line) | Proof (test or principle) |
|---|---|---|
| I-14 | Tests cite the PRD ID they prove | `docs/code-structure.md` AR06 |
| I-15 | The unit suite touches no network and no database | `<test that executes the offline gate against a canary>` |
| I-18 | Snapshot and golden files are updated only for a change whose PRD ID changed the expected output | `docs/code-structure.md` TS39; `scripts/related_tests.py` |
| I-19 | Tests are parallel-safe: own temp dir, no fixed ports or shared names | TS40; review |

## Pattern to copy by kind of change

Name an existing file that is the reference implementation (DS31); trd-create fills it from the code.

| Kind of change | Pattern to copy |
|---|---|
| New endpoint or entry point | `<existing file>` |
| New external call | `<existing file>` |
| New test | `<existing test file>` |
| New area | `<existing area folder or files>` |

## Gaps

A row whose proof column says `gap` has no test or lint rule yet. The ratchet counts those rows against `ai-kit.json` `allowlist.invariant_gaps`, which only shrinks. trd-create proposes, per gap, the lint rule or test that closes it, ranked by `scripts/gates.sh hotspots`.

<!-- trd-create adds the kinds this repository has: new table or column with personal data, new migration, new state, new endpoint or dependency, configuration per tenant, model output. -->
