# Blind reader answers, graded against grader-questions.md

## W4 (A2)
1. 90 s, `lib/timing.ts:14 RECONNECT_WINDOW_MS = 90_000`, CNX-01. Correct.
2. reconnect-policy.test.ts "holds a 90 s window"; session-connection.test.ts "stops 90 s after the first drop", "stops an attempt that hangs at exactly 90 s (CNX-03, DEC-01)", text conversation case. Correct.
3. 60 s (3c3ebf27); changed 2026-10-14 (e853a774, promote 2379aa5a); reason from `changes/archive/004-reconnect-window-90/plan.md` T01 "Why"; decisions.md holds "Reply 1: ok". Correct. Also flagged the stale "(today: it stops at 60 s)" in CNX-01.
4. CNX-10, "Só um instante, estou voltando… 85 s", screen readers read once. Correct.
5. Attempt stopped, CNX-03 message at once; decided in decisions.md DEC-01, implemented in `startConversationConnection`. Correct.
Score: 5/5.

## W2 (A1)
1, 2, 4, 5 correct (timing.ts:14; session-connection and reconnect-policy tests plus the new hook test; CNX-10 format; DEC-01 in decisions.md). 3: 60 s (3c3ebf27, DEC-07 of change 003), changed 2026-10-14 (876d10f4, PRD 83a5c3c4, promote 20de8dcb), reason from the CHANGELOG entry. Score: 5/5.

## W3 (B1)
1, 2, 4, 5 correct (5 decided in CNX-03; the commit message adds "so the count never sits at 0 s"). 3: 60 s and 2026-10-14 (e4dd675c) correct; "no decision records why 60 became 90", and the rejected alternative of decision 1 is not recorded. Score: 4.5/5.

## W1 (B2)
1, 2, 4, 5 correct (5 traced to `endWindow` and CNX-03). 3: 60 s and 2026-10-14 (08cf8674) correct; reason "not found". Score: 4.5/5.

## Reading cost
Second leg only (after the junction allowance): W4 7 calls 51 s, W2 10 calls 71 s, W3 12 calls 78 s, W1 10 calls 79 s. Finding the answers costs about the same in both arms.
