# Execution contract: one-pass interview, orphans, track B and gates (2026-10-09)

Implements every item of [`plan-interview-one-pass.md`](plan-interview-one-pass.md) and the G track of [`../eval/AUDIT-prd-flow-run-2026-10-09.md`](../eval/AUDIT-prd-flow-run-2026-10-09.md) section 3. Each agent reads this file, the item rows it owns in those two files, and its owned files. Branch `feat/one-pass-interview`.

## Decisions (Q1 to Q6 of the plan, taken as recommended on 2026-10-09)
| ID | Decision |
|---|---|
| Q1 | The interview is answered in the chat, free text by number. No AskUserQuestion in the interview |
| Q2 | At most 8 decisions and at most 8 assumed lines per sheet; more decisions means the sheet recommends splitting the change |
| Q3 | One follow-up sheet at most; an item still open after it becomes a `Q-` row with the recommended default, visibly open |
| Q4 | The 16 dimensions are removed (table, record, gate Q3 form check); one blind-spot line in the surveyor file; clinical safety stays a protected rule where a repo has it |
| Q5 | New branch `feat/one-pass-interview` from `origin/main` (730dd4a); this plan supersedes the round 0 and question lint of 730dd4a |
| Q6 | Track B ships on the same branch |
| D1 | BC1 is applied where no script reads the format: DEC rows only in `decisions.md`, no `Execution:` paragraphs and no plan header copy of the orchestration rules, one CHANGELOG entry per slug. The PRD pending marker and the TRD Planned section stay: promote, `--hold` and the TRD path gate read them (deferred, recorded in CHANGELOG) |
| D2 | Surveyor and docs keep `model: opus` with the written reason in the agent file (the user chose opus for surveying and planning on 2026-10-08); executor and reviewer sonnet, recheck haiku |

## Interfaces every agent must agree on
### State folder of a C5 after this change
| File | Writer | Content |
|---|---|---|
| `pack.md` | surveyor `full` | As today (`impact.md` "Format of `pack.md`") |
| `sheet.md` | surveyor `full` | The decision sheet, format below. The surveyor writes nothing else in the state folder besides `state.md` `## Survey` (a 10-line summary: case, size, owner, protected rules, sheet path, `Python:` line) |
| `answers.md` | docs `apply` | `## Reply 1` (the user's message verbatim), `## Reply 2` only after the follow-up, then `## Resolution`: a table `\| Item \| Answer \| From \|` with one row per sheet item (`1`..`N`, `A1`..`An`, `scope`); `Answer` is the chosen option letter, `accepted` (assumption kept), the correction words, `default` (taken through `ok`) or `open Q-<ID>`; `From` is `Reply 1`, `Reply 2` or `ok` |
| `sheet-2.md` | docs `apply` | The follow-up sheet: same format, only the unclear items and new decisions; at most one |
| `rules.md` | docs `apply` | The approved rule rows, written once from sheet plus answers (no `Confirmed:` line, no Dimensions table). `delta.md` is no longer written |
| `decisions.md` | docs `apply` | The only home of DEC rows (rendered by `state_record.py` as today, or written directly if the renderer is reduced) |
| `approved-rules.md` | `state_record.py render` | As today, from `rules.md` |
| `interview.md` | nobody | Removed |

### Format of `sheet.md`
Section headings and field labels are read by the gate from `repo.md` Gate config key `sheet_labels` (comma list, in this order), default English: `What changes in the rules, What does not change, Assumed, Decisions, How to answer, Today:, Why it matters:, Example:, (Recommended)`. The illustrative sheet in the plan ("Format of `sheet.md`") is the canonical example.

| Block | Machine-checkable shape |
|---|---|
| Title | `# <the change in one line>` |
| Diff | `## <What changes in the rules>`: a table whose header has 4 columns (`Rule`, `Today`, `Becomes`, `Kind`, localized); `Kind` is one of `rewrites`, `adds`, `supersedes`, `removes` (always English tokens); `Today` of an `adds` row is `(none)` |
| Scope | `## <What does not change>`: at least one `- ` line (mandatory) |
| Assumed | `## <Assumed>`: lines `- A<n> <text>`, at most 8 |
| Decisions | `## <Decisions>`: items `**<n>. <title>** · rule <ID>[, <ID>]` (rule part optional only for a mechanism decision, then `· mechanism`), each with a `<Today:>` line, a `<Why it matters:>` line, at least two `- <L>) ` option lines exactly one carrying `<(Recommended)>`, an `<Example:>` line; at most 8 items |
| Interactions | Optional `Interacts with: <n>` line inside a decision (I11 S6) |
| How to answer | `## <How to answer>`: the fixed line of the plan, localized |

### Sheet lint (gate, replaces Q6 to Q9)
| Code | Check | Level |
|---|---|---|
| S1 | Every decision has Today, Why it matters, Example, at least two options and exactly one Recommended | error |
| S2 | Every rule ID the pack marks as touched or conflicting (K01, K11, K14) is a row of the diff table | error |
| S3 | No two decisions name the same rule ID with the same scope words; at most 8 decisions, at most 8 assumed lines | error |
| S4 | No `plain_words` term in a decision title or option line (context lines may carry IDs and code names) | warn |
| S5 | A decision whose text has a comparison word (above, below, more than, at least, high, low, after, before, their `repo.md` language equivalents are not required) names a number or a category in its options | warn |
| S6 | A decision listed in another's `Interacts with:` exists | error |
| Q3 (new) | Every sheet item (`1`..`N`, every `A<n>`, `scope`) has a row in `answers.md` `## Resolution`; a mechanism term (env var, switch, flag, configuration key, table, endpoint, column) in `rules.md` or `decisions.md` that is not in the sheet or the answers is an error (D2 of the audit) | error |

Entry points: `gate.py --sheet <slug>` (S1 to S6), `gate.py --rules <slug>` keeps its rule-row checks and runs the new Q3. `gates.sh docs <slug>` calls both. `gate.py --questions` is removed (an alias to `--sheet` for one release is fine).

### Chief flow of a C5 (SKILL.md is the only home; dispatch.md holds the prompts)
| Step | What |
|---|---|
| 0 | Where the change lives is the first check: the chief names the repository (or repositories, one slug, one sheet, rows grouped by repo via `.ai-kit/repos.json`) before any survey. A second slug in the same working tree is refused: a worktree per slug |
| 1 | Surveyor `full`. The prompt adds `Decided in conversation: "<user's verbatim words>"` (every decision the user already stated in this conversation) and `Preferences: "<verbatim>"` (the user's feedback memories that bear on the request); each becomes an Assumed line, never a decision |
| 2 | The chief reads `sheet.md` and prints it as its message, verbatim, and ends the turn. No AskUserQuestion, no round 0, no separate change question ("keep today's rule" is an option of decision 1 when relevant) |
| 3 | The user's reply goes verbatim to docs `apply` (`Answers: <verbatim>`) |
| 4 | Docs `apply` returns either done (rule diff as written plus the wave table) or `Route: user: sheet-2.md`: the chief prints `sheet-2.md` and ends the turn; the reply goes to the same docs agent (SendMessage) as `Answers 2:`; after it, open items become `Q-` rows |
| 5 | The chief prints the rule diff as written (today, then new) plus the wave table: one approval. A correction is docs `adjust: <words>` in place |
| 6 | Execution as today |
| Explain | When the user does not understand an item, the chief may read the PRD rows the sheet cites and explain with today's rule and an example; never the same question in new words (replaces "Forbidden: preparing a question") |

### Docs modes
`apply` (sheet plus answers to answers.md, rules.md, decisions.md, PRD, TRD Planned, plan; checks the combination of the answers per `Interacts with:` before writing; never adds a mechanism outside the sheet or the answers), `adjust: <words>` (in-place correction), `c4`, `fold`, `context` (fan-out) stay. `rules`, `prd-plan`, `trd-plan` and the folded path are removed.

### Commands and harness rules
| Rule | Value |
|---|---|
| Interpreter | The only interpreter any runtime file or prompt names is the output of `scripts/gates.sh python` (it resolves `ai-kit.json` `commands.python`). No `a \|\| b` fallback chains in instructions |
| Commit | Write the message with Write to `<state>/msg-<task>.txt`, then `git add <paths>` and `git commit -F <state>/msg-<task>.txt` as separate calls. Never `-F -`, never a heredoc or a here-string |
| One command per call | Never chain an edit, a format, a test or a commit with `&&` in one call |
| Long commands | Background with an explicit timeout longer than the run, woken by the completion notice, output to a file; never a foreground wait near 600 s, never `tail -f` or polling |
| Format and lint | The executor runs `scripts/gates.sh fix-files <file>...` then `scripts/gates.sh lint-files <file>...` on its own files before its commit |
| Move code | `scripts/gates.sh move <source> <start> <end> <destination> [--at LINE]` (wraps `scripts/move_lines.py`, same arguments); required only in C6 refactors, elsewhere Edit |
| Reap | `scripts/gates.sh reap [--older-than <min>] [--dry-run]`: kills, by PID tree, the processes of this session (shell snapshot id in the command line) that are stdin-waiting interpreters or older than N minutes (default 20), never a tree rooted at a `gates.sh baseline\|compare\|verify` call, never by image name; prints `reaped: <n>` and `left: 0` or the survivors |
| Guard hook | `scripts/guard_hook.py`, a blocking `PreToolUse` hook on `Bash\|PowerShell` declared in the frontmatter `hooks:` of the five `prd-flow-*` agents (so it costs nothing elsewhere); denies `<<` (heredoc and here-string), PowerShell `@'` and `@"` here-strings, `python -` / `python3 -` / `py -` and any interpreter reading stdin, `cat >`, `cat >>`, `tee`, `taskkill`, `Stop-Process -Name`, `pkill`, `killall`, `git checkout`, `git switch`, `git stash`, `git reset`, `git restore`, `commit --amend`, `sed -i`; every deny message names the allowed way (Edit and Write; `gates.sh move`; `gates.sh reap`; commit with `-F <file>`); fails open when Python is missing or the input is not JSON |
| Watchdog | `telemetry_hook.py` writes an `agent_stuck` event for a subagent alive past 30 min or with no tool event for 10 min; `gates.sh verify` prints `stuck agents: <ids>` from the run's events and runs `reap` first |
| Reviewer findings | In the return text; a file `<state>/findings-r<N>.md` only past the line cap, named in `Files:` |
| Return | Every agent returns at most 20 lines: `Status`, `Files:`, `Commit:`, `Route:`, `Next:` (the five fields; kit/CLAUDE.md, AGENTS.md and global/CLAUDE.md say the same) |
| Medium findings | Home `reference/review.md`: Critical and High go to a fix and count a round; Medium and Low ride in the same batched fix and do not count a round on their own; reviewer and recheck link to it |
| Full suite | Home `reference/execution.md`: the chief starts `compare` during the last review; close never runs the suite inline, it reuses the compare result; close order lint, trailers, docs, then the compare result |
| Baseline | Home `reference/dispatch.md` DP06: only the chief, background; started for C2, C3, C5, C6; C4 close does not require it |
| Fresh session | Only past about 120k tokens in the chief, as an offer (BC6) |
| Rule IDs in runtime files | Runtime files (`kit/.claude/**`, `kit/CLAUDE.md`, `kit/AGENTS.md`, `kit/scripts/*`, `global/CLAUDE.md`) cite only IDs or headings defined in files the agent loads; IDs of `rules/` stay in `rules/` (BD1, M11) |

### Homes (M10): one rule, one file; others link by heading
| Rule | Home |
|---|---|
| C5 route, returns, failure table, chief card | `SKILL.md` |
| Prompts, background, resume, ledger, baseline, wave verification, cross-repo | `reference/dispatch.md` |
| Sheet format, sheet lint, answers record | `reference/interview.md` |
| Proof, sweep, conflicts, pack | `reference/impact.md` |
| Review policy, rounds, Medium | `reference/review.md` |
| Wave loop, compare, close order, cost per agent | `reference/execution.md` |
| Plan and card format | `reference/agent-plan.md` |
| PRD rows, CHANGELOG entry | `reference/prd-writing.md` |
| TRD Planned | `reference/trd-planned.md` |

## Waves and ownership
Every agent owns only the files listed; a needed change elsewhere goes in its `Gaps`. No agent commits: the chief commits each agent's files after the wave.

| Wave | Agent | Items | Owns |
|---|---|---|---|
| A | A1 orphans | O1, O2, O4 | `kit/scripts/guard_hook.py` (new), `kit/scripts/reap.py` (new), `kit/scripts/gates.sh`, `kit/scripts/telemetry_hook.py`, `kit/scripts/verify.py`, the frontmatter of the five `kit/.claude/agents/prd-flow-*.md` (the `hooks:` key only), `tests/test_guard_hook.py`, `tests/test_reap.py`, `tests/test_kit_telemetry_hook.py`, `tests/test_kit_verify.py` |
| A | A2 sheet format | I1 | `kit/.claude/skills/prd-flow/reference/interview.md`, `kit/.claude/skills/prd-flow/reference/impact.md`, `kit/.claude/skills/prd-flow/repo.md` (the `sheet_labels` key and its note; remove `question_lint` and `plain_words` notes that only Q6 to Q9 used, keep `plain_words` for S4) |
| A | A3 sheet gate | I5, I11 | `kit/.claude/skills/prd-flow/scripts/gate_interview.py`, `state_record.py`, `gate.py`, `gate_core.py` (config read only), `tests/test_gate_questions_state.py`, `tests/test_gate_rules_v4.py`, `tests/test_state_record.py`, new `tests/test_gate_sheet.py`, `tests/fixtures/**` they need |
| B | B-chief | I3, I9 chief part, O3, O5, O7, BA1, BA4, BC6, BD2, BD3, BF2, BF3 | `SKILL.md`, `reference/dispatch.md` |
| B | B-surveyor | I2, I9, I10 text, BF1, BB9 surveyor | `kit/.claude/agents/prd-flow-surveyor.md` (body), `reference/classification.md` (BC5 one-rule C5) |
| B | B-docs | I4, I11 docs part, BC1 per D1, BB3, BB4, BB5, BB9 docs | `kit/.claude/agents/prd-flow-docs.md` (body), `reference/prd-writing.md`, `reference/trd-planned.md`, `reference/agent-plan.md` |
| B | B-exec | BA2, BA3, BB1, BB2, BB6, BB7, BC2, O6, BE2, BE3, BE4 | `kit/.claude/agents/prd-flow-executor.md`, `prd-flow-reviewer.md`, `prd-flow-recheck.md` (bodies), `reference/execution.md`, `reference/review.md` |
| B | B-root | BB1, BB6, BB8, BD4 | `kit/CLAUDE.md`, `kit/AGENTS.md`, `global/CLAUDE.md`, `kit/.specify/**` only if BD4 needs the template read |
| B | G-a | G1, G2, G3, G4, G9, G10, CH3 | `kit/scripts/gates.sh`, `baseline.py`, `new_failures.py`, `close_gate.py`, `verify.py`, their tests (`tests/test_kit_baseline.py`, `test_kit_gates_run_speed.py`, `test_kit_gates_v5.py`, `test_kit_verify.py`, `test_kit_scripts.py` sections) |
| B | G-b | G6, G7, G8, G11, G12 | `kit/scripts/related_tests.py`, `telemetry_hook.py`, `retro.py`, `retro_detectors.py`, `config_get.py`, `kit_config.py`, `kit/ai-kit.json` (`tests.related_exclude`), their tests |
| C | C-gates | BC3, BC4, I6, D1 promote part | `kit/.claude/skills/prd-flow/scripts/gate*.py` except `gate_interview.py`, `promote.py`, their tests |
| C | C-tools | B2 (`fix-files`, `lint-files`, `move`), I10 (`next_change_number`, settings check), B4 doctor, BE1, M12 | `kit/scripts/gates.sh`, `kit/scripts/next_change_number.py` (new), `kit/scripts/settings_check.py` (new), `kit/scripts/move_lines.py`, `installer/ai-kit/**`, their tests |
| C | C-eval | I8, 9.7 metrics | `eval/**` except the audit file |
| C | C-rules | I7, M08 to M13 | `rules/**`, `MAINTAINING.md`, `CHANGELOG.md`, `README.md` |
| D | D-consistency | B1 test M10, M11, M13 | new `tests/test_runtime_consistency.py`, and the runtime text files only to fix what it flags |

## Rules for every agent
| Rule | Detail |
|---|---|
| Edit | Read, Grep, Glob to read; Edit and Write to change. No heredoc, no `python -`, no `cat >`, no `sed -i`, no PowerShell here-string |
| Direction | Prefer removing instructions over adding them; a new line replaces an old one. English, tables over prose, no em dash (U+2014) |
| Tests | Write the failing test first for script changes. Run only your own test modules: `python -m unittest tests.<module>` with output to a file in the scratchpad, read only failures and the summary. Never the full suite |
| Text tests | Many tests assert kit text. When your edit breaks one of YOUR owned tests, update it; a broken test you do not own goes in `Gaps` with its name |
| Ceiling | About 50 tool calls; then return what is done and what is left |
| Return | At most 20 lines: `Done`, `Files`, `Tests`, `Gaps` |
| Processes | Leave nothing running |
