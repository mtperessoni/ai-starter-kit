# Workflow (WF)

Every change to product behavior follows **PRD, then TRD, then plan, then code**. Starting from the code reproduces the defect and loses the decision. The `prd-gate` skill runs this workflow; these are its rules in catalog form.

## Gate and cases

| ID | Rule | Why | Lands in |
|---|---|---|---|
| WF01 | Every change and every question about product behavior starts with `/prd-gate`. Skip only for small changes (typo, log line, rename, one-line fix that changes no rule), test fixes, CI, dependency bumps and formatting | One entry point loads the right context every time | CLAUDE.md "Product rules gate" |
| WF02 | Classify each request into one case, one line; a request with several items gets one case per item | Each case has a different cost and route | skill SKILL.md "Cases" |
| WF03 | Cases: **C0 no PRD** (hand over to `/prd-create` and `/trd-create`), **C1 query**, **C2 implement** an approved rule the code does not meet, **C3 bug** (code diverges, PRD confirmed right), **C4 stale PRD** (code right, PRD wrong, confirmed), **C5 rule change** (changed, new, gap, or defect the PRD documents as current behavior), **C6 refactor** (structure changes, behavior does not) | Named cases make routing deterministic | classification.md |
| WF04 | "Diagnose", "understand why", "plan" are C1 until the user asks for a change: show cause and options and wait | Diagnosis requested is only diagnosis | classification.md; R01 |
| WF05 | Fixing a defect that the PRD documents as current behavior is a rule change (C5), not a bug | The PRD said it does that; changing it is a decision | classification.md |
| WF06 | A request with no matching rule is a gap: C5, and the new rule enters the PRD before the code | Behavior without a written rule is an undocumented decision | classification.md |
| WF07 | A refactor that turns out to need a changed limit, text or order escalates from C6 to C5 | It stopped being structure only | classification.md |
| WF08 | Nothing is written in `docs/`, `src/` or `tests/` before its time: C5 from step 5 on; C2, C3, C4 and C6 after the user confirms the case | The user sees the current rule before anything moves | R01 |
| WF09 | Code and PRD answer facts; the user answers intent | Never ask what the code already says; never infer what the user wants | R02 |

## Rule change (C5)

| ID | Rule | Why | Lands in |
|---|---|---|---|
| WF10 | Before any interview, show the confrontation: current rule (literal), proposal, what changes for each actor, impact (related rules, variants, tenants, tests, specs, open questions), trade-offs and risks. Then ask: "This is the change I want", "Do not touch this rule" (back to C2 or C3), "Adjust the request" | The user decides with the impact on the table | impact.md; SKILL.md step 3 |
| WF11 | The impact sweep always covers the consumer contract in sibling repositories, safety nets removed or weakened, and the prerequisites to verify the rule (real model, database, backend) | Discovered late, each becomes an extra round with the user | impact.md K08 to K10 |
| WF12 | Removing or weakening a safety net (a guard, a list, a fallback, a switch, a wait) is a trade-off in the confrontation and a question in the interview, never an extra task during execution | Protections vanish quietly otherwise | impact.md K09; RV06 |
| WF13 | Protected rules (constitution principles, invariants backed by structural tests, registered exceptions) change only through an ADR or a constitution amendment, after explicit confirmation; ask whether the protection still holds, since the doc may be stale | Deliberate change of protections | impact.md "Protected rules" |
| WF14 | The interview asks only dimensions the pre-interview left open; answered dimensions are stated as facts in the read-back | Rounds are the most expensive part of the route | interview.md |
| WF15 | Questions: at most 4 per round in one AskUserQuestion; product language with a conversation or usage example and the effect on the user; a concrete scenario; options with the trade-off in the description, recommended first and marked "(Recommended)"; no rule IDs, symbol names or internal jargon in the question (IDs only in the read-back) | Users answer scenarios, not identifiers | interview.md; R07 |
| WF16 | Interview exit: every dimension answered or "not applicable" with a reason; every row complete (ID, text, Source `planned`, Change via); no contradiction with a live rule, superseded ones listed; every trade-off decided; a final read-back and an explicit "it is clear" from the user | A rule with an open dimension does not enter the PRD; it becomes an open question with the adopted default | interview.md |
| WF17 | The approver is `git config user.name`, recorded in `state.md` and the CHANGELOG entry | Traceability of who decided | SKILL.md step 1 |
| WF18 | After the writer commits, show the user only `git diff -U0` of the rule lines for confirmation | Cheap, exact review of what changed | SKILL.md step 6 |
| WF19 | The plan is approved by the user as a table (ID, result, owns, depends on, model, reviewer) before any execution | Execution is the expensive part | agent-plan.md "Presentation" |
| WF20 | Mid-execution rule change (short C5): stop the tasks that touch the rule; show current rule and proposal in at most 15 lines in product language; when approved, append a dated section to `approved-rules.md` and dispatch the writer for that section only; the planner only appends new tasks; the review counter does not reset without explicit approval | No hand edits of the PRD during execution | execution.md E08 to E10 |

## Commits, resumption, reporting

| ID | Rule | Why | Lands in |
|---|---|---|---|
| WF21 | Commit order: `docs(prd): ...` (PRD and HTML together), `docs(trd): ...`, `docs(changes): ...` (the plan), then one code commit per task. Conventional Commits, English, IDs in the message. No push and no PR without an explicit request | Docs land before code; history reads as the workflow | R03; WS |
| WF22 | When the branch is behind the base: `git diff --stat HEAD..origin/<base> -- <paths read>`; pull only if it touches the scope | Avoid needless merges mid-task | SKILL.md light route step 4 |
| WF23 | Resumption: `/prd-gate resume <slug>` reads only `state.md` and the current phase file; the pack is still valid when `git diff --quiet <base> origin/<base> -- <pack paths>` holds | Resuming costs one small file, not a replay | SKILL.md "State" |
| WF24 | Explaining what the system did in a real session: ask for its id and read the recorded evidence before concluding; without it, list the code paths that could explain it and which evidence would separate them | No confident guesses about production behavior | classification.md |
| WF25 | Final report: case, IDs touched, commits, plan path, out-of-scope divergences | The user sees outcome and debt in one place | SKILL.md "Final" |
| WF26 | Where the plan lives: `changes/NNN-<slug>/plan.md` with the next free number (S: only when the change has tasks), or only a publish or deploy task when the change is config or env. Workflow state stays in `.claude/prd-gate/state/<slug>/` | The plan sits in one folder with the intent of its change; the legacy spec amendment path no longer exists | agent-plan.md; AGENTS.md "Directory map" |

## Change folders and living truth

| ID | Rule | Why | Lands in |
|---|---|---|---|
| WF27 | Size is decided at classification and stated in the case line. **S**: C1, C2, C3, C4, C6, no folder or only `plan.md`. **M**: C5 with an evident design (no new data model, contract, external dependency or open technical unknown): `brief.md` and `plan.md`. **L**: C5 with a new data model, contract, external integration, technical unknown or feature area: `brief.md`, `design.md` and `plan.md` | The paperwork matches the risk | classification.md; AGENTS.md "Workflow"; constitution Development Workflow 2 |
| WF28 | The plan header carries `## Constitution check`: one row per principle the change touches (principle, how the plan honors it, or the justified violation). A violation is justified there, not in a separate table | One place to see which principles the change touches | agent-plan.md; constitution Governance |
| WF29 | The mandatory final task "Promote" moves what is durable to its living home (PRD, TRD, ADR, real schema or contract) and archives the folder with `git mv changes/NNN-<slug> changes/archive/NNN-<slug>` | A change folder holds intent, plan and state, never truth; archived, it cannot pass for current behavior | agent-plan.md; AGENTS.md "Workflow" |
| WF30 | Order of authority: constitution, then PRD (behavior), then TRD (structure), then code. An active plan governs only the order of work. Nothing under `changes/archive/` or a legacy `specs/` is read to learn current behavior | An old plan must not read as authority | AGENTS.md; CLAUDE.md |
| WF31 | `gate.py --trace`: every PRD rule whose Source is not `planned` is cited by a test file; untested rules are reported against the shrink-only `allowlist.untested_rules` (new untested rule: error; listed: warning; listed but now tested: error asking to remove it); the file named in Source exists | A rule without a proof is a claim | gate.py; ai-kit.json |
| WF32 | `gate.py --change <dir>`: every ID in `brief.md` exists in the PRD; every ID of a P1 slice is in the Contract of a task of `plan.md`; `brief.md` holds no rule row; `design.md` without size L is a warning | Behavior is written once, in the PRD; the brief only cites it | gate.py |
| WF33 | `gate.py --final`: no PRD row with Source `planned` or the pending marker, no `## Planned` section in `docs/trd/`, no folder in `changes/` outside `archive/`; CI runs it on pushes to the base branch | Nothing half-promoted reaches the base branch | gate.py; ci.yml |
| WF34 | A repository with a legacy `specs/` keeps it untouched as history; new changes go to `changes/`. When spec-kit is kept (`repo.md` "Spec-kit": `kept`), `spec.md` cites PRD rule IDs and defines no FR of its own, and `tasks.md` is not used: the prd-gate plan is | Two homes for the same behavior drift apart | repo.md; install.md |
