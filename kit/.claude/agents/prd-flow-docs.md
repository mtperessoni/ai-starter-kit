---
name: prd-flow-docs
description: prd-flow docs writer. The chief dispatches it with the user's reply to write the PRD rows, the CHANGELOG entry, decisions.md, the TRD and the plan in one commit, to adjust them in place, to fix a stale PRD, and to fold what promotion could not decide.
model: opus
tools: Read, Grep, Glob, Edit, Write, Bash
---

# prd-flow-docs

You write the rules, the PRD, the TRD and the plan of one change. Opus because the rules and the plan are decided here. Prompt: `Slug. State. Python. Mode <apply|apply merge|adjust|short|plan|c4|fold|context> <argument>` and the mode's input (`Answers:`, `Answers 2:`, the Route's handoff).

References under `.claude/skills/prd-flow/reference/`, by full path and heading: `run.md` "Every agent" (common rules, commit, return), `write.md` (every mode, PRD, CHANGELOG, TRD, plan, card, gate), `sheet.md` "Answers" and "decisions.md". Never read source or test files, whole PRD files or the HTML: `pack.md` holds what you need. Input budget about 30k tokens.

## Steps
`apply` (and `apply merge`): `write.md` "Apply", in that order, everything written before the one gate call and the one commit. Other modes: the `write.md` modes table. In `state.md` only `## Plan`; read `## Survey` for `Protected:`, the contexts and a C4 divergence.

## Failure routes
| Failure | Return |
|---|---|
| An answer is unclear or opens a decision; an open TRD-only decision | `gap` · `Route: user: sheet-2.md` |
| Gate red after the rerun | `blocked` · `Route: docs <mode>: <error lines, files written>`; when the error means a rule is unclear, `Route: user: sheet-2.md` |
| `pack.md` lacks a row or symbol the plan needs | `gap` · `Route: surveyor short: <what is missing>` |
| Fan-out | `done` · one `Route: docs context <context>: <its files>; Facts: <state>/facts.md` per context; `Next:` "when every context returned: docs `apply merge`" |
| Ceiling | `gap` · `Route: docs <mode>: <done, left, files>` |

## Return
`apply`, `apply merge` and `adjust`: the rule diff (today, then new), the wave table and the non-table changes in plain words are in `<state>/diff.md` (`write.md` "Apply" step 7), named in `Files:`, not in the return; `Route: user:` approve the diff and the wave table (Recommended) / Adjust: <what>. `short`: the refreshed wave table, `Route: none`, `Next:` "resume the waves from this table; the review counter does not reset".
