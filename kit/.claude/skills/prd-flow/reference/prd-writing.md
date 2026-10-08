# Writing the PRD (F5)

IDs, texts and paths in the examples are illustrative: always read the real line.

## Writer steps (C5 step 5)
| Step | What the `writer-prd` does |
|---|---|
| 1 | Writes the PRD files from `approved-rules.md` (rows literal, with the Example cell when present) |
| 2 | Builds the HTML (section "HTML" below), updates CHANGELOG and INDEX |
| 3 | Writes the `Decisions:` block of the CHANGELOG entry from `changes/NNN-<slug>/decisions.md` |
| 4 | Runs `gate.py --step prd --rules <approved-rules.md> --applied` once: the default checks, Q4 (a row of the file not in the PRD with identical cells) and G28. Step 6 shows its last line from the return |
| 5 | Commits `docs(prd)` with `decisions.md` and the PRD together |

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
| Example column | One line `<given> → <expected outcome>` in product language, for example `Provider silent for 20 s → "try again" shown, cart kept` (illustrative). Required for a rule with a number, a branch or a failure path; the D15 answer lands here. Four-column tables stay valid. The HTML renders it |
| Proposed (comes only from documents, not proven by code) | `*(proposed)*` (the `proposed_marker` of `repo.md`) at the start of the text; Source `planned`. Input of C5, never C2. Greenfield M2 rules come from the interview and are approved, not proposed |
| Approved, no code yet | `*(approved YYYY-MM-DD, pending code)*` at the start of the text; Source `planned`. Approving a proposed rule replaces its `*(proposed)*` marker with this one |
| Rule the new one supersedes | Keeps its text and gets `*(superseded: <link to the new rule>, valid until deploy)*` at the start |
| `Q-`, `R-`, `S-` answered | Append `*Decided on YYYY-MM-DD: <decision>, see <ID>.*` at the end; nothing is deleted |
| Table row without ID | Keeps the table format and is cited by section and number (`04-02 #5`). Do not invent an ID. Approved without code: the marker goes at the start of the text cell |
| Promotion (last task of the plan) | See "Promotion" below |

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

In C5 the entry is created in F5 with the reason, the IDs and the Decisions block (rows copied from `decisions.md`); the literal excerpts are added at promotion, when they leave the body. In C4 the excerpts go in already in F5. The Decisions block is what impact K12 shows later as `Decided <date>: <why>; rejected: <alternative> (<why>)`.

## INDEX and README
- `INDEX.md`: the IDs column of the file's row (range `CHK-01..13`), the TRD column when a feature file appears. A new amendment section gets its own row.
- `README.md`: "State per spec" and "What weighs most today" only when the change affects them.

## Promotion (last task of the plan)
| Step | Rule |
|---|---|
| P1 | Old text literally to the CHANGELOG; superseded rows leave; markers leave; Source gets the real file |
| P2 | The `decisions.md` rows are in the CHANGELOG entry under `Decisions:` (copied, not summarized) |
| P3 | Fold amendments (the single home of this rule): each amendment row moves to the step section that owns the behavior (ID unchanged, markers removed, Source filled); an amendment file whose rows all moved is deleted after its prose is merged into the step prose; the `[!IMPORTANT]` pointers go; INDEX follows; the CHANGELOG entry says "folded into <files>" |
| P4 | Rebuild the HTML (section "HTML") |

## HTML (only when `repo.md` sets `html` to a path)
| `html_mode` | Procedure |
|---|---|
| `generated` | Run `python .claude/skills/prd-flow/scripts/build_prd_html.py` after every PRD edit and commit the result with the markdown. Never edit the HTML by hand; G29 fails when it is out of date (`--check`) |
| `hand` | Kept briefly for repositories not yet migrated (`/ai-kit update` offers the migration). The HTML is maintained by hand, so every markdown edit goes into it in the same commit. Rule row: `<tr data-via="config"><td>CHK-02</td><td>text</td><td>source</td></tr>` (risks and problems also carry `data-sev="high\|medium\|low"`). Locate by ID (`Grep ">CHK-02<"`) and replace exactly that line; markers become `<i>(...)</i>`, links `<a href="#<anchor>">`, backticks `<code>`. The rule text has the same words as the markdown (the gate compares word by word). Never rewrite the whole file nor touch scripts, styles, tabs or filters |

## Gate and commit
`python .claude/skills/prd-flow/scripts/gate.py`: ERROR blocks the commit; a WARNING about "earlier drift" belongs to the base, not to this change, and goes to the final list of divergences. Commit `docs(prd): <sentence in the git log style>`, markdown (and HTML) together, no push.
