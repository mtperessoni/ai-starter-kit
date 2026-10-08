# prd-flow workers

Read only the section with your name. You do not talk to the user: anything missing becomes a **gap** in the return, never an assumption. Parallel batches whenever reads are independent; read by ID (`Grep -n`, then `Read` with offset and limit); a human-reading HTML is never read whole; big files listed in `repo.md` only by symbol. Write and edit docs with Write and Edit only, never through a Python or shell script; the only script you run is `gate.py`. Prose you write is in the `repo.md` `language` (default English); IDs, code, commit messages and file names are always English. No em dash (U+2014). State: `.claude/prd-flow/state/<slug>/`.

Return to the main thread, always in this format and at most 30 lines:

```
Done: <one line>
Files: <paths written or edited>
<the content the section asks for>
Gaps: <list, or "none">
```

## surveyor

Context, freshness and impact, in sequence, for a rule change. Model: `opus` for size L (the confrontation is the step whose miss costs the most), `sonnet` for M. Short mode (short C5): K01, K02, K11, K12 on the touched rules only, confrontation at most 15 lines.

1. **Batch 1, one message:** `Read .claude/skills/prd-flow/repo.md` (including "Rule owners" and "Shared PRDs"); `Grep` the request's terms in `docs/prd/INDEX.md`; `Read docs/trd/README.md`; `Grep` the terms in the PRD section files to find the rows; `git fetch -q && git rev-parse --short HEAD && git rev-list --count HEAD..origin/<base_branch>`.
2. **Batch 2:** the tables of the sections involved; the TRD feature file; `Grep "<IDs>" docs/prd changes <test folders>` (never `changes/archive/`, LT07); the lines of `docs/trd/invariants.md` for the kind of change; the constitution principle the change touches (title and excerpt).
3. **Freshness:** check the Source of each rule that will change (file and symbol exist, behavior matches). A divergence goes into the pack; an out-of-scope divergence is only noted, with no new call.
4. **Impact:** follow `reference/impact.md` (K01 to K13, trade-offs, protections). K08 to K12 are never skipped (K08 uses `scripts/gates.sh contracts` when snapshots are configured): discovered during execution, they become extra rounds with the user. The confrontation always carries `Checked:` and `Conflicts:`. Write `impact.md` already in the confrontation format from there: it is what the main thread shows the user.
5. **Pre-interview:** for each dimension D01 to D15 of `reference/interview.md` plus the extra ones of `repo.md`, mark the state defined in `reference/impact.md` "Pre-interview states". Put the assumed ones in one block of at most 6 lines at the end of the confrontation.
6. Write `pack.md` in the format below and run `python .claude/skills/prd-flow/scripts/gate.py --pack .claude/prd-flow/state/<slug>/pack.md`. ERROR: fix the pack and run again.

Format of `pack.md` (the gate checks the sections and that every rule row is **literal**, copied from the PRD):

```markdown
# Pack · <slug>
Base: <short commit> · Branch: <name> · Behind origin/<base_branch>: <n> (touches the scope: yes|no)
Request: <one line>

## Rules
### docs/prd/product/04-checkout.md
| CHK-02 | <row copied exactly from the PRD> |

## Rows without ID
### docs/prd/product/04-02-limits.md
| 5 | <row copied exactly from the PRD> |

## TRD
- docs/trd/checkout.md

## Invariants
- I-07 <one line>

## Principles
- III <one line>

## Open questions linked
- Q-CHK-04 <one line>

## Changes and tests
- changes/007-checkout/plan.md
- src/features/checkout/tests/test_payment_call.py

## Divergences
- in scope: <PRD says / code does, with file::symbol>
- out of scope: <note>

## Pre-interview
| Dimension | State | Detail |
|---|---|---|
| D02 variants | doc | same config for web and mobile (payment_config.py::PaymentConfig) |
| D04 numbers | assumed | 20 s, from the PaymentConfig default |
```

Return: the confrontation (at most 25 lines, taken from `impact.md`, 15 in short mode), the in-scope divergences, the assumed block and the open dimensions.

## writer-prd

Applies the approved rules to the PRD. Step 5 of the C5 route, E10 of the short C5, and C4. Input (C5): `approved-rules.md`, `interview.md`, `pack.md`, `state.md`, `changes/NNN-<slug>/decisions.md`. You never touch the TRD.

**C4 mode** (stale PRD): input is the confirmed F2 divergence in `state.md` (rule ID, PRD text, what the code does, Source); there is no `interview.md`, `approved-rules.md` or `decisions.md`. Skip step 1 and the `decisions.md` parts: edit the row in place per `reference/prd-writing.md`, old text literally to the CHANGELOG, INDEX if affected, then steps 3, 4 (`gate.py --step prd` without `--rules`), 5 (no `decisions.md` in the commit) and 6.

**New PRD variant** (classification.md): also read `pack.md`. Write only approved rows after the interview, never `*(proposed)*`; lay out the new PRD folder, INDEX row and README overview per `.claude/skills/prd-create/reference/anatomy.md` (M4).

1. `python .claude/skills/prd-flow/scripts/gate.py --rules .claude/prd-flow/state/<slug>/approved-rules.md` (it reads `interview.md` beside it; Q3, G27 and the other errors). ERROR: stop and return it as a gap. Never edit `approved-rules.md` or `interview.md`: they are the user's decisions and belong to this conversation. Copy each approved row into the PRD as it is (marker, Source, Example included), never retyped.
2. Read `reference/prd-writing.md` and follow it: markdown of the owning section, markers, `Example` column when the approved row carries it, CHANGELOG (with the `Decisions:` block from `decisions.md`, and `decided by <owner>, written by <approver>` when `decisions.md` records an owner), INDEX, README if affected. In the short C5, apply only the dated section of `approved-rules.md`.
3. HTML: with `html_mode: generated` (`repo.md`) run `python .claude/skills/prd-flow/scripts/build_prd_html.py` and never edit the HTML; with `hand`, only `Grep -n` of the ID and an exact `Edit` of the line.
4. One run checks everything this step needs: `python .claude/skills/prd-flow/scripts/gate.py --step prd --rules .claude/prd-flow/state/<slug>/approved-rules.md --applied` (the default checks, Q2, Q3, Q4 and G28 for the "Shared PRDs" of `repo.md`). ERROR: fix the PRD, never the approved file, and run it again. A WARNING about "earlier drift" is not yours.
5. Commit `docs(prd): <sentence in the git log style>` with markdown, the generated or edited HTML and `decisions.md` together.
6. Write `writing.md`: files touched, IDs, commit, the last gate line.

Return: commit, IDs touched, the last gate line (it covers `--applied` and `--sibling`), non-table changes (amendment sections, INDEX, README, new folder; at most 5 lines, so step 6 shows them without reopening files), gaps.

## writer-trd

Writes the TRD after the user confirmed the rule diff (C5 step 7; the TRD is never written before step 6), and in C4.

**C4 mode:** run only when files, entry points or tests moved (otherwise the C4 is one `writer-prd` call and this section is skipped). Input: the confirmed divergence in `state.md` and `writing.md`. Update the body of `docs/trd/<area>.md` and the area map for what moved (names only), no "Planned" section; steps 2 to 4 as below.

C5 input: `approved-rules.md`, `pack.md`, `writing.md`.

1. Read `reference/trd-planned.md` and write the "Planned" section of each feature in the pack (or the file of a new feature) in the table `| File | Changes or creates | Symbols | IDs |`: no parameters, intervals or values (they are rules or contracts), "Tests to write" is the table `| Test file | IDs |` (never expected values), and contracts are linked to `design.md`, not copied.
2. `python .claude/skills/prd-flow/scripts/gate.py --step trd` (the default checks and G23 to G26 in one run). ERROR: fix and run again. A file over the TRD budget splits (trd-planned.md "Size and split").
3. Commit `docs(trd): <sentence>`.
4. Append to `writing.md` the TRD files, the commit and the gate output.

Return: commit, TRD files touched, the last gate line, gaps.

## planner

Builds the plan for agents (step 8; the short C5 appends tasks). Input: `approved-rules.md`, `pack.md`, `changes/NNN-<slug>/decisions.md`, the "Planned" section of the TRD files touched.

1. Read `reference/agent-plan.md` and decide size and where the plan lives (LT04, "Where the plan lives"); reuse the change folder step 4 created. For size M and L write `brief.md` (`docs/templates/change-brief.md`, LT02) and, for L, `design.md` (`docs/templates/change-design.md`, LT03) first; the brief cites rule IDs only (LT09).
2. Write the tasks in the format there, with the final promotion task, and copy the "Plan execution rules" and the `## Constitution check` (LT05) into the plan header. Before writing, check with `git log` which tasks the plan depends on are already done. Each task points to its TRD Planned row by file instead of describing it again. Run `python .claude/skills/prd-flow/scripts/gate.py --step plan --plan <plan> --change changes/NNN-<slug>` once (plan, brief and G27 together): fix every ERROR. Commit `docs(changes): <sentence>`.
3. Structure (SKILL.md R08, `docs/code-structure.md`): every task names the area and its files per `docs/code-structure.md` "This repository's layout", files named after their responsibility, and the tests where AR10 puts them; no task creates a file above the limits or with a generic name; a legacy file over the limit follows AR21 (extract first); an untested legacy path gets a characterization test first (TS42); a task that changes the pieces of an area updates its map and TRD.
4. Cost (execution.md E12 to E17): rules cited by ID, never copied outside the owning task; each task section at most 25 lines, naming files, entry symbols and tests; the whole plan around 30 KB. Replace the old path with the new one instead of keeping both in parallel, unless a rollback switch requires it: a double path makes every test be touched twice. Model `sonnet`; `opus` only with a reason on the line (E13). Reviewer from `repo.md`.

Return: where the plan is and the table (ID, result, owns, depends on, model, reviewer).

## executor

Implements ONE task of the plan, or fixes the findings of one review round. Input: the task ID (or the finding IDs) and the plan path.

1. **Batch 1, one message:** from the plan, only "Plan execution rules" and your task's section; from `deliveries.md`, only the blocks of the tasks in "Depends on"; the rule rows by ID in the PRD; `git log -5 -- <files in Owns>`; the commands section of `repo.md`. Big files only by symbol.
2. **Test first:** write the task's test from the contract row's `Example` when it has one (given → expected outcome), run it and see it fail; implement the minimum; run it again.
3. **Gate:** only the related tests (the mirror test of the module and the tests that import or use the touched module: `Grep` the module path in the test folders), the structure ratchet, plus lint and format of the touched files. Never the full suite (execution.md E18): it runs once, at the end of all tasks, in the main thread. Test output to a file; only failures and the summary come back (E16). In a refactor, move code by script, never retype (E19).
4. **Structure (SKILL.md R08):** new code lives in the right feature, respects the limits of `docs/code-structure.md`, cites the PRD IDs in the module and test docstrings, and the feature's `CLAUDE.md` follows the change. The ratchet is always among the related tests and cannot regress.
5. **Outside Owns:** a test of another file that broke as a direct and expected consequence of the change may have only its expectation adjusted, never a loosened safety assertion, and enters the file list of the return. A contract or rule divergence, or any behavior the approved rules do not cover (R09): stop the task and return it as a gap, without inventing a rule; only a missing technical detail is a question.
6. Append your block to `deliveries.md` (format below).
7. No commit and no push (the main thread commits with the exact file list), no script to edit files, no em dash, no unnecessary comment.

**Ceiling (review.md V08):** if you reach the ceiling without finishing, return what you did and what is left; the main thread decides. Never open a subagent (execution.md E12).

`deliveries.md` block (at most 8 lines; it is what the next task reads instead of your code):
```markdown
## T07 · <result in one line>
Creates: PaymentOutcome.retry_after, PAYMENT_TIMEOUT_EVENT
Changes: call_provider(..., timeout=) now reads PaymentConfig
Leaves for: T08 to pass timeout= from the mobile flow
```

Return (at most 20 lines):
```
Done: <ID>, <one line>
Files: <exact list for the commit>
Tests: <new test names> · Gate: <result against the baseline> · Lint: <ok|error>
Commit: <Conventional Commits message in English, with the IDs, ending with the trailer line `Rules: <IDs>` or `Case: none (<reason in at most 8 words>)`>
Gaps: <list, or "none">
```

The trailer is required when the commit touches the source folders (`ai-kit.json`); `scripts/gates.sh trailers` checks it.

## reviewer

Instructions the main thread puts in the prompt of the task's reviewer agent (from `repo.md`), besides the diff:

- "Round N/5 of `.claude/skills/prd-flow/reference/review.md`." In round 1, the delivery diff; from round 2, only the fix diff and the list of previous findings (V03): say resolved or not for each and point out only new problems that diff created.
- Each finding on one line: `[Critical|High|Medium|Low] CS-NNN · file:line · rule · concrete scenario in one sentence · fix in one sentence`. At most 8 findings, the most severe first.
- Severity by consequence to the user or the delivery, not elegance. "Possible in theory" without a concrete scenario is Low.
- Return at most 20 lines; ceiling per review.md V08. A finding that is a behavior outside the approved rules is marked `R09`. Findings only: never edit code or write files.
