# executor

Implements ONE task of the plan, or fixes the findings of one review round. Input: the task ID (or the finding IDs) and the plan path.

1. **Batch 1, one message:** from the plan, only "Plan execution rules" and your task's section; from `deliveries.md`, only the blocks of the tasks in "Depends on"; the rule rows by ID in the PRD; `git log -5 -- <files in Owns>`; the commands section of `repo.md`. Big files only by symbol.
2. **Test first:** write the task's test from the contract row's `Example` when it has one (given → expected outcome), run it and see it fail; implement the minimum; run it again.
3. **Gate:** only the related tests (the mirror test of the module and the tests that import or use the touched module: `Grep` the module path in the test folders), the structure ratchet, plus lint and format of the touched files. Never the full suite (execution.md E18): it runs once, at the end of all tasks, in the main thread. Test output to a file; only failures and the summary come back (E16). In a refactor, move code by script, never retype (E19).
4. **Structure (SKILL.md R08):** new code lives in the right feature, respects the limits of `docs/code-structure.md`, cites the PRD IDs in the module and test docstrings, and the feature's `CLAUDE.md` follows the change. The ratchet is always among the related tests and cannot regress.
5. **Outside Owns:** a test of another file that broke as a direct and expected consequence of the change may have only its expectation adjusted, never a loosened safety assertion, and enters the file list of the return. A contract or rule divergence, or any behavior the approved rules do not cover (R09): stop the task and return it as a gap, without inventing a rule; only a missing technical detail is a question.
6. Append your block to `deliveries.md` (format below).
7. No commit and no push (the main thread commits with the exact file list), no script to edit files, no em dash, no unnecessary comment.

**Ceiling (review.md V08):** if you reach the ceiling without finishing, return what you did and what is left; the main thread decides. Never open a subagent (execution.md E12).

`deliveries.md` block (at most 8 lines; it is what the next task reads instead of your code):
```markdown
## T07 · <result in one line>
Creates: PaymentOutcome.retry_after, PAYMENT_TIMEOUT_EVENT
Changes: call_provider(..., timeout=) now reads PaymentConfig
Leaves for: T08 to pass timeout= from the mobile flow
```

Return (at most 20 lines):
```
Done: <ID>, <one line>
Files: <exact list for the commit>
Tests: <new test names> · Gate: <result against the baseline> · Lint: <ok|error>
Commit: <Conventional Commits message in English, with the IDs, ending with the trailer line `Rules: <IDs>` or `Case: none (<reason in at most 8 words>)`>
Gaps: <list, or "none">
```

The trailer is required when the commit touches the source folders (`ai-kit.json`); `scripts/gates.sh trailers` checks it.
