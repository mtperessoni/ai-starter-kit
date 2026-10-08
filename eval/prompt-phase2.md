/prd-flow resume {slug}

Load the prd-flow skill first, then read the change's `state.md` and follow its `phase` line and its execution steps.

You are working alone in this repository, unattended. Nobody can answer questions. Where you would ask the user something, use the decisions below; where they do not cover it, take the recommended option. Never push.

Each task goes to an executor subagent with a one-line prompt and the main thread commits each task. At the end of every wave, review the diff with a `prd-flow-reviewer` subagent under the review ceiling, saying `review: N/5` every round and sending findings back to an executor until the review is clean or the ceiling is reached. The task card never makes the review optional.

## Decisions

{decisions}

## When you finish

End with a summary of at most 10 lines that lists every commit you made (hash and subject) and anything you left undone.
