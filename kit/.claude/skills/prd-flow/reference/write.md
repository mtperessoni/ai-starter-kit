# Write (docs; the surveyor reads "Card")

Docs writes the PRD, the CHANGELOG entry, `decisions.md`, the TRD and the plan of one change, from `pack.md`, never from source. Examples are illustrative.

## Apply
1. Read the state's `sheet.md`, the reply, `pack.md`, and `sheet.md` "Answers" and "decisions.md" of this folder. Check the combination of the answers. An unclear answer: write only `sheet-2.md`, return `Route: user: sheet-2.md`; on `Answers 2:` continue. One follow-up, hard stop: after `Answers 2:` never another sheet; what stays open is a `Q-` row with the recommended default.
2. `changes/NNN-<slug>/decisions.md`: the `Reply` lines verbatim, then the DEC rows.
3. PRD rows ("Rule rows"), contract and transition lines, CHANGELOG entry, INDEX and README; the ADR when `## Survey` has `Protected:` (`docs/adr/README.md`; at least two real negative consequences and two considered alternatives; index updated). A new product context: the anatomy of `.claude/skills/prd-create/reference/anatomy.md`, approved rows only.
4. TRD ("TRD"), then the plan ("Change folder", "Plan", "Card").
5. Everything written, `scripts/gates.sh docs <slug>` once; fix what it flags; one rerun.
6. One commit, `docs(prd): <sentence>`, holding PRD, CHANGELOG, INDEX, README, ADR, TRD and the change folder.
7. Write the rule diff as written (today, then new) and the wave table (ID, result, owns, depends on, wave, model, lens) to `<state>/diff.md`, with the non-table changes in plain words; name it in `Files:`. `Route: none`, `Next:` "print `diff.md` verbatim and end the turn": the user's reply in chat is the approval, a correction is `adjust: <words>`.

Never write `answers.md`, `rules.md` or `approved-rules.md`, never run `state_record.py`: the PRD diff and the CHANGELOG entry are the approved set. Never write a mechanism (rollback, switch, configuration key, environment variable, table, column, endpoint) that is not in the sheet or a `Reply` line.

| Mode | Does |
|---|---|
| `apply merge` | After every `context` returned: steps 3 (entry, INDEX, README) to 7 once, deciding nothing |
| `adjust: <words>` | In place, never revert and redo: the rows, entry, TRD and cards the words touch; the docs gate once; a new commit; rewrites `<state>/diff.md` (step 7) |
| `short <YYYY-MM-DD>` | `run.md` "Short C5", from `sheet-short-<k>.md` and its reply (already the approval): PRD rows, the entry's `IDs:` extended, a `Reply` line and DEC rows, new and `redo` cards (Read and Owns from `pack.md`), the wave table replaced in `## Plan`; outside a C5 it creates the change folder and `plan.md` |
| `plan` | C2, C3 or C6 over more than one task (the surveyor's `Route: docs plan`): TRD and plan from the rows of `## Survey`, no PRD change; committed before the baseline |
| `c4` | The `## Survey` divergence: the PRD row in place and the old text literally into a CHANGELOG entry in the same run; the TRD body only when files, entry points or tests moved; `gate.py --step prd` (and `--step trd`) once; one commit |
| `fold: <lines>` | What promote could not decide: an amendment fold (P3), a `design.md` destination of a size L, or a superseded row that matches no PRD row; commit `docs(prd): fold <slug>` |
| `context <folder>` | Fan-out: read `<state>/facts.md` first; PRD and TRD of that context's files only; no CHANGELOG, INDEX or commit |

Fan-out: when `## Survey` says `fan-out: yes`, `apply` first writes `<state>/facts.md` (one row per fact the contexts share: key names, invariants, owners, call sites, with its owner context) and returns one `Route: docs context <context>: <its files>; Facts: <state>/facts.md` per context. Every context agent follows `facts.md`. Then `apply merge` (modes table).

## Rule rows
Table `| ID | Rule | Source | Change via |` with an optional `Example` column; risks `| R-NN · high | ... |`.

| Situation | How it looks |
|---|---|
| New ID | Next free number of the prefix; never renumber or reuse |
| Example | One line `<given> → <expected outcome>` in product language; required for a rule with a number, a branch or a failure path; the sheet's `Example:` lands here |
| Approved, no code yet | `*(approved YYYY-MM-DD, pending code)*` at the start of the text (marker word from `repo.md` `pending_marker`); Source `planned`. Approving a `*(proposed)*` row replaces that marker |
| Rewritten | Same ID, new text with the approved marker; its old row goes literally into the CHANGELOG entry |
| Superseded | Keeps its text with `*(superseded: <link to the new rule>, valid until deploy)*` at the start, until promote removes it |
| `Q-`, `R-`, `S-` answered | Append `*Decided on YYYY-MM-DD: <decision>, see <ID>.*`; nothing is deleted |
| Row without ID | Cited by section and number (`04-02 #5`); never invent an ID; the marker goes at the start of the text cell |

`--final` fails while a `*(proposed)*` row is left (G30). Source names a file (and symbol), never a line or a default value.

| Change | Where |
|---|---|
| Inside one section | In place, in the table that owns the ID |
| Across sections or variants | An amendment section `<prd>/NN-NN-<slug>.md`, with a short `> [!IMPORTANT]` pointer in each affected section |

Contract and transition: what consumers receive, and what happens to requests in flight, existing records and rollout, are sheet decisions. When no approved row states the answer, write one line under the owning table, citing the rules it qualifies; "nothing changes" is written too:
```markdown
Contract: the receipt layout and its fields do not change (CHK-09).
Transition: applies to every order from now on; no switch, no migration of existing orders (CHK-09).
```

## CHANGELOG
One entry per slug, newest first; prose in the repo `language`, the labels stay as written:
```markdown
## <Name of the change> (YYYY-MM-DD, <approver>, changes/NNN-<slug>)

Reason: <one sentence>. IDs: CHK-02, CHK-13.
Conflicts: CHK-05 compatible (retry reuses the same timeout).
Supersedes: CHK-07.
Owner: decided by <owner>, written by <approver>

### product/04-checkout.md

**CHK-02** (whole row), rewritten.

    | CHK-02 | <old row, literal> |
```
| Line | Rule |
|---|---|
| `IDs:` | Every approved row of the change, new and rewritten; promote and the gate take the approved set from here |
| `Conflicts:` | Every ID of the pack's `Conflicts:` not rewritten or superseded, as `compatible (<why>)`; `none` when empty |
| `Supersedes:` | IDs that keep their text with the superseded marker until promote; `none` when empty |
| `Owner:` | Only when `repo.md` "Rule owners" applies |
| Excerpts | The old literal row of each rewritten ID, from `pack.md`; promote adds the rest (P1, P2) |

INDEX: the IDs column of the file's row (range `CHK-01..13`), the TRD column when a feature file appears; a new amendment section gets its own row. README: "State per spec" and "What weighs most today" only when affected.

## Promotion
`promote.py <slug>` (`--dry-run` to preview), run by executor `close`; no plan task does it.

| Step | Rule |
|---|---|
| P1 | Markers leave; superseded rows leave with their old text into the entry; Source gets the file of each `Source:` line of `deliveries/<task>.md` |
| P2 | The `decisions.md` rows are copied once into the entry under `Decisions:`, not summarized |
| P3 | Amendments fold (the single home of this rule): each amendment row moves to the section that owns the behavior (ID unchanged); a file whose rows all moved is deleted after its prose is merged; the pointers go; INDEX follows; the entry says "moved into <files>". What it cannot decide is a warning routed to docs `fold` |

HTML is never part of this flow (the single home of this rule): no agent or script of prd-flow builds, edits or reads the PRD or TRD page. The default gate never prints a stale page (G29, G32 only under `gate.py --html`); `html_mode: hand` (G5) is only a warning, never routed; `/docs-html` rebuilds the pages.

## TRD
The TRD says where each feature lives and what must not break; it never repeats a rule. Symbols come from `pack.md`.

Size M: no Planned section. The last code task of each area owns `docs/trd/<area>.md` and updates the body with the names the code used. Size L: a Planned section (heading `repo.md` `planned_heading`) at the end of the area file (or the part file that owns the rules), merged into the body by the last code task of the area:
```markdown
## Planned (<name of the change>, <branch>)
Rules: CHK-02, CHK-13 → [04](../prd/product/04-checkout.md)

| File | Changes or creates | Symbols | IDs |
|---|---|---|---|
| `src/features/checkout/payment_call.py` | changes | `call_provider` | CHK-02, CHK-13 |

Entry into the flow: <path by symbols>. Tests to write: <test file> (CHK-02, CHK-13).
Invariants: I-31 (new) · affected: I-12. Must not break: <what the change touches>.
```
| ID | Rule |
|---|---|
| TP01 | Planned holds files, symbols and IDs only: no parameters, intervals or values |
| TP02 | Tests to write: file and IDs, never expected values (they are the Example column) |
| TP03 | Contracts live only in `design.md`; Planned links to it |
| TP04 | A card points to the Planned row by file instead of describing it again |
| TP05 | Every cited ID exists in the PRD; the module will cite the IDs it implements |
| TP06 | An open TRD-only decision (no PRD or `DEC-` row settles it) goes into the one `sheet-2.md` while unused, no plan before its reply; else a `Q-` row with the recommended default, never a second sheet |
| TP07 | Each card's Contract covers the TRD IDs of its Owns files; each created symbol has a non-test caller owned by a card |

Over `trd_budget_lines` (G26) an area splits into `docs/trd/<area>/<part>.md` plus a README. No History section. A new area file copies the sections of the others and gets a row in `docs/trd/README.md`. A new invariant takes the next free row of its kind in `invariants.md`, with its proof.

## Change folder
`changes/NNN-<slug>/`, the number the surveyor reserved. Size M: `decisions.md`, `plan.md`. Size L: also `brief.md` and `design.md` (templates in `docs/templates/`) before the plan. Only a prompt, config or env change: the plan is the publish or deploy task of `repo.md` "Change routing", no folder. A folder that already covers the touched rules gets the new tasks, up to about 60 KB. With `repo.md` "Spec-kit" `kept`, its `spec.md` cites PRD IDs and defines no FR; `tasks.md` is not used.

## Plan
`plan.md`: title, `## Constitution check` (`| Principle touched | How the plan honors it, or the justified violation |`, one row per principle touched), then the cards. No orchestration rule is copied into it. Check with `git log --oneline -- <paths>` which dependencies are done. `code` becomes cards; anything owned by another repository becomes a handoff note with the rule rows, outside the plan.

The docs gate prints the waves (`WAVE n: T01, T02`, critical path first, at most 4 per wave) and `CRITICAL PATH`, and errors when two tasks of a wave own one file. Replace `## Plan` of `state.md` with `Plan: <path>`, the `WAVE n:` and `CRITICAL PATH` lines verbatim, each task's model (`sonnet` unless the card gives a reason) and lens, and a last line `Review: per wave` when any wave has 2 or more tasks, else `Review: once after the last wave`.

## Card
A card has at most 25 lines; every field is mandatory. The surveyor `light` writes one to `<state>/card.md` for a one-task C2, C3 or C6.
```markdown
### T03 · <verb + result>
Contract: CHK-02
Why: <at most 3 lines: the user's words or the rule's Example that motivates the task>
Owns: src/features/checkout/payment_call.py, src/features/checkout/tests/test_payment_call.py
Read: docs/trd/checkout.md, src/features/checkout/payment_call.py::call_provider
Reached from: POST /checkout handler `checkout_route` calls `call_provider` | none (a pure refactor creates no symbol)
Depends on: T01 | none
Creates / consumes: creates `PaymentOutcome.retry_after`; consumes `PaymentConfig.provider_timeout_seconds` (T01)
Tests: test_<behavior> in <file>, citing CHK-02, fails before the change
Decisions: DEC-03 | none
Leave: src/features/shipping/fee.py::free_shipping uses `>` at 200.00 | none
Commit: <type>(<scope>): <sentence>
        Rules: CHK-02            (or: Case: none (<reason in at most 8 words>))
Model: sonnet | opus (only for a new safety decision; reason on this line)
Lens: <a reviewer of repo.md "Reviewers"> | none
```
| Rule | Detail |
|---|---|
| Granularity | A task is at least one file and its test. Split only when the pieces run in parallel (disjoint Owns) and each is about 10 tool calls or more; sequential pieces of one area are one task; a one-rule change is one task |
| Affinity | Tasks reading the same large files go to one executor; waves group tasks by TRD area, two tasks of one area are serial or one |
| Interfaces | Shared names go in `Creates / consumes`; a consumer reads the producer's delivery, never its code |
| Reached from | Every created symbol names its caller; the last task of each feature is its wiring task |
| Owns | At most 8 files, a test path among them, plus the tests outside the area the change breaks (`Grep` who imports the changed symbols) |
| Read | Exact paths or `path::symbol`, about 25k tokens: the executor reads nothing else |
| Leave | The pack's out-of-scope divergences in or near the task's files; nobody changes them |

## Fix card
A cold fix (executor `fix`) gets a handoff of at most 10 lines, complete like a card; when the lines do not fit, `Lines:` is the findings file path:
```
Fix: CS-003, CS-005 (or: close failure, promote error)
Lines: <the finding or error lines, verbatim>
Owns: <the files named and their tests>
Read: <exact paths or path::symbol>
Rules: CHK-02
```

## Gate
`scripts/gates.sh docs <slug>` once after everything is written, one rerun after a fix (C4: `gate.py --step prd` and `--step trd`). Stdout carries the errors and `warnings: N (see <file>)`; read that file only to decide on a warning. An error blocks the commit. Among the checks: every `IDs:` entry is in the PRD with the pending marker (Q2), every pack `Conflicts:` ID is in `IDs:`, `Supersedes:` or `Conflicts:` (Q5), the mechanism terms (Q3), the waves, and the change number on a remote branch (G27, warning). Earlier drift belongs to the base: list it as out of scope, never fix it.
