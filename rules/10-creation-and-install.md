# Creating the docs (PC) and installing the kit (IN)

## Creating the PRD and the TRD (PC)

| ID | Rule | Why | Lands in |
|---|---|---|---|
| PC01 | The first PRD documents what the code does today, defects included; a behavior that looks wrong is written as it is, with a "checked in code" callout and an open question. Fixing it is a later rule change | The source repository's PRD was written this way, read from the code at a pinned commit, and that is what made it trustworthy as a source of truth | prd-create P01 |
| PC02 | A repository can hold several PRDs, one folder each, when flows run independently (different actors, triggers or consumers). The source repository has two: the analysis run and the guided conversation | One PRD per independent flow keeps each section small and each reader focused | prd-create `anatomy.md` "How many PRDs" |
| PC03 | Every PRD has the same anatomy: summary, glossary with code names, scope, end-to-end journey with a diagram, one section per journey step, states and failures, audit and privacy, configuration, tenant matrix, problems of the current structure, spec versus code, risks, open questions | Readers and agents find the same thing in the same place in every PRD | prd-create `anatomy.md` |
| PC04 | Each step section explains before it rules: what it is, how it works, one concrete example, then the outcome table and the rule table | A rule table without the explanation is unreadable to product people | prd-create P04 |
| PC05 | The outline (PRDs, sections, prefixes, sources) is approved by the user before any section is written | Restructuring a written PRD costs more than approving an outline | prd-create P07 |
| PC06 | Facts come from mapper workers that read the code by area and write inventories; writers turn inventories into sections; the orchestrator never reads the code itself | Same economy as prd-gate: the long context stays in the workers | prd-create workers |
| PC07 | The PRD was split into one file per section after the source repository's agents read two files of 64k and 165k characters whole for every rule they needed; line numbers in Source went stale within hours and were dropped in favor of the TRD | Lazy loading and stable maps | prd-create P03; DS07 |
| PC08 | The TRD is created after the PRD, one file per feature, names only, every entry point verified to have a caller outside the tests, and each feature folder gets its `CLAUDE.md` map | The TRD routes a rule to its code; unverified maps mislead | trd-create T01 to T05 |
| PC09 | A codebase organized by layer gets a restructuring plan (structure-only refactor, code moved by script, ratchet lowered per wave) instead of maps that describe the spread | The source repository went from one rule spread over 10 folders to one folder per PRD area | trd-create `restructure.md` |
| PC10 | Greenfield projects write the PRD by interview first (problem, actors, goals, non-goals, journey, variants, constraints), every Source `planned`; prd-gate C2 fills the Sources as code lands | The PRD exists before the code, so the code is planned against it | prd-create `greenfield.md` |

## Installing and updating the kit (IN)

| ID | Rule | Why | Lands in |
|---|---|---|---|
| IN01 | The kit is one git repository; `install.sh` or `install.ps1` puts the `/ai-kit` skill and the global block on a machine; `/ai-kit install` adapts the kit to each project | One source, adapted per project; improvements flow back to every project | `install.sh`, `install.ps1`, `installer/ai-kit/` |
| IN02 | The skills are copied into each project and committed, so the whole team gets them with the repository, as in the source repository | A skill outside the repository is invisible to teammates | `ownership.md` |
| IN03 | Install detects the stack from manifests and from the project's own scripts; the project's scripts win over the recipe | Teams already know their commands | `install.md` I1 to I4 |
| IN04 | Every command is run once before it is written into `ai-kit.json`; a failing command becomes a question | A wrong command breaks every agent that calls it | `/ai-kit` K05 |
| IN05 | Install never overwrites an existing file: kit-owned files are replaced after a diff, project-owned files are merged | Projects adopt the kit without losing their rules | `ownership.md` |
| IN06 | The linter enforces function size, inheritance, shared state and import direction at the kit's limits with a baseline of today's violations, so CI is green on day one and the baseline only shrinks | Adoption without a big-bang refactor | stack recipes; AR17 |
| IN07 | A manifest records the kit version and the hash of each installed file; update replaces kit-owned files the project did not edit and proposes the rest as diffs | Updates are safe and reviewable | `.ai-kit/manifest.json`; `update.md` |
| IN08 | Install and update work on a branch, show the plan and wait for an explicit yes, commit once, never push | The project owner decides what lands | `/ai-kit` K02, K03, K06 |
| IN09 | Kit improvements found in a project go back to the kit repository first (MAINTAINING.md), then reach every project through `/ai-kit update` | One source of truth for the rules themselves | MAINTAINING.md |
| IN10 | Each CHANGELOG entry may carry an `On update:` line; `/ai-kit update` executes the lines of the entries between the project's version and the kit's | Changes that are not file copies (new folders, new config keys, seeded allowlists) reach existing projects | CHANGELOG.md; update.md |
