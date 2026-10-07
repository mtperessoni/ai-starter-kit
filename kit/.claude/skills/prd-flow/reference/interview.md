# Interview (C5, step 4)

IDs, texts and paths in the examples are illustrative: always read the real line.

Ask only the dimensions that the pre-interview of `pack.md` left **open**; the answered ones enter the read-back as facts. Rounds are the most expensive part of the skill (the context is already large), so each one must count.

## Format of a question
AskUserQuestion, at most 4 per round, each with:
- product language, not code language: a usage example ("the customer taps Pay twice → the app ...?") and the effect on the user, the operator or the stored record. No rule IDs, symbol names, internal acronyms or words like "flag", "key", "handler"; IDs belong to the read-back. If the user asks for clarity, restart from the example and cut by half, without repeating the previous text;
- a concrete scenario: "Payment provider takes 45 s to answer → the app ...?";
- options with the trade-off in the description, the recommended one first, marked "(Recommended)";
- nothing the code or the PRD already answers.

## Dimensions
| ID | Dimension | Guiding question |
|---|---|---|
| D01 | Happy path | What happens, step by step, in the common case? |
| D02 | Variants | Does it hold the same on each variant listed in `repo.md` (platforms, channels, engines)? |
| D03 | Tenants | Does it hold for every tenant or customer, or vary? If it varies, which configuration field carries the variation? |
| D04 | Numbers | Limits, ceilings, timeouts: which value, where is it configurable, who changes it? |
| D05 | Failures | Dependency down, timeout, invalid response: what does the user experience and in which state does it end? |
| D06 | States | In which state does the rule apply; which transition creates or removes it? |
| D07 | Safety and risk | Can it harm the user, expose sensitive data, or bypass a control? Which guard covers it? |
| D08 | Contract | Does what consumers receive change? Can they accept and store it? |
| D09 | Audit | What is recorded to answer "what did the system receive and produce, and why"? |
| D10 | Privacy | Does new personal data go to a log, a model, a third party or the database? Masked? Deleted on request? |
| D11 | Rollback | How does it go back without a deploy? |
| D12 | Governance | If it is editable configuration: approval, immutable versions, audit of the publish |
| D13 | Transition | Sessions or requests in flight during the deploy: old rule or new? |
| D14 | Observability | Which log or metric shows the rule working? |
| D15 | Acceptance | Which test, with which input and which output, proves the rule? |

Extra domain dimensions (D16 and up) are in `repo.md`.

## Closing each round
Show the rows as they would look and ask for corrections. Record the round in `interview.md` (one line per question: dimension, question, answer, default adopted).

## Exit criteria
1. Every dimension answered, or "not applicable" with a reason.
2. Every row with ID (or section and number, for a table without IDs), text, Source (`planned`) and Change via.
3. No contradiction with a live rule; the superseded ones listed.
4. Every trade-off of the confrontation with a decision.
5. A final read-back and an explicit "it is clear" from the user.

Then write `approved-rules.md`:

```markdown
# Approved rules · <slug> · <YYYY-MM-DD> · <approver>
## docs/prd/product/04-checkout.md
| CHK-02 | *(approved 2026-10-04, pending code)* Payment waits at most 20 s for the provider, then shows "try again" and keeps the cart. | planned | config |
| CHK-13 | *(approved 2026-10-04, pending code)* A request in flight during the deploy keeps the timeout it started with. | planned | code |
## Supersedes
- CHK-02 (30 s)
```

If the user wants to stop earlier: save the state and say what is missing. A rule with an open dimension does not go to the PRD; it becomes a `Q-` row in "Open questions" with the adopted default, if the user prefers to continue.
