# Writing the PRD (read by the docs agent)

IDs, texts and paths in the examples are illustrative: always read the real line.

## Who writes what
| Artifact | Writer |
|---|---|
| `approved-rules.md` rows, conflict resolutions, Supersedes, `interview.md` answers, `DEC-` rows | docs `rules`, from the answers the chief passes |
| PRD files, CHANGELOG entry, INDEX, README, ADR | docs `prd-plan` (`short` for a dated section, `c4` for a stale PRD, `context` for one context of a fan-out) |
| Promotion (markers out, Source in, CHANGELOG excerpts, archive) | `promote.py`, run by `executor close` |
| An amendment fold or superseded mismatch promote could not decide | docs `fold` |

## Writer steps (docs `prd-plan`)
| Step | What the docs agent does |
|---|---|
| 1 | Writes the PRD files from `approved-rules.md` (rows literal, with the Example cell when present) |
| 2 | Updates CHANGELOG and INDEX (never the HTML, section "HTML" below) |
| 3 | Writes the `Decisions:` block of the CHANGELOG entry from `changes/NNN-<slug>/decisions.md`, and the contract and transition lines (below) |
| 4 | Runs `gate.py --step prd --rules <approved-rules.md> --applied` once: the default checks, Q4 (a row of the file not in the PRD with identical cells) and G28 |
| 5 | Commits `docs(prd)` with `decisions.md` and the PRD together |

In a fan-out, a `context` agent does only step 1 on its own section files; the `prd-plan merge` dispatch does steps 2 to 5 once for the whole change.

A folded `prd-plan` (`interview.md` "Folded path") writes the rules and `Confirmed:` first, then follows this order; the PRD write happens only after `gate.py --rules` is green.

The user review skip (the single home of this rule): the user does not review the written PRD when `--applied` is green and the change has no non-table content (prose, new sections, an amendment file); the docs agent continues to the TRD and the plan in the same run. With non-table changes it does not stop either: one `prd-plan` dispatch commits the prose last, in its own `docs(prd): prose <slug>` commit, and returns the non-table changes in plain words for the user to confirm in the plan round, together with the wave table. The contract and transition lines below are not non-table content: the user already confirmed them in the interview.

## Contract and transition lines
The interview answers of D08 (contract: what consumers receive) and D13 (transition: requests in flight, existing records, rollout) are decisions, not rule rows, and `interview.md` is deleted at close. When the answer is `user` or `assumed-confirmed` and no approved row already states it, the docs agent writes one line under the owning section's rule table, in product language, citing the rules it qualifies; a "nothing changes" answer is written too, because it is what the executor and the reviewer must keep:

```markdown
Contract: the receipt layout and its fields do not change (CHK-09).
Transition: applies to every order from now on; no switch, no migration of existing orders (CHK-09).
```

The plan cites the `DEC-` row of the same answer, when there is one, in the `Decisions:` line of the task that implements the rule.

## Where to write
| Change | Form |
|---|---|
| Stays inside one section | In-place edit, in the table of the section that owns the ID |
| Crosses sections or variants | An amendment section (`<prd>/NN-NN-<slug>.md`, "Amendment X"), with a short `> [!IMPORTANT]` note in each affected section pointing to it |
| C4 (stale PRD) | In-place edit, old text literally to the CHANGELOG |

## Rule rows
Table format: `| ID | Rule | Source | Change via |` with an optional fifth column `Example`. Risks and problems use `| R-NN · high | ... |`.

| Situation | How it looks |
|---|---|
| New ID | Next free number of the prefix. Never renumber or reuse |
| Example column | One line `<given> → <expected outcome>` in product language, for example `Provider silent for 20 s → "try again" shown, cart kept` (illustrative). Required for a rule with a number, a branch or a failure path; the D15 answer lands here. Four-column tables stay valid |
| Proposed (comes only from documents, not proven by code) | `*(proposed)*` (the `proposed_marker` of `repo.md`) at the start of the text; Source `planned`. Input of C5, never C2. Greenfield M2 rules come from the interview and are approved, not proposed |
| Approved, no code yet | `*(approved YYYY-MM-DD, pending code)*` at the start of the text; Source `planned`. Approving a proposed rule replaces its `*(proposed)*` marker with this one |
| Rule the new one supersedes | Keeps its text and gets `*(superseded: <link to the new rule>, valid until deploy)*` at the start |
| Rule rewritten (same rule, new text) | Keeps its ID; the rewritten row carries the approved marker; the old text goes literally to the CHANGELOG at promotion. An ID is never reused for a different rule |
| Conflict found by the surveyor | `approved-rules.md` has `## Conflicts` with `\| ID \| Resolution \| Note \|`, filled by docs `rules`. Resolution is `rewritten` (the same ID is a row under its file heading, with the new text and marker), `superseded` (listed under `## Supersedes` as `ID: old text`) or `compatible` (the Note says why). The gate (Q5) requires a row for every ID of the pack's `Conflicts:` line, the table row for `rewritten`, an existing PRD ID for `superseded`, and a non-empty Note for `compatible` |
| `Q-`, `R-`, `S-` answered | Append `*Decided on YYYY-MM-DD: <decision>, see <ID>.*` at the end; nothing is deleted |
| Table row without ID | Keeps the table format and is cited by section and number (`04-02 #5`). Do not invent an ID. Approved without code: the marker goes at the start of the text cell |
| Promotion | See "Promotion" below |

`--final` fails on any rule still marked proposed (G30).

Style: English, product language; a technical term only in backticks and explained. Source with a file (and symbol when it helps), never a line or a default value. No em dash.

## CHANGELOG
New entry at the top:

```markdown
## <Name of the change> (YYYY-MM-DD, <approver>, <change folder or branch>)

Reason: <one sentence>. IDs: CHK-02, CHK-13.
Owner: decided by <owner>, written by <approver>   (only when "Rule owners" of repo.md applies)

Decisions:
| ID | Question | Decision | Rejected alternative | Why | Rules |
|---|---|---|---|---|---|
| DEC-01 | <question> | <decision> | <alternative> | <reason> | CHK-02 |

### product/04-checkout.md

**CHK-02** (whole row). Superseded by <link>.

    | CHK-02 | <old row, literal> |
```

In a rule change the entry is created by docs `prd-plan` with the reason, the IDs and the Decisions block (rows copied from `decisions.md`); the literal excerpts are added at promotion, when they leave the body. In docs `c4` the excerpts go in already in the same run. The Decisions block is what impact K12 shows later as `Decided <date>: <why>; rejected: <alternative> (<why>)`.

## INDEX and README
- `INDEX.md`: the IDs column of the file's row (range `CHK-01..13`), the TRD column when a feature file appears. A new amendment section gets its own row.
- `README.md`: "State per spec" and "What weighs most today" only when the change affects them.

## Promotion
`executor close` runs `promote.py <slug>` (`--dry-run` to preview) after the last wave and commits its result; no plan task does it. The script applies these rules:

| Step | Rule |
|---|---|
| P1 | Old text (superseded and rewritten rows) literally to the CHANGELOG; superseded rows leave; markers leave; Source gets the real file (from the `Source:` lines of `deliveries/<task>.md`, or the TRD Planned file column) |
| P2 | The `decisions.md` rows are in the CHANGELOG entry under `Decisions:` (copied, not summarized) |
| P3 | Fold amendments (the single home of this rule): each amendment row moves to the step section that owns the behavior (ID unchanged, markers removed, Source filled); an amendment file whose rows all moved is deleted after its prose is merged into the step prose; the `[!IMPORTANT]` pointers go; INDEX follows; the CHANGELOG entry says "folded into <files>". A fold the script cannot decide is listed as a warning; `executor close` routes it to docs `fold` |
## HTML
Never part of this flow (the single home of this rule, DS45): no agent and no script of prd-flow builds, edits or reads the PRD or TRD page. The default gate only warns when a page is stale (G29 PRD, G32 TRD) or when `html_mode` is still `hand` (G5); those warnings are expected after a docs commit and are not routed. The pages are rebuilt by the `/docs-html` skill, when the user runs it; executor `close` ends its return with "`/docs-html` refreshes the reading pages" when the change touched `docs/prd/` or `docs/trd/`.

## Gate and commit
`<python> .claude/skills/prd-flow/scripts/gate.py`: ERROR blocks the commit; a WARNING about "earlier drift" belongs to the base, not to this change, and goes into the return as an out-of-scope divergence. The docs agent commits `docs(prd): <sentence in the git log style>`, markdown only, no push.
