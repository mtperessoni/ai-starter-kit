# HTML reading version (html-writer)

People read `docs/prd/prd.html` (path in `repo.md` `html`); agents never do. It carries the same words as the markdown, one tab per PRD, and the gate compares every rule row word by word.

## Rules
| ID | Rule |
|---|---|
| H01 | Start from `docs/templates/prd.html` the first time; afterwards only extend or edit the existing file. Never rewrite the whole file, never touch the `<style>` or `<script>` blocks |
| H02 | Write with Write (first time) and Edit (afterwards). Never generate the HTML with a script |
| H03 | Tabs: `overview` first, one per PRD (`data-tab` and `data-panel` equal to the PRD folder name), `decisions` last |
| H04 | One `<section id="<letter>-<slug>">` per markdown section file, in INDEX order, with `<h2><span class="num">NN</span>Title</h2>`; the panel's `toc` lists every section. Each PRD uses its own id letter (`a-`, `b-`) so ids never collide |
| H05 | Explanatory prose goes in `<div class="explain">`, the first paragraph with `class="lede"`. `> [!CAUTION]` becomes `<div class="callout risk">` with `<span class="verified">checked in code</span>` when the markdown says so; `> [!IMPORTANT]` becomes `<div class="callout info">` |
| H06 | Rule tables: `<div class="tw"><table class="rules">` with `ID, Rule, Source, Change via` headers; each row `<tr data-via="<change via>"><td>ID</td><td>text</td><td>source</td></tr>` (the script adds the Change via column). Risks and problems also carry `data-sev="high\|medium\|low"` |
| H07 | Other tables (glossary, outcomes, configuration, matrices) use `<div class="tw"><table class="mx">` |
| H08 | Text conversion: backticks become `<code>`, bold becomes `<b>`, markers become `<i>(...)</i>`, links to other sections become `<a href="#<id>">`, links across PRDs `<a href="#<id>" data-go="<tab>">` |
| H09 | Mermaid diagrams go in `<pre class="mermaid">` with the same source as the markdown block |
| H10 | The rule text has the same words as the markdown row (the gate tokenizes both, so markup does not matter, words do) |
| H11 | Fill every `{{...}}` placeholder of the template: project name, repo, branch, commit, date, headlines from the README and summaries |
| H12 | Open questions appear in the `decisions` tab as rule rows with their `Q...` ids, ranked by risk, mirroring README "Open decisions" |

## Steps
1. First time: copy the template with Write, fill the sidebar (one tab button per PRD) and the overview panel from `README.md`.
2. For each PRD: one panel, its `toc`, one section per markdown file, in INDEX order. Work one PRD at a time; for a large PRD, one Edit per section.
3. The decisions panel from README "Open decisions" and the open questions files.
4. Run `python .claude/skills/prd-gate/scripts/gate.py`: every `G5`, `G6` or `G10` error is a row whose words differ; fix the HTML row, never the markdown.
