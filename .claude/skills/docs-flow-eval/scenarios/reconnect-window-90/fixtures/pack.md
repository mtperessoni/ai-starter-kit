# Pack · reconnect-window-90
Base: 46b66879 · Branch: eval/reconnect-window-90/survey · Behind origin/staging: 1 (touches the scope: no, a merge commit with no file change)
Request: Raise the reconnect window of the conversation from 60 s to 90 s, counted from the first drop, and while reconnecting show the patient the seconds left ("Só um instante, estou voltando… 85 s").
Conflicts: CNX-01 (rewrite: the window 60 s becomes 90 s), CNX-03 (rewrite: its Example says "after 60 s"), CNX-04 (rewrite: "inside the 60 s window of CNX-01" and its Example; the row stays planned, held by change 003), CNX-09 (rewrite: its Example says "it stops at 60 s"); adds CNX-10 (the countdown)
Compatible (read, unchanged): CNX-07 (the turn wait stays paused while reconnecting, now up to 90 s), CNS-09 and Q4 (their 60 s is the farewell-text wait, another timer), CNS-10 (the countdown lives inside the existing reconectando state, no new state), CNS-11 (the countdown takes the 14 px of the failure alert). New rule: CNX-10 (the countdown; CNX-02 stays unwritten, DEC-02 of change 003)
Checked: docs/prd/conversation-connection/02..07, docs/trd/triage.md, docs/trd/invariants.md, .claude/skills/prd-flow/repo.md "Protected rules", lib/timing.ts, lib/reconnect-policy.ts, lib/session-connection.ts::startConversationConnection, lib/failure-copy.ts, lib/copy.ts::errors, lib/ending/failure-view.ts::failureKindOf, lib/screen/screen-machine.ts::screenState, lib/screen/screen-label.ts::screenLabel, components/conversational-screen.tsx (failure, screen label), components/failure-notice.tsx (role), hooks/use-waited-ms.ts, clara-ai origin/staging (resume window setting)

## Rules
### docs/prd/conversation-connection/05-drops-and-endings.md
| CNX-01 | When the connection of the conversation drops for a reason that does not end it, the screen shows "Só um instante, estou voltando…", blocks the answer box and tries again after 0.5 s, doubling the wait up to 8 s. The 60 s window counts from the first drop and restarts only when the conversation service answers on the new connection; a connection that opens and closes again before that answer, or a wait for another open window of the same triage, restarts neither the window nor the wait. | src/app/triage/[triageId]/(internal)/components/conversational/lib/reconnect-policy.ts::nextReconnectStep | frontend | The service accepts each new connection and closes it before answering → attempts after 0.5, 1, 2, 4, 8, 8 s...; 60 s after the first drop the screen stops trying and shows the connection-lost message (today: one attempt every 0.5 s with no end) |
| CNX-03 | When the window of CNX-01 ends, the screen shows "A conexão caiu e não voltou. Procure o balcão para continuar.", the answer box stays blocked and nothing tries again by itself; reloading the page resumes the conversation (CNX-06). | src/app/triage/[triageId]/(internal)/components/conversational/lib/session-connection.ts::startConversationConnection | frontend | Wi-Fi off for 2 minutes → after 60 s the message stays on screen; Wi-Fi back and page reloaded → the conversation resumes at the open question |
| CNX-04 | *(approved 2026-10-09, pending code)* When the conversation service closes the connection for a failure of its own (reason `SESSION_FAILED`, or the close code 1011), the screen tries again as for any drop, inside the 60 s window of CNX-01; a failure that keeps repeating after the service answers ends at the service's resume limit (CNX-05). | planned | frontend | Service closes with `SESSION_FAILED` → "Só um instante, estou voltando…", attempts after 0.5, 1, 2 s...; the service answers → the conversation resumes at the open question; the failure repeats with nothing new from the patient → at the 4th return the service ends with `RESUME_CEILING` and CNX-05 applies; the service closes with 1011 before answering every time → 60 s after the first drop, CNX-03 (today: 1011 retries every 0.5 s with no end) |
| CNX-09 | CNX-01 to CNX-08 hold the same in the text and the voice conversation. | src/app/triage/[triageId]/(internal)/components/conversational/hooks/use-conversation-session.ts::useConversationSession | frontend | Text conversation drops and the service closes before answering every time → it stops at 60 s, as in the voice conversation |

## Rows without ID
- docs/prd/conversation-connection/02-glossary.md: | Window | The 60 s, counted from the first drop, inside which the screen keeps trying to come back | `conversational/lib/timing.ts::RECONNECT_WINDOW_MS` |
- docs/prd/conversation-connection/04-end-to-end-journey.md: 2. The connection drops. The screen shows "Só um instante, estou voltando…", blocks the answer box and tries again, waiting longer each time (section 05, CNX-01).
- docs/prd/conversation-connection/04-end-to-end-journey.md: 4. Nothing answers for 60 s from the first drop: the screen shows "A conexão caiu e não voltou. Procure o balcão para continuar."; a reload resumes the conversation (CNX-03).
- docs/prd/conversation-connection/04-end-to-end-journey.md:   B -->|60 s from the first drop| D[A conexão caiu e não voltou. Procure o balcão]
- docs/prd/INDEX.md: | [05-drops-and-endings.md](conversation-connection/05-drops-and-endings.md) | Step 1 · Drops and endings of the conversation | CNX-01, CNX-03..09 | [triage](../trd/triage.md) |

## TRD
- docs/trd/triage.md "How it enters the flow", paragraph "Conversation drops and endings": names `lib/reconnect-policy.ts::nextReconnectStep` as "the 60 s window and the backoff" (a default value in the TRD; becomes "the window and the backoff"); the rule list at the top (CNX-01, CNX-03..09) gains CNX-10.
- docs/trd/triage.md "Where it lives": a row for the countdown module and its hook when they are created; `hooks/use-waited-ms.ts::useWaitedMs` is the closest pattern but ticks only at fixed steps (4, 8, 12 s).
- lib/timing.ts::RECONNECT_WINDOW_MS (60_000 today) is the one home of the window; read by lib/reconnect-policy.ts::nextReconnectStep and ::decideReconnect (callers: lib/session-connection.ts::startConversationConnection, retryInWindow).
- lib/session-connection.ts::startConversationConnection keeps the first-drop time (`droppedAt`) inside its closure and reports only `setStatus("reconnecting")`; nothing outside knows when the window ends. The countdown needs that end time to leave the connection (a new optional dep, like `onAnswered`), cleared on the first message (where `droppedAt` is reset) and on finish.
- At the window end `retryInWindow` waits the remaining time, then `finishFor("connectionLost")`: the count reaching 0 and the CNX-03 message coincide.
- The message is rendered by components/conversational-screen.tsx from `failureSurface(failureKindOf(...))` (kind `reconnecting`, copy `CONVERSATIONAL_COPY.errors.reconnecting`) inside components/failure-notice.tsx, which has `role="alert"` (screen readers read each text change).
- The count must be derived from the end time and the clock, not a decrement per tick: background tabs throttle timers.
- lib/failure-copy.ts::isPatientSafe rejects 3-digit 4xx/5xx numbers; a count of at most 90 cannot match.

## Invariants
- I-05 a give-up always surfaces a message; I-12 timeout, retry policy and failure state explicit, fakes in the unit suite; I-13 and I-23 the window-end log carries counters only (`logger.warn("conversation reconnect window ended", { attempts })`, unchanged); I-20 the new copy is pt-BR in `lib/copy.ts`.

## Principles
- Constitution I: the count carries no patient data; holds.
- Constitution II: the countdown copy lives in the one typed copy map (`CONVERSATIONAL_COPY`); holds.
- Constitution IV: proven with fake timers on the FakeSocket; no live clara-ai.

## Open questions linked
- Q4 (CNS-09) mentions "the 60 s of the farewell-text path": another timer, unchanged.

## Changes and tests
- Active change changes/003-conversation-reconnect (not archived): CNX-04, CNX-05, CNX-08 held planned waiting for clara-ai voice-resilience; its T02 owned lib/reconnect-policy.ts and lib/session-connection.ts. This change edits CNX-04's number only and keeps it planned. Change number of this one: changes/004-reconnect-window-90.
- Tests pinned to 60 s: lib/__tests__/session-connection.test.ts `ATTEMPT_TIMES` (last attempt 55_500) and the case "stops 60 s after the first drop" (with 90 s the attempts go on 63_500, 71_500, 79_500, 87_500, then the end at 90_000); lib/__tests__/reconnect-policy.test.ts reads RECONNECT_WINDOW_MS (follows the constant).
- Other tests citing the rules: lib/__tests__/failure-copy.test.ts (CNX-03), lib/__tests__/close-reason.test.ts ("reconnecting" surface), lib/ending/__tests__/failure-view.test.ts (reconnecting kind), lib/screen/__tests__/screen-machine.test.ts (reconectando).
- Base: `gates.sh setup` up to date; `gates.sh lint` (ESLint and tsc) green at 46b66879.
- K08 clara-ai: its resume window is the required deploy variable `CONVERSATION_SESSION_RESUME_WINDOW_SECONDS` (docs/prd/prd-2/21-configuracao.md, example 300), values not in the repository; past it the sweeper ends the session (`resume-window-expired`). It must stay above 90 s in every environment.

## Divergences
- in scope: none; CNX-01 and CNX-03 functional (lib/reconnect-policy.ts::nextReconnectStep, lib/session-connection.ts::startConversationConnection retryInWindow); CNX-01 Example still says "(today: one attempt every 0.5 s with no end)", stale wording since change 003 shipped, refreshed by the rewrite.
- out of scope: lib/screen/screen-label.ts::screenLabel shows "pode falar" (ORB_LABEL of the `listening` orb) in the reconectando state while the answer box is blocked (CNS-10)
- out of scope: lib/failure-copy.ts `recoverable` has no reader outside tests (already a Leave of change 003)
