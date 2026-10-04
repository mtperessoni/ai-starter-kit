# Docs system (DS)

The PRD says what the product does and why; the TRD says where it lives in the code and what must not break; the plan says in which order it gets built. Each fact has one home, and every home is small enough to load alone.

## Authority and layout

| ID | Rule | Why | Lands in |
|---|---|---|---|
| DS01 | Order of authority: constitution, then the PRD on product behavior, then the spec or plan on how and in what order, then the code | Conflicts have a known winner | AGENTS.md |
| DS02 | The PRD is markdown split one file per section, under `docs/prd/<prd-name>/NN-<section>.md`. `docs/prd/INDEX.md` lists every file with its section, its ID ranges and its TRD | An agent loads one section; the index routes | `kit/.claude/skills/prd-create/reference/anatomy.md` |
| DS03 | `docs/prd/README.md` is the human overview (what the product is, documents, state per spec, what weighs most today); `CHANGELOG.md` holds superseded wording | Body stays current; history stays literal | `kit/.claude/skills/prd-create/reference/anatomy.md` |
| DS04 | Docs age. When document, code and request disagree, ask citing both sides; never silently pick one | Stale docs were common and confidently wrong | skill SKILL.md; R02 |

## Rule rows

| ID | Rule | Why | Lands in |
|---|---|---|---|
| DS05 | Rule rows use `\| ID \| Rule \| Source \| Change via \|`. Risks and problems use `\| R-NN · high \| ... \|` | Machine-checkable, Grep-able, one line per rule | prd-writing.md |
| DS06 | IDs are permanent: a new rule takes the next free number of its prefix. Never renumber, never reuse | IDs are cited in code, tests and commits | prd-writing.md |
| DS07 | `Source` names a file (and symbol when it helps), never a line number or a default value. A rule without code yet has Source `planned` | Lines and defaults drift without anyone touching the doc | prd-writing.md; gate |
| DS08 | `Change via` says how the rule changes: values from `repo.md` (for example `code`, `config`, `env`, `prompt`, `backend`, `frontend`) | Routes the plan: a config change needs no code task | repo.md; gate |
| DS09 | Markers: approved without code `*(approved YYYY-MM-DD, pending code)*` at the start of the text, Source `planned`; superseded `*(superseded: <link>, valid until deploy)*`; an answered open question gets `*Decided on YYYY-MM-DD: <decision>, see <ID>.*` at the end; nothing is deleted until promotion | The doc shows what is live and what is coming | prd-writing.md |
| DS10 | Rule text is in product language; a technical term only in backticks and explained | The PRD is read by product people and by agents alike | prd-writing.md; WS |
| DS11 | A change that stays inside a section is an in-place edit; a change that crosses sections becomes an amendment section with a short `> [!IMPORTANT]` note in each affected section pointing to it | Cross-cutting changes stay readable as one unit | prd-writing.md |
| DS12 | The PRD body holds only what is valid today. On promotion, superseded wording moves literally to `CHANGELOG.md` (newest first, with date, approver, branch, reason, IDs) | Agents read only current rules; history stays auditable | prd-writing.md; gate G7 |
| DS13 | Code that exists but has no caller outside tests is not wired: the rule stays `pending code` | "Implemented" claims were often unwired code | classification.md |
| DS14 | The human-reading version `docs/prd/prd.html` (one tab per PRD, an overview tab and an open-decisions tab) carries the same words as the markdown, is edited in the same commit by exact-line edits, and is never read by agents | People read the HTML; agents load one small markdown section at a time | repo.md `html`; gate G5, G6, G10; prd-create `reference/html.md` |

## TRD, invariants, testing guide

| ID | Rule | Why | Lands in |
|---|---|---|---|
| DS15 | One TRD file per feature (`docs/trd/<f>.md`), 1:1 with `src/features/<f>/`. Sections: Where it lives, How it enters the flow, Tests, Must not break, Known pitfalls, History. The TRD never repeats PRD rules; it cites IDs | Code map separate from rules | `kit/docs/templates/trd-feature.md` |
| DS16 | `docs/trd/README.md` lists feature, TRD file, folder and the PRD sections it implements; plus cross-cutting files (`infra.md`, `invariants.md`, `testing.md`) | The router from rule to code | `kit/docs/templates/trd-readme.md` |
| DS17 | Before code, a rule change writes a `## Planned (<change>, <branch>)` section at the end of the feature TRD: files to change or create, symbols, entry into the flow, tests to write, invariants new or affected, what must not break. The plan and the agents start from this approved map, not from the current code | Agents implement a reviewed design | trd-planned.md |
| DS18 | The final task of every plan promotes: PRD markers removed, superseded wording to CHANGELOG, Source filled with real files; TRD "Planned" merged into the body with the names the code actually used | Docs end the delivery true | agent-plan.md "Mandatory final task" |
| DS19 | `docs/trd/invariants.md`: repository rules by kind of change (any change, new env var, new external call, new table, new endpoint, logs, tests...), one line each with its proof (a test file or a principle), stable IDs `I-NN` | The planner and the reviewer check the right invariants for the change | `kit/docs/templates/invariants.md` |
| DS20 | `docs/trd/testing.md`: gate targets, how to run one file, configuration, guards, fakes, patterns that avoid rework | Agents stop rediscovering how to test | `kit/docs/templates/testing.md` |
| DS21 | A code change that moves a file, an entry point or a test updates the feature's TRD and `CLAUDE.md` in the same commit. An area without a TRD gets one the first time someone works on it | Maps stay true by construction | AGENTS.md "Keeping it true" |
| DS22 | One canonical end-to-end flow doc (`docs/flow.md`); when the flow changes, update it | A single overview, never several competing ones | AGENTS.md |
| DS23 | A decision that changes a protected rule or the architecture gets an ADR (`docs/adr/NNNN-<title>.md`) | Protections change deliberately | impact.md "Protected rules" |
| DS27 | ADR quality bars: at least two honest negatives (ones an opponent would recognize), at least two genuinely considered alternatives with what each was good at and the specific reason it lost; 400 to 700 words; a decision with one option is a constraint, not an ADR | An ADR with weak negatives is a sales pitch, not a record | `docs/adr/README.md`; `/adr` skill |
| DS28 | An accepted ADR is never edited to say the opposite: a new ADR supersedes it and the old status becomes `Superseded by NNNN`. Numbering is sequential and never reused | The folder preserves what was believed at the time, including where it was wrong | `docs/adr/README.md` |
| DS29 | New docs start from the templates in `docs/templates/` (PRD section, TRD feature, feature `CLAUDE.md`) | Every file of a kind has the same shape, so agents scan it the same way | `docs/templates/` |

## The gate script

| ID | Rule | Why | Lands in |
|---|---|---|---|
| DS24 | `scripts/gate.py` runs before every docs commit and blocks on errors: duplicate IDs; INDEX lists a missing file or misses a new ID; a changed rule row without Source or Change via; a rule reworded or removed without a CHANGELOG entry; markdown and HTML differ (when HTML is on); em dashes; a TRD "Planned" section citing an ID that does not exist | Structure is checked by a script, not by attention | skill scripts/gate.py |
| DS25 | Drift that predates the change is a warning, not an error, and is listed at the end as an out-of-scope divergence | The gate never blocks on someone else's debt | gate.py |
| DS26 | The gate also checks the state artifacts: `--pack` (required sections, rule rows copied literally from the PRD), `--rules` (approved rows complete, IDs not reused), `--plan` (every task has Owns, Reviewer, Model; no unknown IDs; size) | Workers' outputs are verified before the next step uses them | gate.py |
