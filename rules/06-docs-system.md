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
| DS14 | The human-reading version `docs/prd/prd.html` (one tab per PRD, an overview tab and an open-decisions tab) carries the same words as the markdown, is built from it by `build_prd_html.py` in the same commit (DS42), and is never read by agents | People read the HTML; agents load one small markdown section at a time | repo.md `html`, `html_mode`; gate G5, G6, G10 (hand mode) or G29 (generated); prd-create `reference/html.md` |

## TRD, invariants, testing guide

| ID | Rule | Why | Lands in |
|---|---|---|---|
| DS15 | One TRD file per area (`docs/trd/<area>.md`), 1:1 with the area, wherever its files live. Sections: Where it lives, How it enters the flow, Tests, Must not break, Known pitfalls (no History: git log is the history, DS41). The TRD never repeats PRD rules; it cites IDs | Code map separate from rules | `kit/docs/templates/trd-feature.md` |
| DS16 | `docs/trd/README.md` lists feature, TRD file, folder and the PRD sections it implements; plus cross-cutting files (`infra.md`, `invariants.md`, `testing.md`) | The router from rule to code | `kit/docs/templates/trd-readme.md` |
| DS17 | Before code, a rule change writes a `## Planned (<change>, <branch>)` section at the end of the feature TRD: files to change or create, symbols, entry into the flow, tests to write, invariants new or affected, what must not break. The plan and the agents start from this approved map, not from the current code (format: DS33) | Agents implement a reviewed design | trd-planned.md |
| DS18 | The final task of every plan promotes: PRD markers removed, superseded wording to CHANGELOG, Source filled with real files; TRD "Planned" merged into the body with the names the code actually used | Docs end the delivery true | agent-plan.md "Mandatory final task" |
| DS19 | `docs/trd/invariants.md`: repository rules by kind of change (any change, new env var, new external call, new table, new endpoint, logs, tests...), one line each with its proof (a test file or a principle), stable IDs `I-NN` | The planner and the reviewer check the right invariants for the change | `kit/docs/templates/invariants.md` |
| DS20 | `docs/trd/testing.md`: gate targets, how to run one file, configuration, guards, fakes, patterns that avoid rework | Agents stop rediscovering how to test | `kit/docs/templates/testing.md` |
| DS21 | A code change that moves a file, an entry point or a test updates the feature's TRD and `CLAUDE.md` in the same commit. An area without a TRD gets one the first time someone works on it | Maps stay true by construction | AGENTS.md "Keeping it true" |
| DS22 | One canonical end-to-end flow doc (`docs/flow.md`); when the flow changes, update it | A single overview, never several competing ones | AGENTS.md |
| DS23 | A decision that changes a protected rule or the architecture gets an ADR (`docs/adr/NNNN-<title>.md`) | Protections change deliberately | impact.md "Protected rules" |
| DS27 | ADR quality bars: at least two honest negatives (ones an opponent would recognize), at least two genuinely considered alternatives with what each was good at and the specific reason it lost; 400 to 700 words; a decision with one option is a constraint, not an ADR | An ADR with weak negatives is a sales pitch, not a record | `docs/adr/README.md`; `/adr` skill |
| DS28 | An accepted ADR is never edited to say the opposite: a new ADR supersedes it and the old status becomes `Superseded by NNNN`. Numbering is sequential and never reused | The folder preserves what was believed at the time, including where it was wrong | `docs/adr/README.md` |
| DS29 | New docs start from the templates in `docs/templates/` (PRD section, TRD feature, feature `CLAUDE.md`) | Every file of a kind has the same shape, so agents scan it the same way | `docs/templates/` |
| DS30 | Current schema and contracts have one readable snapshot each (database schema, API schema, message contracts): the framework's own file when it has one, otherwise a dump. `contracts` in `ai-kit.json` lists file and command; `scripts/gates.sh contracts` fails on drift. The TRD links them; agents read the snapshot, never the migration history | The current schema is the sum of every migration; replaying them by reading costs many files and the agent can still get it wrong | `scripts/contract_drift.py` |
| DS31 | `docs/trd/invariants.md` names, per kind of change, the pattern to copy: an existing file that is the reference implementation | An agent that copies a real file of the repository matches its conventions; one that invents from a description does not | trd-create rules-writer |

## The gate script

| ID | Rule | Why | Lands in |
|---|---|---|---|
| DS24 | `scripts/gate.py` runs before every docs commit and blocks on errors: duplicate IDs; INDEX lists a missing file or misses a new ID; a changed rule row without Source or Change via; a rule reworded or removed without a CHANGELOG entry; markdown and HTML differ (when HTML is on); em dashes; a TRD "Planned" section citing an ID that does not exist | Structure is checked by a script, not by attention | skill scripts/gate.py |
| DS25 | Drift that predates the change is a warning, not an error, and is listed at the end as an out-of-scope divergence | The gate never blocks on someone else's debt | gate.py |
| DS26 | The gate also checks the state artifacts: `--pack` (required sections, rule rows copied literally from the PRD), `--rules` (approved rows complete, IDs not reused), `--plan` (every task has Owns, Reviewer, Model; no unknown IDs; size) | Workers' outputs are verified before the next step uses them | gate.py |

## Formats and checks added with prd-flow

| ID | Rule | Why | Lands in |
|---|---|---|---|
| DS32 | Rule tables take an optional fifth column `Example`, defined in prd-flow `reference/prd-writing.md` "Example column"; `approved-rules.md` rows carry it and the HTML renders it | A rule without a worked case can be read two ways | prd-writing.md; interview.md; `docs/templates/prd-section.md`; PC14 |
| DS33 | TRD "Planned" is a table `\| File \| Changes or creates \| Symbols \| IDs \|` with no parameters, intervals or values (those are rules or contracts); "Tests to write" lists the test file and IDs only, never expected values; contracts live only in `design.md` and are linked; plan tasks point to the Planned row by file instead of describing it again | The same detail written in the PRD, the TRD and the plan has three copies that can diverge | trd-planned.md; `docs/templates/trd-feature.md`; agent-plan.md |
| DS34 | `gate.py --status [--prd <folder>] [--state <state>]` prints one line per rule (ID, state, file, Source, Change via); states derive from markers and Source: `proposed`, `approved`, `superseded`, `implemented`. Nothing generated is committed | "What is pending" required reading every section | `gate_status.py`; SKILL.md C1 |
| DS35 | Promote folds amendments into the sections that own the behavior, as defined in prd-flow `reference/prd-writing.md` P3; the CHANGELOG entry says "folded into <files>" | Amendments piled up beside the sections they changed | prd-writing.md; agent-plan.md "Mandatory final task" |
| DS36 | A TRD file over `trd_budget_lines` of `repo.md` (default 250) warns G26 and splits into `docs/trd/<area>/<part>.md`, parts mirroring PRD section groups, with an `<area>/README.md` listing them; `docs/trd/README.md` points to the folder | Large TRD files cost every task that loaded them | trd-planned.md; repo.md; trd-create |
| DS37 | `gate.py --trd` checks the TRD against the code: G23 a cited path matches no tracked file (error), G24 a cited symbol is absent from its row's files, G25 a row cites an ID its file never mentions, G26 budget (warnings) | A TRD that cites files that do not exist sends agents to the wrong place | `gate_trd.py`; workers.md `writer-trd` |
| DS38 | The ratchet counts the rows of `docs/trd/invariants.md` whose proof column says `gap`; `ai-kit.json` `allowlist.invariant_gaps` holds the number and only shrinks. trd-create's rules-writer proposes the lint rule or test for each gap, ranked by hotspots | An invariant with no proof is a wish, and the count was invisible | `scripts/ratchet.py`; `ai-kit.json`; trd-create rules-writer |
| DS39 | `repo.md` "Shared PRDs" lists PRD folders kept identical in a sibling repository; `gate.py --sibling` fails G28 when they differ (line endings normalized) and warns when the sibling path is absent locally | A PRD shared between two repositories can drift | repo.md; `gate_sibling.py` |
| DS40 | The consumer-contract sweep (K08) uses `scripts/gates.sh contracts` when snapshots are configured; trd-create and `/ai-kit install` propose configuring snapshots when `repo.md` lists a sibling consumer | Contract impact was found by reading the sibling's code | impact.md K08; DS30; IN15 |
| DS41 | The TRD template has no "History" section; existing History sections are not appended to | `git log` is the history; the section grew and duplicated it | `docs/templates/trd-feature.md`; trd-create |
| DS42 | With `html_mode: generated`, `scripts/build_prd_html.py` renders README, every PRD in INDEX order and the decisions tab into the `html_template`; the writer runs it and never edits the HTML; G29 (`--check`) replaces G5, G6 and G10 and fails when the file is out of date. `hand` mode keeps the old checks | Hand edits of a 440 KB page were slow and drifted from the markdown (LS12, LS13) | `build_prd_html.py`; prd-writing.md; repo.md `html_mode`; `gate_html_build.py` |
| DS43 | `.github/CODEOWNERS` owns `docs/prd/**` by the "Rule owners" table of `repo.md`; the installer fills it or leaves it commented when there is no owner | Review requests should reach the owner of a rule without anyone remembering | `kit/.github/CODEOWNERS`; WF48 |
