# doctor

Read-only. Reports, in at most 25 lines, what drifted from the kit and from its own rules. Never edits.

| Check | How |
|---|---|
| Kit version | Manifest version versus the kit's HEAD; number of commits behind |
| Kit-owned files edited locally | Hash versus manifest |
| Placeholders left | `Grep "<[a-z][^>]*>\|\{\{"` outside `docs/templates/` and code |
| Commands still work | Run `scripts/gates.sh lint`, `ratchet`, `imports` and `related` on one file |
| Docs gate | `python .claude/skills/prd-flow/scripts/gate.py`: errors and earlier drift |
| PRD and TRD coverage | Every area (feature folders plus `ai-kit.json` `areas`) has a TRD file; every map folder (feature folders plus `map_dirs`) has a `CLAUDE.md` of at most 20 lines; every INDEX row with IDs has a TRD |
| Readiness per area (IN13) | Against `docs/ai-readiness.md`: map present and short, TRD present, files and tests over limits, crowded folders, missing IDs, generated files without marker, related-run time versus `tests.related_budget_seconds`, top hotspots (`scripts/gates.sh hotspots`) |
| Noise and settings | `.ignore` and `.claude/settings.json` exist and cover `generated_patterns` and `ignore` (CE22) |
| Ratchet trend | Allowlist sizes versus the manifest's install snapshot (`long_modules`, `no_prd_id`, `crowded_dirs`, `generated_without_marker`, ...) |
| Stale spec-kit references | `Grep "speckit" ` in `.specify/memory/constitution.md` and `AGENTS.md`; a hit while `repo.md` "Spec-kit" is `none` is drift, fixed by `/ai-kit update` |
| Change folders | `changes/archive/` exists; no stale folder in `changes/` outside `archive/` on the base branch (`gate.py --final`) |
| State folder | `.claude/prd-flow/` ignored by git |
| Container hygiene | A `Dockerfile` or compose file without the `docker` section in `ai-kit.json`, or a compose service, volume or network without the repo label, is drift. Run `scripts/gates.sh guard` (read-only) and report its refusals, the Docker disk file warning and the unlabelled images it lists |
| Telemetry hooks | `.claude/settings.json` registers `scripts/telemetry_hook.py` (through the launcher command of the kit, never the bare `python scripts/telemetry_hook.py`) for the 12 events of TM03, and no guard hook (`agent_guard_hook.py`) remains (drift: remove it); `tests.failure_regex` captures a real failure line (IN17); `rg` is on PATH (IN18); `.ai-kit/runs/` is git-ignored; the `telemetry` section exists in `ai-kit.json` |
| Last run's coverage | In `.ai-kit/runs/<latest>/retro.md` (or `summary.json`): the Coverage line; a low share of calls with a duration or no probes means the hook or `run_probe.py` is not wired |
| Last retro findings | Count and titles of the Findings section of that `retro.md`; none is reported as within every threshold |
| Leftover prd-gate | `.claude/skills/prd-gate/` or `.claude/prd-gate/` exists, or `Grep "prd-gate"` hits CLAUDE.md, AGENTS.md, the constitution, settings, `ai-kit.json` or `docs/`: drift, fixed by `/ai-kit update` |
| Hand HTML under generated | `repo.md` `html_mode` is `generated` and `build_prd_html.py --check` fails: the HTML was edited by hand, rebuild it instead |
| Commit trailers | `scripts/gates.sh trailers` on the last 20 commits; missing `Rules:` or `Case: none` is drift |
| prd-flow agents | `.claude/agents/prd-flow-surveyor.md`, `-docs`, `-executor`, `-reviewer` and `-recheck` all exist; a missing one is drift, fixed by `/ai-kit update` |
| Leftover workers | `.claude/skills/prd-flow/reference/workers/` exists: drift, fixed by `/ai-kit update` |
| SKILL.md sizes | Every `.claude/skills/*/SKILL.md` is within `ai-kit.json` `limits.skill_md_bytes` or listed in `allowlist.skill_md_bytes` (`scripts/gates.sh ratchet`) |
| Global block | `~/.claude/CLAUDE.md` contains the kit block (between the `ai-kit` markers) |

End with the fixes, each as the command or skill that applies it (`/ai-kit update`, `/trd-create` mode N2, `/prd-flow`).
