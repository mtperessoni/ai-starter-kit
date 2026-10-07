# HTML reading version (html-writer)

People read `docs/prd/prd.html` (path in `repo.md` `html`); agents never do. The page is generated from the markdown by `.claude/skills/prd-flow/scripts/build_prd_html.py`: the html-writer runs the build, it never writes or edits the HTML. A wrong page is fixed in the markdown or in the build, never in the page.

## Run and check
| Step | Command |
|---|---|
| Build after any change under `docs/prd/` | `python .claude/skills/prd-flow/scripts/build_prd_html.py` |
| Check the page is current (what G29 runs) | `python .claude/skills/prd-flow/scripts/build_prd_html.py --check` (exit 1 when it differs from a fresh render) |
| Preview elsewhere without touching the repository | `--root <repo> --out <file> [--template <file>]` |

Commit the page in the same `docs(prd)` commit as the markdown. The sidebar and footer name the last commit touching `docs/prd/` and its date (never the clock); `--check` ignores those `data-stamp` values, since a page committed with its markdown can only name the commit before its own.

## What the build guarantees
| ID | Guarantee |
|---|---|
| H01 | Template: `html_template` (default `docs/templates/prd.html`) with the slots `{{PROJECT}}`, `{{TABS}}`, `{{VIAS}}`, `{{PANELS}}`, `{{REPO}}`, `{{COMMIT}}`, `{{DATE}}`, `{{PRD_DIR}}`; its `<style>` and `<script>` are kept as they are. A template without `{{PANELS}}` predates the build: copy the kit's template |
| H02 | Deterministic: two builds of the same markdown give the same bytes; stdlib only |
| H03 | Tabs: `overview` first, one per PRD in `INDEX.md` order (`data-tab` and `data-panel` equal to the PRD folder), `decisions` last. Tab title `PRD N · Name` and subtitle from the `## PRD N · Name (scope)` heading of INDEX |
| H04 | One `<section id="<letter>-<file slug>">` per section file, in INDEX order, with `<h2><span class="num">NN</span>Title</h2>` from the file's `## NN. Title`; the panel's `toc` lists every section. Each PRD has its own letter (`a-`, `b-`) |
| H05 | Prose (paragraphs, lists, `###` headings) goes in `div.explain`; the first paragraph of a section is the `lede`; ordered lists are journey timelines (`ol.story`, numbering kept) |
| H06 | Callouts: `> [!CAUTION]` is `callout risk`, `> [!WARNING]` `callout warn`, `> [!IMPORTANT]` `callout info`, `> [!NOTE]` and `> [!TIP]` `callout note`. A first paragraph that is entirely bold becomes the callout title; `*(checked in code)*` becomes the `checked in code` badge |
| H07 | Rule tables: a table whose rows start with a rule ID (`PAY-01`, `R1-04 · high`) is `table.rules`; each row is `<tr data-via="…" data-sev="…"><td>ID</td><td class="rule">…</td>…` (one row per ID, the form the gate reads), the Change via column is a tag, the Source and Evidence columns break at `/` and `::`. Risks and problems carry `data-sev` from `ID · level` |
| H08 | Example column: rendered as its own column (`td.ex`); four-column tables stay valid |
| H09 | Every other table (glossary, outcomes, configuration, matrices, questions with `Q1` ids) is `table.mx`; an ID in the first column is shown as a pill but never as a rule row |
| H10 | Text: HTML is escaped; backticks become `<code>`, bold `<b>`, italics `<em>`, markers `*(...)*` become `<i class="mk">` pills (pending, superseded, proposed, checked), IDs never break across lines |
| H11 | Links: to another section file become `<a href="#<id>">`, across PRDs `<a href="#<id>" data-go="<tab>">`; to `README.md` go to the overview tab; to other files (TRD, CHANGELOG) a path relative to the page; external links open in a new tab |
| H12 | Mermaid blocks go in `<pre class="mermaid">` with the same source; other fenced blocks in `pre.code` |
| H13 | Overview tab from README `## Overview`, one section per `###` (`### 00. Title` keeps its number); the hero is the README title and the first sentences of section 00 |
| H14 | Decisions tab from README `## Open decisions`, one section per `###`, rows like `Q3 Should…` split into an ID column; then every PRD's `NN-open-questions.md` table, ranked by the highest severity of the risks and problems each question blocks. Question rows are rule rows for the filter and the counters, never gate rows |
| H15 | Phone (390 px) and desktop, light and dark: no horizontal page scroll; on narrow screens tables become stacked cards with column labels |

## Markdown the build reads
The anatomy in `anatomy.md` as written: `## NN. Title` per file, `###` subsections, paragraphs, `-` and `1.` lists (nested by indentation), pipe tables with a separator row (`\|` for a literal pipe), GitHub callouts, fenced code and mermaid, inline code, bold, italics, markers and relative links. Raw HTML in the markdown is escaped, not rendered.

## Steps
1. Write or change the markdown; never touch `prd.html`.
2. Run the build, then `--check` (or the gate, which runs G29 when `html_mode` is `generated`).
3. Open the page once after a large change: every new section in the toc, callouts and tables readable on a phone width.

A repository whose `repo.md` still says `html_mode: hand` (or has no `html_mode`) keeps the hand-written page and the gate's G5, G6 and G10 checks until `/ai-kit update` migrates it.
