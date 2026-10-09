/prd-flow resume {slug}

Load the prd-flow skill first, then read the change's `state.md` and follow its `phase` line and its execution steps.

You are working alone in this repository, unattended. Nobody can answer questions. The decision sheet (`sheet.md`) was printed and the turn ended; the reply below is the user's answer to it, by number: `ok` accepts every recommendation and assumption, `1B` picks option B of decision 1, `A2: ...` corrects assumption 2, `scope: ...` corrects what does not change. Pass it verbatim to docs `apply`. If an answer is unclear, write the one follow-up `sheet-2.md` and answer it from the notes at the end of the reply; an item still open after that becomes a `Q-` row with the recommended default. Where you would ask the user anything else, take the recommended option. Never push.

Follow the repository's own rules for who does each step. Reviews use a `prd-flow-reviewer` subagent under the review ceiling, with `review: N/5` stated every round, and the task card never makes the review optional.

## Reply to the sheet

{decisions}

## When you finish

End with a summary of at most 10 lines that lists every commit of the run (hash and subject) and anything you left undone.
