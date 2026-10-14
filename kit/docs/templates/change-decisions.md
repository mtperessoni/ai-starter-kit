# Decisions · <NNN-slug>

Size L only. Sizes S and M record the same facts in the commit body (`Request:`, `Decided:`, `Assumed:`, `Red:`, then `Rules:`) and keep no file.

Reply 1: "<the user's reply to the sheet, verbatim>"
Reply 2: "<the reply to the follow-up sheet, verbatim; delete this line when there was none>"

Product trade-offs decided on the sheet of this change: one row per answer that chose between real options. Technical decisions stay in `design.md`. The rows of the rules land in the PRD with the code task that implements them; this file never feeds the CHANGELOG, which is frozen.

| ID | Question | Decision | Rejected alternative | Why | Rules |
|---|---|---|---|---|---|
| DEC-01 | <the question that had real options> | <what was chosen> | <the option that lost> | <the specific reason> | <PFX-01, PFX-02> |
