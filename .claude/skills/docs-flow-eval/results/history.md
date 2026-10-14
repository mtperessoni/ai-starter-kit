# docs-flow-eval history

One row per run. Elapsed and active are agent minutes after the sheet answer; reader is the blind reader score out of 5. `-` = not measured in that round.

| Date | Scenario | Arm | Run | Dispatches | Elapsed min | Active min | Turns | Input tokens | Tool calls | Docs gate fails | Stale | Decision kept | INDEX current | Tests pass | Reader |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-14 | reconnect-window-90 | current-prd-flow | 1 | 4 | 17 | 16.1 | 113 | 7.96M | 209 | 1 | 1 | yes | yes | yes | 5 |
| 2026-10-14 | reconnect-window-90 | current-prd-flow | 2 | 7 | 20 | 17.4 | 105 | 6.33M | 202 | 3 | 1 | yes | yes | yes | 5 |
| 2026-10-14 | reconnect-window-90 | rule-as-data-v1 | 1 | 1 | 6 | 5.9 | 35 | 4.29M | 106 | 0 | 0 | no | no | yes | 4.5 |
| 2026-10-14 | reconnect-window-90 | rule-as-data-v1 | 2 | 1 | 5 | 5.1 | 33 | 3.98M | 97 | 0 | 1 | no | no | yes | 4.5 |
| 2026-10-14 | reconnect-window-90 (fixture b) | rule-as-data-v2 | 1 | 1 | 5.7 | 5.7 | 32 | 3.79M | 82 | 0 | 0 | yes | yes | yes | 5 |
| 2026-10-14 | reconnect-window-90 (fixture b) | rule-as-data-v2 | 2 | 1 | 5.7 | 5.7 | 35 | 4.03M | 92 | 0 | 0 | yes | yes | yes | 5 |
| 2026-10-14 | reconnect-window-90 (fixture b) | rule-as-data-v3 | 1 | 1 | 5.6 | 5.6 | 32 | 2.32M | 91 | 0 | 0 | yes | yes | yes | 5 |
| 2026-10-14 | reconnect-window-90 (fixture b) | rule-as-data-v3 | 2 | 1 | 7.0 | 7.0 | 44 | 3.23M | 109 | 0 | 0 | yes | yes | yes | 5 |

Fixture a (first four rows) and fixture b differ in the sheet decision (a: stop the attempt at zero; b: how a screen reader hears the count); costs compare, decision rows do not.
