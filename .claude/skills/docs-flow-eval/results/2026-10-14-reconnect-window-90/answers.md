# Blind reader answers, graded against answer_key (fixture 2026-10-14b)

## W2 = v2-1
1. 90 s, `lib/timing.ts:14`, CNX-01, glossary. 1
2. `reconnect-countdown.test.ts`, `reconnect-policy.test.ts`, `session-connection.test.ts:155` (CNX-01, CNX-10), hook test. 1
3. 60 s (DEC-07 of change 003), changed 2026-10-14 in 98c8b113, request in the commit body; decision 1A with "rejected: read every 15 s, or every second" found in the same body (cited under 5). 1
4. CNX-10, "Só um instante, estou voltando… 85 s", `copy.ts`, hook. 1
5. CNX-03 message replaces the count at zero; screen reader hears the message once (`aria-hidden` seconds); decided in CNX-10 and commit `Decided: 1A`. 1
Score 5/5. Finding: `Assumed: A1..A8` names IDs that live only in the git-ignored sheet, a dangling reference.

## W3 = v3-1
1 to 4 correct (timing.ts:14; session-connection 90 s cases, reconnect-countdown and hook tests; 60 s to 90 s in 4eed618f with the Request line; CNX-10 format). 5: CNX-03 message at zero, screen reader once, decision 1A with "rejected: 1B every 15 s, 1C every second" from the commit body; did not locate the aria-hidden code (did not open failure-notice.tsx), which the question does not require. Score 5/5. Same dangling `Assumed: A1..A8` finding.

## W1 = v3-2
All five correct (timing.ts:14 and TRD; session-connection, reconnect-policy secondsLeft and hook tests; 60 s to 90 s in b90c2fa8 with the Request line; CNX-10 format; CNX-03 at zero, failure-notice role alert plus aria-hidden seconds, decision 1A with rejected B and C from the commit body). Score 5/5.

## W4 = v2-2
All five correct (timing.ts:14 and glossary; session-connection 90 s and CNX-10 cases, reconnect-policy, countdown and hook tests; 60 s to 90 s in 6f762ab6 with the Request line; CNX-10 format via copy.ts; CNX-03 at zero, role alert plus aria-hidden, decision 1A with rejected 15 s and every second from the commit body). Score 5/5.

## Cross-reader findings
- Three readers flagged `Assumed: A1..A8`: IDs whose text lives only in the git-ignored sheet. Contract fix: write each assumption that shaped the code in words.
- Every reader noticed `changes/003-conversation-reconnect` (an older change still open) still says 60 s. Not a regression of any arm: open change folders that restate a rule go stale when the rule changes.
