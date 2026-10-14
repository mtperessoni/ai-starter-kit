# Questions for the blind reader

Answer each question only from the repository you were given: its `docs/`, `changes/`, source, tests and git history. Cite the file (and line or symbol) or the commit that gives each answer. Say "not found" when the repository does not tell you.

1. What is the current reconnect window of the conversation, and in which file and symbol is it implemented?
2. Which test files and test names prove that window?
3. What was the previous window value, when did it change, and what decision or reason is recorded for the change?
4. Is the countdown shown while reconnecting a documented rule? Give its ID and the exact on-screen format.
5. What happens when the countdown reaches zero while a connection attempt is still under way, and where is that decided?

## Ground truth (for grading, never given to the reader)

| Q | Correct answer |
|---|---|
| 1 | 90 s; `lib/timing.ts::RECONNECT_WINDOW_MS` (90_000) |
| 2 | `lib/__tests__/session-connection.test.ts` (a 90 s case and the hanging-attempt case); optionally `reconnect-policy.test.ts` |
| 3 | 60 s; changed 2026-10-14; the request to extend to 90 s plus decision 1 = A (stop the attempt at zero) |
| 4 | Yes, CNX-10; "Só um instante, estou voltando… 85 s" (whole seconds after the text, screen readers read the message once) |
| 5 | The attempt under way is stopped and the CNX-03 connection-lost message shows at once; decided in CNX-03 (decision 1 = A) |
