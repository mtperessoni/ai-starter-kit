# prd-create workers

Read only the section with your name. You do not talk to the user: anything missing becomes a **gap** in the return, never an assumption. Parallel batches when reads are independent; code only by symbol (`Grep -n`, then `Read` with offset and limit); big files listed in `.claude/skills/prd-flow/repo.md` never whole; the HTML never read. Write docs with Write and Edit only, never through a script; the only script you run is the gate; no worker builds the HTML (`/docs-html` does). Everything you write is in English, product language, no em dash (U+2014). State: `.claude/prd-flow/state/<slug>/`. Format rules: `reference/anatomy.md`.

Stay inside the folders, documents and read budget of your assignment; do not explore beyond it, and do not call ToolSearch.

Return: at most 15 lines of content, then these five fields as the last lines, nothing after:
```
<the content the section asks for>
Status: done | gap | blocked
Files: <paths written, or none>
Commit: <short hash, or none>
Route: none | user: <one question with options> | <worker>: <handoff of at most 10 lines>
Next: <the step the chief runs next>
```
A failing gate is rerun twice; then `blocked` with `Route` to a fresh worker of your role (the error lines as handoff), or `user` when the rule is unclear. A `gap` always carries a `Route`. Where a section says "gaps", put them in `Status: gap` and `Route`.

## scoper

Runs steps 1 and 2. Reads `repo.md`, the source folders and entry points, `changes/`, legacy `specs/`, `docs/`, any `docs/prd/INDEX.md` and `reference/anatomy.md`; writes `state.md` (slug, mode, approver from `git config user.name`, base commit) and `outline.md` (PRDs, sections, ID prefixes, areas). Return: the outline as a table and the questions for the user, each with options and a recommendation, in `Route: user`.

## interviewer

M2 only. Reads `reference/greenfield.md`; prepares rounds of at most 4 questions with a product-language example each, in `Route: user`; when the chief passes the answers in the handoff, writes `interview.md`. Return: the next round or `Status: done`.

## mapper

M1. Inventories ONE area of the code. Input: the area and its folders from `outline.md`.

1. **Batch 1:** `Glob` of the area folders; the entry points (routes, handlers, commands, jobs, public modules); its tests; its configuration and environment reads (`Grep` of the settings access).
2. Follow each entry point by symbol. For each behavior, ask: what triggers it, what the user or the caller experiences, which limit or order applies, what happens on failure, what is stored, what is sent to whom.
3. Write `areas/<area>.md`, at most 120 lines:
   - `## Entry points`: `file::symbol`, one line each.
   - `## Candidate rules`: one per line, product language, `| text | file::symbol | change via |`. Limits with where they are configured, never the default as the rule.
   - `## States and transitions`.
   - `## Failures`: cause, what the user experiences, final state.
   - `## Configuration`: each knob, where it lives, its effect, how it changes.
   - `## Data and privacy`: what is stored, logged, sent to third parties; masking.
   - `## Tests`: folders and what they cover.
   - `## Surprises`: code with no caller outside tests, contradictions with docs, behavior that looks wrong, each with evidence. Do not fix anything.
4. Ceiling: about 40 tool calls.

Return: candidate rules count, the surprises (at most 10 lines), gaps.

## doc-reader

M3. Reads ONE set of existing documents (specs, tickets, an old PRD, an HTML). Input: the paths from `outline.md`.

1. Read by heading (`Grep -n "^#"`, then ranges). Never read a document over 100 KB whole.
2. Write `areas/doc-<name>.md`, at most 120 lines: intended behaviors as candidate rules (`| text | doc::heading | change via |`), decisions with dates, open questions, and claims that need checking against code (`## To verify`).
3. Ceiling: about 30 tool calls.

Return: candidate rules count, claims to verify, gaps.

## section-writer

Writes the step sections assigned to you. Input: `outline.md`, the `areas/*.md` of your sections, `repo.md`.

1. For each assigned section, write `docs/prd/<prd>/NN-<slug>.md` following "Anatomy of a step section" in `reference/anatomy.md`, starting from `docs/templates/prd-section.md`.
2. Turn candidate rules into rule rows: one behavior per row, product language, IDs from `-01` with the prefix in the outline, Source and Change via from the area file. Merge duplicates; split compound ones. Add the Example column (prd-flow `reference/write.md` "Rule rows") for every rule with a number, a branch or a failure path. A rule that comes only from a document (`areas/doc-*.md`) and is not proven by code is written `*(proposed)*` at the start of the Rule cell with Source `planned`; a rule from the interview (M2) or proven by code is not.
3. Every surprise in your areas becomes a `> [!CAUTION]` callout in the section where it hurts, and a line in `writing.md` under `## For open questions` (the crosscut-writer turns them into Q- and R- rows).
4. Verify each Source with one `Grep` of the symbol; a symbol with no caller outside tests is stated in the rule ("not wired yet") and listed as a surprise.
5. Append to `writing.md`: files written, ID ranges, surprises.

Return: files, ID ranges, gaps.

## crosscut-writer

Writes the cross-cutting sections of one PRD: summary, glossary, scope, end-to-end journey, states and failures, audit cost and privacy, configuration, tenant matrix (if any), problems of the current structure, spec versus code, risks, open questions. Input: `outline.md`, all `areas/*.md` of the PRD, `writing.md`, the step sections (by heading and rule table only).

1. Glossary: every term used in a rule, with its name in code.
2. Journey: numbered steps that match the step sections one to one, plus one mermaid flowchart with failure exits.
3. Configuration: every knob from the areas, grouped by where it changes.
4. Problems, risks, open questions: from the surprises and the CAUTION callouts; each open question has the adopted default (today's behavior) and what it blocks; each problem points to the question that decides it.
5. Spec versus code: every `## To verify` claim from the doc-readers that the code contradicts.

Return: files, ID ranges, the 5 heaviest problems in one line each, gaps.

## index-writer

Writes `docs/prd/INDEX.md`, `docs/prd/README.md` and `docs/prd/CHANGELOG.md` (header only when new), following `reference/anatomy.md`. In M4, adds the new PRD to the existing files without touching the other PRDs' rows. Runs `python .claude/skills/prd-flow/scripts/gate.py` until it has no error (a WARNING that the HTML is missing or stale is expected: the page is built later by `/docs-html`, never here). Never builds, edits or reads the HTML.

Then commit all the PRD files with `docs(prd): <scope> PRD from <source>` (the chief gives scope and source in the handoff) and return the hash in `Commit`.

Return: files, the gate's last line, gaps.
