# writer-trd

Writes the TRD after the user confirmed the rule diff (C5 step 7; the TRD is never written before step 6), and in C4.

**C4 mode:** run only when files, entry points or tests moved (otherwise the C4 is one `writer-prd` call and this section is skipped). Input: the confirmed divergence in `state.md` and `writing.md`. Update the body of `docs/trd/<area>.md` and the area map for what moved (names only), no "Planned" section; steps 2 to 4 as below.

C5 input: `approved-rules.md`, `pack.md`, `writing.md`.

1. Read `reference/trd-planned.md` and write the "Planned" section of each feature in the pack (or the file of a new feature) in the table `| File | Changes or creates | Symbols | IDs |`: no parameters, intervals or values (they are rules or contracts), "Tests to write" is the table `| Test file | IDs |` (never expected values), and contracts are linked to `design.md`, not copied.
2. `<python> .claude/skills/prd-flow/scripts/gate.py --step trd` (the default checks and G23 to G26 in one run). ERROR: fix and run again. A file over the TRD budget splits (trd-planned.md "Size and split").
3. Commit `docs(trd): <sentence>`.
4. Append to `writing.md` the TRD files, the commit and the gate output.

Return: commit, TRD files touched, the last gate line, gaps.
