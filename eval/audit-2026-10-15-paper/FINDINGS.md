# Harness audit against "An Empirical Study of Harness Design for Coding Agents", 2026-10-15

Scope: the 29 Claude Code sessions of 2026-10-13 to 2026-10-15 under `~/.claude/projects/c--Projects-agora-consulta-fe` (work on agora-consulta-fe, clara-ai, modulo-integrador and the kit): 263 subagents, about 12,000 turns, 2.19B tokens processed (context plus output, summed per turn). The core rules (CR01 to CR22) landed on 2026-10-14 evening and no delivery ran after them, so these numbers describe the pattern they target. Earlier evidence: `../audit-2026-10-14-session-slowness/FINDINGS.md`. Scripts: `scripts/`. Paper: arXiv 2609.20804 (Fan et al., Sep 2026; Nemotron-3 30B/120B/550B and Mistral-Medium-3.5 on SWE-Bench Verified and Terminal-Bench 2.1, 176 settings).

## What the paper found

| ID | Finding | Number |
|---|---|---|
| P1 | Context management pays only when the window binds; its benefit is avoiding overflow, it does not change agent behavior | managed minus unmanaged: +35.7 pp at 32k, +2.7 pp at 128k |
| P2 | Cheap rule-based elision of stale tool output before LLM summarization (soft 60%, hard 85% of the window) is the cheapest policy at equal accuracy | lowest cost in 7 of 8 panels |
| P3 | Lossless recall of elided content is almost never used and adds no accuracy | 56% of settings never called it; -0.36 pp |
| P4 | A live plan (one item in progress, injected each turn, kept out of history) is an accuracy scaffold for weak models and a cost saver for strong ones, by trimming post-edit verification | strong models: -30% cost, -0.4 to -2 pp |
| P5 | Predefined fine-grained tools help weak models; strong models are cheaper with composite actions and coarser edits | 550B bash-only: +3.6 pp, -53% cost, -32% calls; re-patches 4.6 to 1.5 |
| P6 | Fixed harness substrate: post-edit lint appended to the edit result, stuck detection (reminder at 5 identical calls, stop at 8 failing), tool output truncated at 24k chars, up to 8 parallel read-only calls, errors returned as observations | design |
| P7 | Harness design is conditional: pick each component for the model, task and budget, never as a default | conclusion |

## What the sessions show

| ID | Finding | Evidence | Paper |
|---|---|---|---|
| H01 | The fixed preamble is a third of all tokens | first turn: main 83k, subagent 55k (CE18 measured 76k and 41k); 2,864 main and 8,882 subagent turns, so about 727M of 2.19B tokens are the preamble resent | P6, P7 |
| H02 | The main thread is 43% of tokens and serial | orchestrators at median context 216k to 667k, about 1.0 to 1.2 calls per turn; 33d0c972 alone: 451 turns at 579k median, 237M | P1, P2 |
| H03 | Edits refused for reading through the shell | 409 "File has not been read yet" (390 in subagents); 362 of 390 (93%) followed a `cat`, `sed` or `grep` of that file; the auto-mode note invites shell reads and SA51 is not in the always-loaded text | P6 (the read state is recorded only by the read tool) |
| H04 | Fine-grained edits | 2,235 product edits over 543 files, 4.1 per file per session; 48 files edited 10 or more times, max 70 (`use-reply-audio.ts`) | P5 |
| H05 | Subagents spend half their calls locating | 13,684 calls of the 7 big sessions: locate 52%, product edit 16%, test edit 9%, test runs 7%, docs 6%, process and gates 4%; 12 to 35 calls before the first product edit | P5 |
| H06 | Test failure streaks run past the SA30 cap | max streak 4 to 6 in five sessions; SA30 (2 reruns) is text only | P6 |
| H07 | No identical-call spinning | max identical streak 1 everywhere | P6 (already met) |
| H08 | Lint is a manual call | WF80 asks for `fix-files` and `lint-files`; no `PostToolUse` lint hook | P6 |
| H09 | No live plan | 0 TodoWrite calls in 13,684 (the tool is absent from this harness); 10 to 18% of executor calls come after the last product edit | P4 |
| H10 | Opus by default in two places | `Explore` without `model` ran on Opus (5f8098eb: 100%); `prd-flow-surveyor` and `prd-flow-docs` frontmatter | P7 |
| H11 | A dead hook runs on every prompt | FE `UserPromptSubmit` calls `C:\AgoraConsulta-2\meta-docs\...\session-start.sh`, which does not exist | P6 |

## Already aligned with the paper

| Practice | Rule | Paper |
|---|---|---|
| No recall machinery, one record set | CE11, DS12, rule as data | P3 |
| Short plan only for size L | CR04 | P4 |
| Sonnet by default per dispatch | CR09 | P7 |
| Bounded output to files | CE26, CR17 | P6 |
| Fewer cold agents | CR07 | P5 |
| No identical-call loops | SA30, guard hook | P6 |

## Plan

`proposals/plan-efficiency-2026-10-15.md`.
