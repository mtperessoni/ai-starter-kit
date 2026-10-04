# prd-gate workers

Read only the section with your name. You do not talk to the user: anything missing becomes a **gap** in the return, never an assumption. Parallel batches whenever reads are independent; read by ID (`Grep -n`, then `Read` with offset and limit); a human-reading HTML is never read whole; big files listed in `repo.md` only by symbol. Write and edit docs with Write and Edit only, never through a Python or shell script; the only script you run is `gate.py`. Everything you write is in English. No em dash (U+2014). State: `.claude/prd-gate/state/<slug>/`.

Return to the main thread, always in this format and at most 30 lines:

```
Done: <one line>
Files: <paths written or edited>
<the content the section asks for>
Gaps: <list, or "none">
```

## surveyor

Context, freshness and impact, in sequence, for a rule change.

1. **Batch 1, one message:** `Read .claude/skills/prd-gate/repo.md`; `Grep` the request's terms in `docs/prd/INDEX.md`; `Read docs/trd/README.md`; `Grep` the terms in the PRD section files to find the rows; `git fetch -q && git rev-parse --short HEAD && git rev-list --count HEAD..origin/<base_branch>`.
2. **Batch 2:** the tables of the sections involved; the TRD feature file; `Grep "<IDs>" docs/prd specs <test folders>`; the lines of `docs/trd/invariants.md` for the kind of change; the constitution principle the change touches (title and excerpt).
3. **Freshness:** check the Source of each rule that will change (file and symbol exist, behavior matches). A divergence goes into the pack; an out-of-scope divergence is only noted, with no new call.
4. **Impact:** follow `reference/impact.md` (K01 to K10, trade-offs, protections). K08 to K10 are never skipped: discovered during execution, they become extra rounds with the user. Write `impact.md` already in the confrontation format from there: it is what the main thread shows the user.
5. **Pre-interview:** for each dimension D01 to D15 of `reference/interview.md` plus the extra ones of `repo.md`, mark `answered: <source>`, `not applicable: <reason>` or `open: <question with scenario and recommended default>`.
6. Write `pack.md` in the format below and run `python .claude/skills/prd-gate/scripts/gate.py --pack .claude/prd-gate/state/<slug>/pack.md`. ERROR: fix the pack and run again.

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

## Specs and tests
- specs/007-checkout/spec.md FR-012
- src/features/checkout/tests/test_payment_call.py

## Divergences
- in scope: <PRD says / code does, with file::symbol>
- out of scope: <note>

## Pre-interview
| Dimension | State | Detail |
|---|---|---|
| D02 variants | answered | same config for web and mobile (payment_config.py::PaymentConfig) |
```

Return: the confrontation (at most 25 lines, taken from `impact.md`), the in-scope divergences and the open dimensions.

## writer

Applies the approved rules to the PRD, the HTML if any, and the TRD. Input: `approved-rules.md`, `pack.md`, `state.md`.

1. `python .claude/skills/prd-gate/scripts/gate.py --rules .claude/prd-gate/state/<slug>/approved-rules.md`. ERROR: stop and return it as a gap.
2. Read `reference/prd-writing.md` and follow it: markdown of the owning section, markers, CHANGELOG, INDEX, README if affected. The HTML only by `Grep -n` of the ID and an exact `Edit` of the line.
3. `python .claude/skills/prd-gate/scripts/gate.py`. ERROR: fix and run again until green. A WARNING about "earlier drift" is not yours.
4. Commit `docs(prd): <sentence in the git log style>` with markdown and HTML together.
5. Read `reference/trd-planned.md` and write the "Planned" section of each feature in the pack (or the file of a new feature). Gate again. Commit `docs(trd): <sentence>`.
6. Write `writing.md`: files touched, IDs, commits, final gate output.

Return: commits, IDs touched, the last line of the gate, gaps.

## planner

Builds the plan for agents. Input: `approved-rules.md`, `pack.md`, the "Planned" section of the TRD files touched.

1. Read `reference/agent-plan.md` and decide where the plan lives (amendment of an active spec, a new plan, or only a publish or deploy task).
2. Write the tasks in the format there, with the final promotion task, and copy the "Plan execution rules" into the plan header. Before writing, check with `git log` which tasks the plan depends on are already done. Run `python .claude/skills/prd-gate/scripts/gate.py --plan <plan>`: fix every ERROR. Commit `docs(specs): <sentence>`.
3. Structure (SKILL.md R08, `docs/code-structure.md`): every task names the feature (`src/features/<f>/`), the files it creates or changes, named after their responsibility, and the tests in `features/<f>/tests/`; no task creates a file above the limits or with a generic name; a task that changes the pieces of a feature updates its `CLAUDE.md` and TRD.
4. Cost (execution.md E12 to E17): rules cited by ID, never copied outside the owning task; each task section at most 25 lines, naming files, entry symbols and tests; the whole plan around 30 KB. Replace the old path with the new one instead of keeping both in parallel, unless a rollback switch requires it: a double path makes every test be touched twice. Model `sonnet`; `opus` only with a reason on the line (E13). Reviewer from `repo.md`.

Return: where the plan is and the table (ID, result, owns, depends on, model, reviewer).

## executor

Implements ONE task of the plan, or fixes the findings of one review round. Input: the task ID (or the finding IDs) and the plan path.

1. **Batch 1, one message:** from the plan, only "Plan execution rules" and your task's section; from `deliveries.md`, only the blocks of the tasks in "Depends on"; the rule rows by ID in the PRD; `git log -5 -- <files in Owns>`; the commands section of `repo.md`. Big files only by symbol.
2. **Test first:** write the task's test, run it and see it fail; implement the minimum; run it again.
3. **Gate:** only the related tests (the mirror test of the module and the tests that import or use the touched module: `Grep` the module path in the test folders), the structure ratchet, plus lint and format of the touched files. Never the full suite (execution.md E18): it runs once, at the end of all tasks, in the main thread. Test output to a file; only failures and the summary come back (E16). In a refactor, move code by script, never retype (E19).
4. **Structure (SKILL.md R08):** new code lives in the right feature, respects the limits of `docs/code-structure.md`, cites the PRD IDs in the module and test docstrings, and the feature's `CLAUDE.md` follows the change. The ratchet is always among the related tests and cannot regress.
5. **Outside Owns:** a test of another file that broke as a direct and expected consequence of the change may have only its expectation adjusted, never a loosened safety assertion, and enters the file list of the return. A contract or rule divergence: stop and return it as a gap, without inventing a rule.
6. Append your block to `deliveries.md` (format below).
7. No commit and no push (the main thread commits with the exact file list), no script to edit files, no em dash, no unnecessary comment.

**Ceiling (review.md V08):** if you reach about 50 tool calls or 30 minutes without finishing, return what you did and what is left; the main thread decides. Never open a subagent (execution.md E12).

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
Commit: <Conventional Commits message in English, with the IDs>
Gaps: <list, or "none">
```

## reviewer

Instructions the main thread puts in the prompt of the task's reviewer agent (from `repo.md`), besides the diff:

- "Round N/5 of `.claude/skills/prd-gate/reference/review.md`." In round 1, the delivery diff; from round 2, only the fix diff and the list of previous findings (V03): say resolved or not for each and point out only new problems that diff created.
- Each finding on one line: `[Critical|High|Medium|Low] CS-NNN · file:line · rule · concrete scenario in one sentence · fix in one sentence`. At most 8 findings, the most severe first.
- Severity by consequence to the user or the delivery, not elegance. "Possible in theory" without a concrete scenario is Low.
- Return at most 20 lines; ceiling of 40 to 60 tool calls. Findings only: never edit code or write files.
