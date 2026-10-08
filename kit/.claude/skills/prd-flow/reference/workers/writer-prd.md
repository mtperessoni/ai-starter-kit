# writer-prd

Applies the approved rules to the PRD. Step 5 of the C5 route, E10 of the short C5, and C4. Input (C5): `approved-rules.md`, `interview.md`, `pack.md`, `state.md`, `changes/NNN-<slug>/decisions.md`. You never touch the TRD.

**C4 mode** (stale PRD): input is the confirmed F2 divergence in `state.md` (rule ID, PRD text, what the code does, Source); there is no `interview.md`, `approved-rules.md` or `decisions.md`. Skip step 1 and the `decisions.md` parts: edit the row in place per `reference/prd-writing.md`, old text literally to the CHANGELOG, INDEX if affected, then steps 3, 4 (`gate.py --step prd` without `--rules`), 5 (no `decisions.md` in the commit) and 6.

**New PRD variant** (classification.md): also read `pack.md`. Write only approved rows after the interview, never `*(proposed)*`; lay out the new PRD folder, INDEX row and README overview per `.claude/skills/prd-create/reference/anatomy.md` (M4).

1. `<python> .claude/skills/prd-flow/scripts/gate.py --rules .claude/prd-flow/state/<slug>/approved-rules.md` (it reads `interview.md` beside it; Q3, G27 and the other errors). ERROR: stop and return it as a gap. Never edit `approved-rules.md` or `interview.md`: they are the user's decisions and belong to this conversation. Copy each approved row into the PRD as it is (marker, Source, Example included), never retyped.
2. Read `reference/prd-writing.md` and follow it: markdown of the owning section, markers, `Example` column when the approved row carries it, CHANGELOG (with the `Decisions:` block from `decisions.md`, and `decided by <owner>, written by <approver>` when `decisions.md` records an owner), INDEX, README if affected. In the short C5, apply only the dated section of `approved-rules.md`.
3. HTML: with `html_mode: generated` (`repo.md`) run `<python> .claude/skills/prd-flow/scripts/build_prd_html.py` and never edit the HTML; with `hand`, only `Grep -n` of the ID and an exact `Edit` of the line.
4. One run checks everything this step needs: `<python> .claude/skills/prd-flow/scripts/gate.py --step prd --rules .claude/prd-flow/state/<slug>/approved-rules.md --applied` (the default checks, Q2, Q3, Q4 and G28 for the "Shared PRDs" of `repo.md`). ERROR: fix the PRD, never the approved file, and run it again. A WARNING about "earlier drift" is not yours.
5. Commit `docs(prd): <sentence in the git log style>` with markdown, the generated or edited HTML and `decisions.md` together.
6. Write `writing.md`: files touched, IDs, commit, the last gate line.

Return: commit, IDs touched, the last gate line (it covers `--applied` and `--sibling`), non-table changes (amendment sections, INDEX, README, new folder; at most 5 lines, so step 6 shows them without reopening files), gaps.
