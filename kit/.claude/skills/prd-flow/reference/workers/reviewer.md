# reviewer

Instructions the main thread puts in the prompt of the task's reviewer agent (from `repo.md`), besides the diff:

- "Round N/5 of `.claude/skills/prd-flow/reference/review.md`." In round 1, the delivery diff; from round 2, only the fix diff and the list of previous findings (V03): say resolved or not for each and point out only new problems that diff created.
- Each finding on one line: `[Critical|High|Medium|Low] CS-NNN · file:line · rule · concrete scenario in one sentence · fix in one sentence`. At most 8 findings, the most severe first.
- Severity by consequence to the user or the delivery, not elegance. "Possible in theory" without a concrete scenario is Low.
- Return at most 20 lines; ceiling per review.md V08. A finding that is a behavior outside the approved rules is marked `R09`. Findings only: never edit code or write files.
