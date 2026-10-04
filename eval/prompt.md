You are working alone in this repository, unattended. Nobody can answer questions.

Follow this repository's own instructions end to end: classify the request, document it, plan it, implement it test first, run the gates, and commit. Where you would ask the user something, use the decisions below; where they do not cover it, take the recommended option. Never push.

## How this team works

{protocol}

## How work is executed here

Execute the plan the way the repository's execution rules say (`.claude/skills/prd-gate/reference/execution.md` and `workers.md`): each task goes to an `executor` subagent with a one-line prompt, the main thread commits each task, and at the end of each wave a `reviewer` subagent reviews the diff with the review ceiling, saying `review: N/5` every round and sending findings back to an executor until the review is clean or the ceiling is reached.

## Request

{request}

## Decisions

{decisions}

## When you finish

End with a summary of at most 10 lines that lists every commit you made (hash and subject) and anything you left undone.
