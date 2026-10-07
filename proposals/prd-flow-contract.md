# prd-flow v4 · implementation contract

Implements every finding of `proposals/prd-gate-and-docs-review.md` (A01 to A15, B01 to B13, C01, C02). Each decision below is the single definition of a format or behavior; skills, references, templates, scripts and tests follow it word for word. Agents cite decisions by ID (K-NN). Paths are relative to the kit repository; `<skill>` is `kit/.claude/skills/prd-flow`.

## Names and files
| ID | Decision |
|---|---|
| K-01 | The skill is `prd-flow` (was `prd-gate`, finding A15). `scripts/gate.py` keeps its name: it is the gate. State lives in `.claude/prd-flow/state/<slug>/`. Prose may say "formerly prd-gate" only in the installer migration, README and CHANGELOG |
| K-02 | `gate.py` stays the single CLI entry, under 500 lines; its checks move into sibling modules in `<skill>/scripts/` named after their responsibility (for example `gate_rules.py`, `gate_trd.py`, `gate_interview.py`, `gate_remote.py`, `gate_status.py`), moved by script, never retyped. Stdlib only |
| K-03 | New `repo.md` "Gate config" keys, each with a default in `gate.py` `load_config` so older adapters keep working: `proposed_marker` (default `proposed`), `html_mode` (`generated` or `hand`, default `hand` when the key is absent, `generated` in the kit's repo.md), `html_template` (default `docs/templates/prd.html`), `trd_budget_lines` (default `250`) |
| K-04 | New gate codes. Errors: `Q3` interview not closed; `Q4` approved row not applied literally; `G23` TRD path matches no tracked file; `G28` shared PRD differs from its sibling; `G29` generated HTML out of date; `G30` a `proposed` rule left at `--final`. Warnings: `G24` TRD symbol not found in its file; `G25` TRD row cites an ID its file never mentions; `G26` TRD file over `trd_budget_lines`; `G27` an ID or change number is already used on a remote branch |

## Cases and route (A01, A10, A12, A14)
| ID | Decision |
|---|---|
| K-10 | C0 only when `docs/prd/INDEX.md` does not exist. In a repository with PRDs, a new product, module or incoming spec document is **C5 size L, new PRD variant**: the surveyor sweeps the incoming document against every existing PRD (K-20) and the writer may follow `prd-create` M4 to lay out the new folder, but every rule passes confrontation and interview first |
| K-11 | Rules that come only from documents (prd-create M3 and M4, not proven by code) are written with the marker `*(proposed)*` and Source `planned`. A proposed rule is C5 input, never C2: prd-flow confronts and interviews it per section and replaces the marker with `*(approved YYYY-MM-DD, pending code)*`. `--final` fails on any proposed rule (G30). Greenfield M2 rules come from the interview, so they are approved, not proposed |
| K-12 | C5 route steps: 1 state; 2 surveyor; 3 confrontation; 4 interview, then `decisions.md` (K-31); 5 `writer-prd` (PRD, HTML build, CHANGELOG, INDEX, `decisions.md`, gate, `--applied`, commit `docs(prd)`); 6 user confirms the rule diff plus the non-table summary; 7 `writer-trd` (Planned, `gate.py --trd`, commit `docs(trd)`); 8 planner; 9 plan approval; 10 execution. The TRD is never written before step 6 |
| K-13 | C1 answers say, per rule cited, "verified in code" (one Grep found the Source symbol with a caller outside tests) or "not verified" |
| K-14 | The surveyor runs on `opus` for size L (reason: the confrontation is the step whose miss costs the most), `sonnet` for M |

## Confrontation (A04, A05, A07, A08, A09)
| ID | Decision |
|---|---|
| K-20 | Impact sweep **K11 semantic**: from `docs/prd/INDEX.md` read the Section column of every PRD file (not only grep hits), pick up to 8 section files whose subject could interact (same entity, actor, state, number or journey step), read their rule tables, and list each rule the proposal would contradict, constrain or duplicate. The confrontation always carries `Checked: <files and ID ranges read>` and `Conflicts: <ID: why>` or `Conflicts: none found in the checked files` |
| K-21 | Impact sweep **K12 history**: `Grep` each in-scope ID in `docs/prd/CHANGELOG.md`; the confrontation shows, per ID with history, `Decided <date>: <why>; rejected: <alternative> (<why>)` from the entry's Decisions block |
| K-22 | K06 also looks at remote branches: for each in-scope ID and the next free IDs and change number, `git for-each-ref refs/remotes` (most recent 30) and `git grep -l` the ID in `docs/prd` and `changes` of each ref. A hit is shown in the confrontation and asked about. `gh pr list` is used only when `gh` is available |
| K-23 | Pre-interview states per dimension: `doc: <source>` (the PRD states it and the change does not touch it), `assumed: <proposed default and where it comes from>` (inferred from current code, or the change touches it), `open: <question with scenario and recommended default>`, `n/a: <reason>`. A dimension the change touches is never `doc`. The confrontation shows the assumed ones in one block of at most 6 lines that the user confirms or corrects explicitly before the interview |
| K-24 | `repo.md` section "Rule owners" (`| PRD files (glob) | Owner | How they approve |`). When the change touches an owned section and the approver is not the owner, the confrontation names the owner, step 4 does not close until the user states the owner agreed, and the CHANGELOG entry records `decided by <owner>, written by <approver>` |

## Interview record (A02, A05)
| ID | Decision |
|---|---|
| K-30 | `state/<slug>/interview.md` format, parsed by `gate.py --rules` (reads the `interview.md` beside the given approved-rules file):<br>`## Dimensions` table `\| Dimension \| State \| Answer \|`, Dimension starting with its ID (`D05 failures`), State one of `user`, `doc`, `assumed-confirmed`, `n/a`, `question`. `question` requires a `Q-` ID in Answer that exists in `approved-rules.md` or the PRD. `open` and `assumed` are not allowed at closure.<br>After the table, one line `Confirmed: <name> · <YYYY-MM-DD> · "<the user's words>"`.<br>The first Dimensions table lists D01 to D15 plus every ID of `repo.md` "Extra interview dimensions". A short C5 appends `## Dimensions (YYYY-MM-DD)` with only the reopened dimensions (at least one) and its own `Confirmed:` line.<br>Q3 when the file is missing, a required dimension is missing, a state is not allowed, or a table has no `Confirmed:` line after it |
| K-31 | `changes/NNN-<slug>/decisions.md`, committed with `docs(prd)` (step 4 allocates the change folder; the planner reuses it). Template `kit/docs/templates/change-decisions.md`:<br>`\| ID \| Question \| Decision \| Rejected alternative \| Why \| Rules \|` with IDs `DEC-NN`. One row per trade-off decided and per interview answer that chose between real options. The Promote task copies the rows into the CHANGELOG entry under `Decisions:` |
| K-32 | `gate.py --rules <approved-rules.md> --applied` (Q4): every rule row of the file exists in the PRD file named by its `## <file>` heading with identical cells (ID, Rule, Source, Change via, Example when present), whitespace normalized. The writer runs it after writing; step 6 shows its result |

## R09 and the short C5 (A06, C01, C02)
| ID | Decision |
|---|---|
| K-40 | New rule **R09**: any behavior not covered by the approved rules, proposed by anyone (the user, an executor, a reviewer, this conversation), stops the tasks that touch it and enters the short C5 before code. A rule gap is never resolved by a task |
| K-41 | Short C5: E08 stop the touching tasks and dispatch the surveyor in short mode (K01, K02, K11, K12 on the touched rules only; confrontation of at most 15 lines); E09 interview of the reopened dimensions (K-30 dated table and confirmation) and new `DEC-` rows; E10 `writer-prd` applies the dated section of `approved-rules.md`, `--applied` green, then `writer-trd`, then the planner appends tasks. The review counter does not reset without explicit approval |
| K-42 | E05: a gap that is a rule or contract divergence goes to the short C5; only a missing technical detail becomes a question or a task. V06 covers any behavior change, not only the safety posture. The "Plan execution rules" line reads: "Any behavior outside the approved rules, safety included, stops and goes to the short C5 (R09)" |
| K-43 | Ceilings have one home, `review.md` V08: executor and fixer about 50 tool calls or 30 minutes, reviewer about 40 tool calls. Every other file cites V08 instead of restating numbers |

## PRD and TRD formats (B03 to B08, B12)
| ID | Decision |
|---|---|
| K-50 | Rule tables take an optional fifth column `Example`: `\| ID \| Rule \| Source \| Change via \| Example \|`, one line `<given> → <expected outcome>` in product language. Required by the interview exit and the writer for rules with a number, a branch or a failure path; the D15 answer lands there. Four-column tables stay valid. `approved-rules.md` rows carry it. The HTML renders it |
| K-51 | TRD "Planned": table `\| File \| Changes or creates \| Symbols \| IDs \|`; no parameters, intervals or values (they are rules or contracts). "Tests to write": test file and IDs only, never expected values (they are the PRD Example). Contracts live only in `design.md` and are linked. Plan tasks point to the TRD Planned row by file instead of describing it again |
| K-52 | `gate.py --status [--prd <folder>] [--state <state>]` prints `ID · state · file · Source · Change via`, one line per rule, states derived from markers and Source: `proposed`, `approved` (pending code), `superseded`, `implemented`. No generated file is committed |
| K-53 | Promote folds amendments: each amendment row moves to the step section that owns the behavior (ID unchanged, markers removed, Source filled); an amendment file whose rows all moved is deleted after its prose is merged into the step prose; the `[!IMPORTANT]` pointers go; INDEX follows; the CHANGELOG entry says "folded into <files>" |
| K-54 | `gate.py --trd`: G23 a backticked token under `docs/trd` that looks like a path (has `/` or a file extension) matches no tracked file (suffix match after stripping a leading `.../`; `*` globs by fnmatch), outside the Planned section and outside rows marked `creates`; G24 a backticked symbol in a `Main symbols` or `Symbols` column absent from the row's files; G25 an ID in the row's `IDs` column absent from the row's files (the module cites the IDs it implements); G26 a TRD file over `trd_budget_lines`. CI runs it |
| K-55 | An area whose TRD passes the budget splits into `docs/trd/<area>/<part>.md`, parts mirroring PRD section groups, plus `docs/trd/<area>/README.md` listing them; `docs/trd/README.md` points to the folder. The TRD template has no "History" section (git log is the history); existing History sections are not appended to |

## HTML (B01)
| ID | Decision |
|---|---|
| K-60 | `<skill>/scripts/build_prd_html.py` (stdlib only) renders `docs/prd/` (README overview, every PRD in INDEX order, the decisions tab) into the template `html_template`, writing `repo.md` `html`. API: `render(root: Path, cfg: dict) -> str`; CLI `python build_prd_html.py [--check]`; `--check` exits 1 when the file differs from a fresh render. Output is deterministic: the commit and date come from the last commit touching `docs/prd/`, never the clock |
| K-61 | Rendering covers everything H03 to H12 of `prd-create/reference/html.md` asked of the hand writer: tabs, toc, one section per file with number, lede, explain blocks, callouts (`risk`, `info`, `checked in code`), rule tables with `data-via` and `data-sev`, the Example column, other tables as `mx`, code, bold, italics markers, links within and across PRDs, mermaid, the decisions tab from README "Open decisions" and the open questions. The `<style>` and `<script>` of the template are kept, improved where the review of the rendered page asks for it |
| K-62 | Quality bar: rendered from the real PRD of `C:/Projects/agora-consulta-fe/docs/prd/` (read only, render into the scratchpad), the page is at least as complete and as polished as that repository's hand-made `prd.html`, on desktop and on a 390 px phone, light and dark, with no horizontal page scroll, no raw markdown left, no broken link or anchor |
| K-63 | With `html_mode: generated`, the gate replaces G5, G6 and G10 by G29 (`build_prd_html.py --check` semantics); with `hand` the old checks stay. The writer runs the build and never edits the HTML; `/ai-kit update` migrates a hand HTML to generated after showing the user a rendered preview |

## Team and repository guards (A08, A09, A11, B09, B10, B11, B13)
| ID | Decision |
|---|---|
| K-70 | `gate.py --rules` warns G27 when an ID new to the current PRD exists in `docs/prd` of a remote branch; `gate.py --change <dir>` warns G27 when a `changes/NNN-*` with the same number exists on a remote branch |
| K-71 | `repo.md` section "Shared PRDs" (`\| PRD folder \| Sibling repository path \| Source of truth \|`). `gate.py --sibling`: G28 when the shared folder differs from the sibling's (line endings normalized); a warning when the sibling path is absent locally |
| K-72 | Commit trailers: a commit that touches the source folders (`ai-kit.json`) carries `Rules: <IDs>` or `Case: none (<reason in at most 8 words>)`. `kit/scripts/commit_trailers.py <base>..<head>` checks it; `scripts/gates.sh trailers [range]` runs it; the kit CI runs it on pull requests. The executor's proposed commit message includes the trailer |
| K-73 | The ratchet counts rows of `docs/trd/invariants.md` whose proof column contains `gap`; `ai-kit.json` `allowlist.invariant_gaps` holds the number, shrink-only (error when it rises, a message to lower it when it drops). trd-create's rules-writer proposes the lint rule or test for each gap, ranked by `gates.sh hotspots` |
| K-74 | K08 uses `scripts/gates.sh contracts` when snapshots are configured; trd-create and `/ai-kit install` propose configuring contract snapshots when `repo.md` lists a sibling consumer |
| K-75 | `scripts/gates.sh retro` adds a `doc_reads` finding: the doc and skill files read most in the run (Read calls and rereads per file, with bytes), top 5, flagged when one file is read more than the threshold in `ai-kit.json` retro thresholds |
| K-76 | `CODEOWNERS` template in the kit with `docs/prd/**` owned by the "Rule owners" of `repo.md`; the installer fills it or leaves it commented when there is no owner |

## Migration (A15, B01)
| ID | Decision |
|---|---|
| K-80 | `/ai-kit update` on a repository with `.claude/skills/prd-gate/`: shows the list, then moves the project-owned `repo.md` into `.claude/skills/prd-flow/`, deletes the old skill folder, moves `.claude/prd-gate/state/` to `.claude/prd-flow/state/`, replaces `prd-gate` with `prd-flow` in the project files the kit manages (CLAUDE.md, AGENTS.md, constitution, settings, gitignore, ai-kit.json, docs/prd/README.md, docs/trd, docs/templates), adds the K-03 keys with the defaults, and offers the HTML migration (K-63). `doctor` reports a leftover `prd-gate` folder or reference |

## Eval (A13)
| ID | Decision |
|---|---|
| K-90 | New small-fixture scenarios: **S5** a rule change whose request conflicts with a rule in another section phrased with other words; **S6** an incoming spec document (a file in the fixture) to implement, which conflicts with an existing rule (new PRD path, K-10); **S7** a rule change that leaves a dimension open that `decisions.md` does not answer. `expected.json` gains `conflict_ids` (S5, S6) and `gap_topic` (S7) |
| K-91 | New metrics: `conflict_found` (an ID of `conflict_ids` appears in the assistant text or in files under the state folder or `changes/` before the first `docs/prd` commit, or the PRD diff supersedes or edits it), `contradiction_left` (judge: a live conflict rule still contradicts a new rule; lower is better), `gap_recorded` (judge: the PRD diff holds a `Q-` row or a rule covering `gap_topic`). R4 accepts `prd-flow` or `prd-gate` |
| K-92 | `eval/arms-flow.json`: arm `GATE` (ref `fix/existing-repo-adoption`, protocol `arms/living-gate.md`, the old name) and arm `FLOW` (ref `HEAD`, protocol `arms/living.md`), scenarios S5, S6, S7, one rep each, small fixture (six runs; cost and time are compared on the same runs). The grader resolves the gate path for either skill name |
