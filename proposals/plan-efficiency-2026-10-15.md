# Plan: cost per turn and number of turns, 2026-10-15

Evidence: `eval/audit-2026-10-15-paper/FINDINGS.md` (H01 to H11, paper P1 to P7). Approved by the owner on 2026-10-15: delivery 1, hooks allowed (new hook and guard hook), one PR per slice.

## Goal and out of scope

Goal: fewer tokens and less time per delivery by cutting the fixed preamble (H01), refused edits (H03), manual lint turns (H08), test failure streaks (H06) and fat main threads (H02).
Out of scope: product code, model choice, a prd-flow redesign beyond gate removal, the Optii and medzap repositories.

## Decisions

| ID | Decision | Why |
|---|---|---|
| D1 | Read with Read before Edit, never with the shell, is an always-loaded rule (global block), not a domain file row | H03: SA51 existed and was not loaded |
| D2 | Mechanics move into hooks where the harness allows it: lint after edit, the failure-streak cap, the context checkpoint | P6; H06 and H08 show text rules alone do not hold |
| D3 | The hooks advise through `additionalContext`; only the failure streak at 5 asks the agent to hand back, and nothing blocks the main thread | Safety nets change only with the owner's yes (CR22); given 2026-10-15 |
| D4 | The preamble gets a budget the doctor measures: template `AGENTS.md` plus `CLAUDE.md` plus the global block | H01; CE18 had no measurement |
| D5 | Every slice is measured with the probe (`eval/audit-2026-10-15-paper/probe.py`, fixed task, fixed ref) before and after | M07 |
| D6 | Lint after edit runs in a detached worker and its findings arrive on the agent's next Edit, Write or shell call | A synchronous lint of one file took about 30 s in agora-consulta-fe (type-aware ESLint); the deferred hook returns in about 160 ms |
| D7 | `prd-flow-surveyor` keeps opus; only `prd-flow-docs` moves to sonnet | The surveyor judges conflicts across every PRD, the one place CR09's reason holds; prd-flow runs only when typed |

## Slices

| # | Slice | Files (main) | Acceptance | Min |
|---|---|---|---|---|
| K0 | Baseline | `eval/audit-2026-10-15-paper/` | probe runs 3 times on ref f8eb0561 of agora-consulta-fe; FINDINGS and scripts committed | 40 |
| K1 | Read, edit and stop rules | `global/CLAUDE.md`, `kit/.claude/agents/*.md`, `rules/core.md`, `rules/02-subagents.md` | global block says read with Read, write whole files after a full Read, batch independent reads, done means stop; docs agent on sonnet (D7); tests that pin the text pass | 30 |
| K3 | Preamble diet | `kit/AGENTS.md`, `kit/CLAUDE.md`, `kit/scripts/preamble.py`, doctor | template text deduplicated against the global block and the constitution; `preamble.py` prints bytes and estimated tokens and warns over budget; test | 60 |
| U1 | Owner machine | `~/.claude/CLAUDE.md` block, memory index | global block reinstalled; done memories archived, not deleted | 20 |
| K2 | Post-tool hook | `kit/scripts/post_tool_hook.py`, `kit/.claude/settings.json`, `kit/ai-kit.json`, tests | lint of the edited file delivered on the next call (D6); failing test streak per agent advised at 3 and hand back at 5; one checkpoint reminder when the main context passes the budget; offline tests | 120 |
| K5 | After | probe results, FINDINGS | probe 3 runs with K1 to K3 overlaid; table before and after; verdict per M07 | 30 |

Later deliveries (not approved yet): R1 to R3 replicate to agora-consulta-fe, modulo-integrador and clara-ai; K4a and K4b remove the per-commit gates of `proposals/audit-rules-cost-2026-10-14.md` section 5.

## Metrics

| Metric | Source | Better |
|---|---|---|
| first-turn context | probe, transcripts | lower |
| turns, tokens, cost, wall time | probe | lower |
| refused edits ("has not been read yet") | probe, transcripts | 0 |
| shell reads, manual lint calls | probe | lower |
| longest failing test streak | probe, transcripts | at most 2 |
| task passes | probe `verify` | 3 of 3 |
