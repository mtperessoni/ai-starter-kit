# Plan: prd-flow lite (same guarantees, a fraction of the transport)

Why: [`../eval/AUDIT-prd-flow-end-to-end-2026-10-09.md`](../eval/AUDIT-prd-flow-end-to-end-2026-10-09.md). A plain Claude session beats prd-flow because prd-flow moves understanding through cold agents and copies, not because its rules are wrong. This plan keeps every orchestration rule that makes the run fluid (chief only coordinates, parallel waves, warm resume, review cap, batch verification, reap) and removes transport: copies of the same rule, gates that check those copies, scaffolds, cold restarts, and session garbage.

Branch `feat/prd-flow-lite`, worktree `C:/Projects/ai-starter-kit-lite`, from `a979cd6`. Rebased on `feat/one-pass-interview` when that branch lands.

## Invariants (must hold after this plan)
| ID | Invariant | Rules it keeps |
|---|---|---|
| I1 | The chief coordinates and never does what it dispatches: closed tool list, no source, diff or plan reading | SA01, SA43, SA28 |
| I2 | A rule change reaches the PRD before the code, after one user approval of the rule diff | WF06, WF08, WF45 |
| I3 | The sweep finds conflicting neighbor rules and the code proves each touched rule | WF10, WF38, WF39, WF59, WF50 |
| I4 | Work runs in parallel waves of subagents with disjoint Owns, dispatched in one message in the background | SA12, SA13, SA36, SA54 |
| I5 | Warm agents are resumed with SendMessage; cold ones get a handoff of at most 10 lines | SA48, SA16, SA18 |
| I6 | Review per wave, at most 5 rounds per delivery, cascade stop, batched fix | RV01 to RV07, RV18, SA40 |
| I7 | Test first; executors run only their own test; one verification per wave; full suite once | TS, RV09 |
| I8 | Trailers on every source commit; tests cite rule IDs | WF49, WF31 |
| I9 | One return contract with Status, Files, Commit, Route, Next; every failure has an owner and a route | SA45, SA46 |
| I10 | No data leaves its boundary: PII, PHI and tokens never in logs, telemetry, prompts to other repos or long-lived files; the state folder is deleted at close | constitution I of the target repos, TM redaction |
| I11 | No process, agent or file of the run outlives it: every run starts and ends with `gates.sh cleanup` | new SA56 |

## Decisions
| ID | Decision | Effect | Rules touched |
|---|---|---|---|
| L1 | The surveyor runs `scripts/gates.sh prd-sweep --ids <IDs> --terms "<words>" --out <state>/sweep.md` (`prd_sweep.py`) first: a deterministic script prints the literal rows, citing rows, same-table rows, candidate sections from INDEX by terms, unconditional candidates, CHANGELOG history, active changes, tests citing each ID, and for each Source symbol whether it exists and who calls it outside tests. The surveyor reads the output, does F3 (reads the symbols) and judges conflicts | Surveyor from 37 to 118 calls down to about 20 to 35 | WF38, WF39, WF41, WF57 (the sweep becomes a script plus judgment); new WF75 |
| L2 | Surveyor model per mode: `query` and `light` on sonnet (dispatch passes `model`), `full` and `short` on opus | Most cases run on the fast model | WF51 applied; SA44 amended (heavy only where a decision is made) |
| L3 | Docs `apply` writes one record set: PRD rows (marker kept), the CHANGELOG entry (reason, IDs, conflicts, supersedes, the old rows literal), `changes/NNN-<slug>/decisions.md` (the user's reply verbatim on top, then DEC rows), the plan. No `answers.md`, no `rules.md`, no `approved-rules.md`, no `state_record.py render` | 3 artifacts and a render loop gone; the PRD diff is the approved set | CE29, WF43, WF44, WF47 amended; WF61 amended |
| L4 | `promote.py` and the gate read the approved set from the PRD: the rows of the IDs listed in the slug's CHANGELOG entry (`IDs:` line) that carry the pending marker; Supersedes and Conflicts from the same entry | Same promotion, no state copy | WF61, WF72, WF44 |
| L5 | Size M writes no `brief.md` and no TRD Planned section: the cards name files and symbols, and the last task of each area updates the TRD body. Size L keeps `brief.md`, `design.md` and TRD Planned | Less generated prose on the critical path | WF26, WF27, WF70, TP rules; DS TRD Planned for M |
| L6 | Docs commits: one `docs(prd): <sentence>` commit holding PRD, CHANGELOG, TRD and the change folder, instead of three | 6 calls fewer per C5 | WF21 amended |
| L7 | A fix goes to the warm executor of the task (SendMessage with the finding lines); a new executor `fix` only when that agent is past its ceiling or 150k. The recheck is the warm reviewer of the round resumed with the fix commit; `prd-flow-recheck` stays only as the cold fallback | 2 cold starts fewer per round | SA48 applied; RV10, RV03 unchanged in substance |
| L8 | Gate output to agents is errors only, plus one line counting warnings; warnings go to `_gate/last-<mode>.txt` and the close report. Checks that exist only to compare protocol copies go: Q2, Q3 answers part, Q4 against `approved-rules.md` (replaced by L4 checks on the PRD), P11 to P16 (plan alignment reminders) | Fewer reruns and fewer reads of noise | DS46, WF68, WF70 amended; M09 of the earlier plan |
| L9 | Cards carry `Why:` (at most 3 lines: the user's words or the rule's Example that motivates the task) so the executor does not read whole PRD sections | Intent survives the handoff | SA37 amended |
| L10 | Ceilings fit the work: surveyor `full` and docs `apply` 80 calls, every other role as today; V08 stays the single home | Handoffs by design end | SA15, RV08, WF52 |
| L11 | Subagents never use `run_in_background`; long commands run foreground with an explicit timeout under 600 s. Only the chief starts background work (baseline, verify, compare, watch) | Ends orphans from subagent shells | SA54 clarified; TS rows on background |
| L12 | The guard hook runs for every subagent from `settings.json` (`PreToolUse`, Bash and PowerShell, only when the payload has `agent_id`), not only from the prd-flow frontmatter; the `general-purpose` fallback in `dispatch.md` is removed | Every agent is guarded; the main thread is never blocked | SA51, SA53 enforced |
| L13 | `gates.sh cleanup [<slug>]` (new): reap by PID tree (suite trees reaped once their status is not running or past their timeout), delete this session's task output files, delete loose files in `.ai-kit/runs/`, move state folders untouched for 7 days to `state/_stale/` and delete `_stale/` entries older than 14 days, delete `_tests` and `_gate` caches older than 3 days. Prints `left: 0` or the survivors. The chief runs it at the start and at the end of every case; `gates.sh close` runs it last; a `SessionEnd` hook runs `cleanup --session-end` (reap and task outputs only) | The session always ends clean | new SA56; TS rows on disk; LK5 to LK7 |
| L14 | `gates.sh watch <slug> [--minutes N]` (new): the chief starts it in the background with each wave; it exits when an agent of this session has had no tool event for 10 minutes or the wave passes N minutes (default 30), printing the agent ids. Its completion wakes the chief, which TaskStops them, reaps and redispatches with a handoff | A hung agent can no longer hold a wave | new SA57; LK4 |
| L15 | The ratchet allowlist moves from `ai-kit.json` to `ai-kit.allowlist.json`; `kit_config` reads either (sidecar first) so old repos keep working; `/ai-kit update` moves it | `ai-kit.json` drops from 58 to 115 KB to under 10 KB | CF1; IN rule for update |
| L16 | Hook commands carry the interpreter resolved at install (`__AIKIT_PYTHON__` placeholder filled by `/ai-kit install` and `update`), no `python -c pass` probe | About 2 fewer process launches per hook | TM03 |
| L17 | Cross-repo: the chief is started in the target repository (or its worktree); a prompt never says "follow the other agent file" | One definition per agent | SA55 amended |
| L18 | Instructions are rewritten as imperative steps per mode; IDs stay only where a script, a test or the catalog needs them; the 9 references become 5: `dispatch.md` (the chief's only reference, since `SKILL.md` must stay under 6,144 bytes), `survey.md` (surveyor), `sheet.md` (surveyor and docs), `write.md` (docs), `run.md` (executor, reviewer, recheck), plus `repo.md` | About half the runtime text; no rule lost (catalog map below) | M03, M10, M13 |
| L19 | `eval/` gets arms `PLAIN` (no skill, PRD diff prompt) and `LITE` (this branch) beside `FLOW`, per MAINTAINING "once without the skill" | The skill is measured against the plain agent | M07 |

## Flow after the plan
| Case | Route |
|---|---|
| C1 query | cleanup, surveyor `query` (sonnet) with the sweep, report, cleanup |
| C2, C3, C6 | cleanup, surveyor `light` (sonnet) writes `card.md`, baseline, executor `task`, watch, reviewer, warm fix if needed, executor `close`, cleanup |
| C4 | cleanup, surveyor `light`, docs `c4`, executor `close`, cleanup |
| C5 | cleanup, surveyor `full` (opus, sweep first) writes `pack.md` and `sheet.md`; chief prints the sheet and ends the turn; docs `apply` (opus) writes PRD, CHANGELOG, `decisions.md`, plan in one commit and returns the rule diff and wave table; one approval; baseline; per wave: executors in one message plus watch, then reap, verify with the reviewer, warm fixes, warm recheck; executor `close` (promote, close gate, cleanup); final report |

State folder of a C5 after the plan: `state.md`, `pack.md`, `sheet.md`, optional `sheet-2.md`, optional `facts.md`, `card.md` (C2, C3, C6), `deliveries/<task>.md`, `findings-r<N>.md` past the line cap, message files. Deleted at close.

## Formats shared by scripts and instructions
CHANGELOG entry written by docs `apply` (newest first; prose in the repo `language`, the labels below stay as written):

```markdown
## <Name of the change> (YYYY-MM-DD, <approver>, changes/NNN-<slug>)

Reason: <one sentence>. IDs: CHK-02, CHK-13.
Conflicts: CHK-05 compatible (retry reuses the same timeout).
Supersedes: CHK-07.

### product/04-checkout.md

**CHK-02** (whole row), rewritten.

    | CHK-02 | <old row, literal> |
```

| Line | Rule |
|---|---|
| `IDs:` | Every approved row of the change (new and rewritten); promote and the gate take the approved set from here (L4) |
| `Conflicts:` | Every ID of `pack.md` `Conflicts:` that is not rewritten or superseded, with `compatible (<why>)`; `none` when empty |
| `Supersedes:` | IDs that keep their text with the superseded marker until promote removes them; `none` when empty |
| Excerpts | The old literal row of each rewritten ID, written by docs `apply` (it has it in `pack.md`); promote adds the excerpts of superseded rows and the `Decisions:` block |

`changes/NNN-<slug>/decisions.md` (template `docs/templates/change-decisions.md`): first `Reply 1: "<the user's message verbatim>"` (and `Reply 2:` after a follow-up), then the table `| ID | Question | Decision | Rejected alternative | Why | Rules |`.

Gate checks replacing Q2 to Q5 (L4, L8), all errors: every `IDs:` entry exists in the PRD with the pending marker (until promote) or without it (after); every pack `Conflicts:` ID appears in `IDs:`, `Supersedes:` or `Conflicts:`; a mechanism term (environment variable, switch, flag, configuration key, table, endpoint, column) in `decisions.md` or in the rows of `IDs:` that is not in `sheet.md`, `sheet-2.md` or a `Reply` line is an error. A state folder that still has `approved-rules.md` (old route) is read the old way until it closes.

## Catalog map (no orchestration rule is dropped silently)
| Rule | After the plan |
|---|---|
| SA01, SA02, SA03, SA09, SA12, SA13, SA14, SA16, SA18, SA19, SA23, SA25, SA26, SA27, SA28, SA29, SA30, SA32, SA34, SA35, SA36, SA38, SA39, SA40, SA43, SA45, SA46, SA47, SA48, SA50, SA51, SA52, SA53, SA54 | Kept as they are |
| SA15, RV08, WF52 | Kept, values per L10 |
| SA37 | Kept, card adds `Why:` (L9) |
| SA44, WF51 | Surveyor first in every case kept; model per mode (L2) |
| SA55 | Kept, plus L17 |
| SA07, SA22 | Already superseded by deliveries per task and cards; text aligned |
| SA05, CE29 | State folder kept; the rendered state record (`rules.md`, `approved-rules.md`) retired by L3 and L4 |
| SA49 | Kept for fan-out |
| SA42, SA41 | Kept |
| RV01 to RV07, RV09 to RV18 | Kept; RV10 and RV03 carried out by warm agents (L7) |
| WF01 to WF13, WF17, WF19, WF22 to WF25, WF28, WF30 to WF37, WF40, WF46, WF48 to WF50, WF53 to WF66, WF71 to WF74 | Kept |
| WF21 | Amended by L6 |
| WF26, WF27, WF70 | Amended by L5 (M without brief and Planned) |
| WF38, WF39, WF41, WF57 | Carried out by `prd_sweep.py` plus the surveyor's judgment (L1) |
| WF43, WF44, WF47, WF61, WF72 | Amended by L3 and L4 |
| WF68, WF69 | Sheet lint S1 to S6 kept; plan alignment P11 to P16 retired (L8); WF69 kept as a `sheet-2.md` item |
| WF14, WF16, WF18, WF20, WF42, WF67 | Already replaced or retired by the one-pass branch |
| New SA56 | Every run starts and ends with `gates.sh cleanup` (L13) |
| New SA57 | Per-wave watch (L14) |
| New WF75 | The sweep script (L1) |

## Waves and ownership
Each agent reads this file, the decision rows it owns and its owned files; it never edits a file outside its Owns. Sonnet unless the row says otherwise. Each runs only its own tests (`python -m unittest tests.<module>`), output to a file. Returns at most 20 lines: Done, Files, Tests, Gaps.

| Wave | Agent | Decisions | Owns |
|---|---|---|---|
| 1 | A cleanup and leaks | L11 (scripts side), L12, L13, L14, L16 | `kit/scripts/reap.py`, `kit/scripts/clean_task_outputs.py`, new `kit/scripts/cleanup.py`, new `kit/scripts/watch.py`, `kit/scripts/guard_hook.py`, `kit/scripts/gates.sh`, `kit/scripts/close_gate.py`, `kit/.claude/settings.json`, `tests/test_reap.py`, `tests/test_guard_hook.py`, new `tests/test_cleanup.py`, new `tests/test_watch.py` |
| 1 | B sweep | L1 | new `kit/.claude/skills/prd-flow/scripts/prd_sweep.py`, new `tests/test_prd_sweep.py`, new fixture under `tests/fixtures/sweep/` |
| 1 | C config | L15 | `kit/scripts/kit_config.py`, `kit/scripts/ratchet.py`, `kit/scripts/config_get.py`, `kit/.claude/skills/prd-flow/scripts/gate_plan.py` (only the allowlist read), `kit/ai-kit.json`, the ratchet and config tests |
| 1 | D promote and gate | L3 (scripts side), L4, L8 | `promote.py`, `state_record.py`, `gate.py`, `gate_core.py`, `gate_rules.py`, `gate_prd.py`, `gate_interview.py`, `gate_output.py` and their tests (`test_promote.py`, `test_state_record.py`, `test_gate_rules_v4.py`, `test_gate_sheet.py`, `test_gate_output.py`, `test_gate_docs_final.py`, `test_gate_questions_state.py`, `test_gate_base.py`, `test_gate_step.py`, `test_gate_change.py`) |
| 2 | E instructions (opus: one voice across 16 files, one home per rule) | L2, L3, L5 to L11, L13, L14, L17, L18 | `kit/.claude/skills/prd-flow/SKILL.md`, `repo.md`, `reference/*`, `kit/.claude/agents/prd-flow-*.md`, `kit/docs/templates/change-*.md`, `kit/AGENTS.md`, `kit/CLAUDE.md` |
| 3 | F catalog and docs | catalog map | `rules/*.md`, `CHANGELOG.md`, `MAINTAINING.md`, `README.md`, `installer/ai-kit/*` (L15 move, L16 placeholder) |
| 3 | G eval | L19 | `eval/arms*.json`, `eval/arms/*`, new arm protocol files, `eval/README.md` |
| each | Reviewer | the wave's decisions | findings only |

Wave 2 waits for wave 1 so the instructions cite commands that exist. The full suite runs once at the end against the baseline recorded before wave 1.

## Targets on the next real C5 (size M)
| Measure | Before | Target |
|---|---|---|
| Surveyor calls | 37 to 118 | at most 35 |
| Docs `apply` calls | 61 to 166 | at most 50 |
| Agents dispatched | 45 to 89 | at most 12 |
| Docs output tokens / code output tokens | 1.2 to 3.2 | under 0.6 |
| Agents past 150k | 7 to 12 | 0 |
| Time from the answer to the first executor | 40 min to 2 h 20 min | under 15 min |
| Processes, agents and task output files left after the run | many, 3.7 GB | 0 |

## Risks
| Risk | Mitigation |
|---|---|
| `promote.py` reading the PRD instead of `approved-rules.md` misses a row | Tests on the existing promote fixtures, rewritten to the new input; `--dry-run` |
| Repos on the old format mid-run | A state folder with `approved-rules.md` keeps the old route until it closes |
| The watch script is a waiter with a sleep loop | It is one bounded background call owned by the chief with a timeout, not model polling; it is the only way to wake a chief whose last agent hung |
| Conflicts with `feat/one-pass-interview`, which is still moving | Rebase at the end; instruction files are rewritten in one pass by one agent |
