# The conversation keeps trying to reconnect for 90 s instead of 60 s and shows the patient the seconds left

## What changes in the rules
| Rule | Today (literal) | Becomes | Kind |
|---|---|---|---|
| CNX-01 | "When the connection of the conversation drops for a reason that does not end it, the screen shows "Só um instante, estou voltando…", blocks the answer box and tries again after 0.5 s, doubling the wait up to 8 s. The 60 s window counts from the first drop and restarts only when the conversation service answers on the new connection; a connection that opens and closes again before that answer, or a wait for another open window of the same triage, restarts neither the window nor the wait." | The same rule with "The 90 s window counts from the first drop"; Example: "... attempts after 0.5, 1, 2, 4, 8, 8 s...; 90 s after the first drop the screen stops trying and shows the connection-lost message (today: it stops at 60 s)" | rewrites |
| CNX-10 | (none) | "While the screen is reconnecting (CNX-01), the message shows the whole seconds left until the window ends, counting down once a second: "Só um instante, estou voltando… 85 s". The count starts at 90 s on the first drop, starts again at 90 s only when the window restarts, and when it reaches 0 the connection-lost message of CNX-03 takes its place. Screen readers hear the message once when reconnecting starts, not each second." | adds |
| CNX-03 | Example: "Wi-Fi off for 2 minutes → after 60 s the message stays on screen; Wi-Fi back and page reloaded → the conversation resumes at the open question" | Example: "Wi-Fi off for 2 minutes → the count reaches 0 at 90 s and the message stays on screen; Wi-Fi back and page reloaded → the conversation resumes at the open question" (rule text unchanged) | rewrites |
| CNX-04 | "... the screen tries again as for any drop, inside the 60 s window of CNX-01; ..." and Example "... the service closes with 1011 before answering every time → 60 s after the first drop, CNX-03 ..." | "inside the 90 s window of CNX-01" and "→ 90 s after the first drop, CNX-03"; stays planned (held by change 003 until clara-ai ships) | rewrites |
| CNX-09 | Example: "Text conversation drops and the service closes before answering every time → it stops at 60 s, as in the voice conversation" | Example: "... → the count runs down and it stops at 90 s, as in the voice conversation" (rule text unchanged) | rewrites |
| Glossary · Window | "The 60 s, counted from the first drop, inside which the screen keeps trying to come back" | "The 90 s, counted from the first drop, inside which the screen keeps trying to come back and counts down the seconds left" | rewrites |
| Journey · steps 2 and 4 | "tries again, waiting longer each time (section 05, CNX-01)." and "Nothing answers for 60 s from the first drop" | step 2 adds "and shows the seconds left (CNX-10)"; step 4 and the diagram say 90 s | rewrites |

## What does not change
- The wait between attempts (0.5 s, doubling up to 8 s), the message of each end (CNX-03 to CNX-08) and the resend of the answer in flight (CNX-07).
- The 60 s maximum wait of the farewell text and the 30 s after the closing frame (CNS-09, Q4): other timers.
- The line under the circle while reconnecting: today it can read "pode falar" while the answer box is blocked; left as it is (say `scope:` to include it).
- Nothing changes in clara-ai or the backend.

## Assumed (holds unless you correct it)
- A1 The window is 90 s counted from the first drop, and while reconnecting the screen shows the countdown in seconds (decided in conversation).
- A2 The count sits inside the reconnecting message, at its place and size, in the format of the request ("Só um instante, estou voltando… 85 s"); whole seconds rounded up, from 90 s down to 1 s, then the connection-lost message.
- A3 One value for every unit and organization, fixed in the front: no per-unit setting and no switch.
- A4 A failure of Sara's service (CNX-04) uses the same 90 s and the same count; the text and the voice conversation behave the same (CNX-09).
- A5 Sara's service keeps a dropped conversation for more than 90 s: its resume window is a clara-ai deploy setting (example 300 s) not visible from this repository; whoever deploys confirms it is above 90 s in every environment.
- A6 Rollback is reverting the front deploy; a page open during the deploy keeps 60 s and no count until it reloads.
- A7 Proof: unit tests with fake timers (the end at 90 s, the count shown at a given second, the restart at 90 s); no live clara-ai needed.
- A8 Patient data: the count carries only a number of seconds; nothing new reaches logs or analytics.

## Decisions (answer by number)
**1. How a screen reader hears the countdown** · rule CNX-10
Today: the reconnecting message sits in a box that screen readers read aloud every time its text changes (`components/failure-notice.tsx`, role "alert"); a number that changes every second would be read every second.
Why it matters: a patient who uses a screen reader would hear up to 90 announcements in a row, over everything else on the screen.
- A) Read the message once when reconnecting starts, and the connection-lost message at the end; the number is only seen (Recommended): no stream of announcements; that patient does not hear how many seconds are left. No stated preference.
- B) Read the seconds left every 15 s (90, 75, 60...): that patient hears the time left; up to 6 announcements per drop.
- C) Read every second, as the screen changes: same as what is seen; up to 90 announcements per drop.
Example: the connection drops for 40 s, then (A) the screen reader says "Só um instante, estou voltando…" once and nothing more until the conversation resumes.

## How to answer
`ok` accepts every recommendation and assumption. Otherwise: `1B`, `A2: <correction>`, `scope: <correction>`. If a scenario is wrong, say its number.
