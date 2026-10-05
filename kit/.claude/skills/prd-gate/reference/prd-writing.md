# Writing the PRD (F5)

IDs, texts and paths in the examples are illustrative: always read the real line.

## Where to write
| Change | Form |
|---|---|
| Stays inside one section | In-place edit, in the table of the section that owns the ID |
| Crosses sections or variants | An amendment section (`<prd>/NN-NN-<slug>.md`, "Amendment X"), with a short `> [!IMPORTANT]` note in each affected section pointing to it |
| C4 (stale PRD) | In-place edit, old text literally to the CHANGELOG |

## Rule rows
Table format: `| ID | Rule | Source | Change via |`. Risks and problems use `| R-NN · high | ... |`.

| Situation | How it looks |
|---|---|
| New ID | Next free number of the prefix. Never renumber or reuse |
| Approved, no code yet | `*(approved YYYY-MM-DD, pending code)*` at the start of the text; Source `planned` |
| Rule the new one supersedes | Keeps its text and gets `*(superseded: <link to the new rule>, valid until deploy)*` at the start |
| `Q-`, `R-`, `S-` answered | Append `*Decided on YYYY-MM-DD: <decision>, see <ID>.*` at the end; nothing is deleted |
| Table row without ID | Keeps the table format and is cited by section and number (`04-02 #5`). Do not invent an ID. Approved without code: the marker goes at the start of the text cell |
| Promotion (last task of the plan) | Old text literally to the CHANGELOG, the superseded row leaves, the markers leave, Source gets the real file |

Style: English, product language; a technical term only in backticks and explained. Source with a file (and symbol when it helps), never a line or a default value. No em dash.

## CHANGELOG
New entry at the top:

```markdown
## <Name of the change> (YYYY-MM-DD, <approver>, <change folder or branch>)

Reason: <one sentence>. IDs: CHK-02, CHK-13.

### product/04-checkout.md

**CHK-02** (whole row). Superseded by <link>.

    | CHK-02 | <old row, literal> |
```

In C5 the entry is created in F5 with the reason and the IDs; the literal excerpts are added at promotion, when they leave the body. In C4 the excerpts go in already in F5.

## INDEX and README
- `INDEX.md`: the IDs column of the file's row (range `CHK-01..13`), the TRD column when a feature file appears. A new amendment section gets its own row.
- `README.md`: "State per spec" and "What weighs most today" only when the change affects them.

## HTML (only when `repo.md` sets `html` to a path)
It is maintained by hand and is what people read, so every markdown edit goes into it in the same commit.
- Rule row: `<tr data-via="config"><td>CHK-02</td><td>text</td><td>source</td></tr>`. Risks and problems also carry `data-sev="high|medium|low"`.
- Locate by ID (`Grep ">CHK-02<"`) and replace exactly that line. Markers become `<i>(...)</i>`; links become `<a href="#<anchor>">`; backticks become `<code>`.
- The rule text must have the same words as the markdown: the gate compares word by word.
- Never rewrite the whole file, nor touch scripts, styles, tabs or filters.

## Gate and commit
`python .claude/skills/prd-gate/scripts/gate.py`: ERROR blocks the commit; a WARNING about "earlier drift" belongs to the base, not to this change, and goes to the final list of divergences. Commit `docs(prd): <sentence in the git log style>`, markdown and HTML together, no push.
