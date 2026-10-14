# Scenario format

A scenario is one frozen rule change on one repository, kept in the project at `.claude/skills/docs-flow-eval/scenarios/<name>/`: `scenario.json`, `questions.md`, `fixtures/` (`sheet.md` and `pack.md`, the frozen survey, with `{WORKTREE}` where the worktree path goes). Results live beside it in `.claude/skills/docs-flow-eval/results/`.

| Key | Meaning |
|---|---|
| `name`, `slug` | Folder and worktree name; the prd-flow state slug |
| `repo`, `base` | The scenario repository and the commit every run starts from |
| `case`, `size`, `request`, `sheet_answer` | The prd-flow case and size, the request in the user's words, the answer given to the sheet |
| `fixtures`, `questions` | Folder of the frozen survey; the readers' questions file |
| `stale_patterns`, `stale_context`, `stale_allow` | Q1: regexes of the old value, the words that make a match a rule mention, and the lines allowed to keep it |
| `constant` | Q2: `glob`, `regex` (group 1 is the value) and `expected` |
| `new_rule_pattern` | Q3: regex of the new rule's wording in the PRD rows |
| `decision_regex`, `rejected_regex` | Q8: the recorded decision and its rejected alternative |
| `answer_key` | One line per reader question; the chief grades each answer 1, 0.5 or 0 |
| `fixture_version`, `decided_in_conversation` | Provenance of the fixtures and the verbatim decision given to the surveyor |

Q4 to Q11 need nothing from the scenario beyond `base` and `slug`. Fixtures are frozen: a new survey is a new scenario.
