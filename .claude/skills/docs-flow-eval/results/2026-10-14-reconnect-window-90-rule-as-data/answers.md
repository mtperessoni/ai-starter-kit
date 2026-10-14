# Blind reader grades

Aliases (ledger only): W1 = cur-4, W2 = cur-3. cur-1 and cur-2 were not read (their stale CNX-01 row was fixed in the contract and rerun).

| Reader | Q1 | Q2 | Q3 | Q4 | Q5 | Total | Note |
|---|---|---|---|---|---|---|---|
| W2 (cur-3) | 1 | 1 | 1 | 1 | 1 | 5 | Found `Decided: 1A ... (rejected: ...)` in the commit body |
| W1 (cur-4) | 1 | 1 | 0.5 | 1 | 1 | 4.5 | Read the frozen-in-effect CHANGELOG, found the old 60 s entry only, never opened the commit body: "no rejected alternative is recorded". The record was there (`gate.py --history CNX-10` prints it) |
| W1 rerun (cur-4 plus the frozen CHANGELOG note, ef0efe7a) | 1 | 1 | 1 | 1 | 1 | 5 | Fresh reader; found 1A and both rejected options in the commit body |
