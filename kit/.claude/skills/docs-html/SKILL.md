---
name: docs-html
description: |
  Rebuilds the human reading pages of the PRD (`docs/prd/prd.html`) and the TRD (`docs/trd/trd.html`)
  from the markdown, checks both are current, and commits them. The only place in the kit that
  writes HTML: prd-flow, prd-create and trd-create edit the markdown only and never build or read
  the pages. Builds only, never hand edits; a repository still on `html_mode: hand` is sent to
  `/ai-kit update` to migrate first.
  TRIGGER on: "update the HTML", "rebuild the PRD HTML", "rebuild the TRD HTML", "refresh the reading
  version", "/docs-html", the gate warning G29 or G32 (page out of date), before sharing the PRD or
  TRD with people, or right after /prd-create or /trd-create.
  DO NOT TRIGGER on: changing a product rule (prd-flow), writing the PRD or TRD (prd-create,
  trd-create), or inside a prd-flow run.
---

# Rebuild the reading pages

People read the HTML; agents read only the markdown. The pages are generated, so this skill runs two builds and one check; it never writes, edits or reads a page by hand. A wrong page is fixed in the markdown or in the build, never in the page. Values specific to this repository are in `.claude/skills/prd-flow/repo.md`.

## Rules
| ID | Rule |
|---|---|
| DH01 | Separate from the change flow: prd-flow (every agent and `promote.py`), prd-create and trd-create never build, edit or read the HTML. The default gate and CI only warn when a page is stale (G29 PRD, G32 TRD); `gate.py --html`, run here, is the strict check |
| DH02 | Generated only: `repo.md` `html_mode` must be `generated`. With `hand` or no key, stop and say: run `/ai-kit update`, whose HTML migration renders a preview and switches the mode when accepted. Nothing else is written |
| DH03 | `html` set to `none` (or `trd_html` set to `none`) opts that page out: skip it and say so |
| DH04 | One commit with the pages only, never mixed with a markdown change. Nothing to commit when both were already current |
| DH05 | Runs on the main thread, no subagents: it is three commands |

## Steps
| Step | Command or action |
|---|---|
| 1 | Read the Gate config table of `repo.md`: `html_mode`, `html`, `trd_html`, `html_template`. Apply DH02 and DH03 |
| 2 | `scripts/gates.sh html` (builds the PRD page, then the TRD page). An `ERROR` about the template names a template that predates a slot: copy the kit's `docs/templates/prd.html` (`/ai-kit update` does it) |
| 3 | `python .claude/skills/prd-flow/scripts/gate.py --html` until green: G29 and G32 current, no em dash in the pages (G4). Fix the cause in the markdown, never in the page |
| 4 | After a large change, open each page once: every new section in the table of contents, callouts and tables readable at phone width |
| 5 | `git status --short` on the two page paths; when changed, commit `docs: rebuild the PRD and TRD reading pages` with only those files. Report the pages built, the commit, and anything skipped |

## References
| File | Read by |
|---|---|
| `reference/html.md` | only when a page looks wrong: what each build renders (H01 to H15 PRD, T01 to T03 TRD), the markdown it reads, preview flags |
| `.claude/skills/prd-flow/scripts/build_prd_html.py`, `build_trd_html.py` | run by step 2; never edited here |
| `docs/templates/prd.html` | the template both builds render into |
