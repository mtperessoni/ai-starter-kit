# doctor

Read-only. Reports, in at most 25 lines, what drifted from the kit and from its own rules. Never edits.

| Check | How |
|---|---|
| Kit version | Manifest version versus the kit's HEAD; number of commits behind |
| Kit-owned files edited locally | Hash versus manifest |
| Placeholders left | `Grep "<[a-z][^>]*>\|\{\{"` outside `docs/templates/` and code |
| Commands still work | Run `scripts/gates.sh lint`, `ratchet`, `imports` and `related` on one file |
| Docs gate | `python .claude/skills/prd-gate/scripts/gate.py`: errors and earlier drift |
| PRD and TRD coverage | Every feature folder has a TRD file and a `CLAUDE.md` of at most 20 lines; every INDEX row with IDs has a TRD |
| Ratchet trend | Allowlist sizes versus the manifest's install snapshot (`long_modules`, `no_prd_id`, ...) |
| Stale spec-kit references | `Grep "speckit" ` in `.specify/memory/constitution.md` and `AGENTS.md`; a hit while `repo.md` "Spec-kit" is `none` is drift, fixed by `/ai-kit update` |
| Change folders | `changes/archive/` exists; no stale folder in `changes/` outside `archive/` on the base branch (`gate.py --final`) |
| State folder | `.claude/prd-gate/` ignored by git |
| Container hygiene | A `Dockerfile` or compose file without the `docker` section in `ai-kit.json`, or a compose service, volume or network without the repo label, is drift. Run `scripts/gates.sh guard` (read-only) and report its refusals, the Docker disk file warning and the unlabelled images it lists |
| Telemetry hooks | `.claude/settings.json` registers `scripts/telemetry_hook.py` for the 12 events of TM03; `.ai-kit/runs/` is git-ignored; the `telemetry` section exists in `ai-kit.json` |
| Last run's coverage | In `.ai-kit/runs/<latest>/retro.md` (or `summary.json`): the Coverage line; a low share of calls with a duration or no probes means the hook or `run_probe.py` is not wired |
| Last retro findings | Count and titles of the Findings section of that `retro.md`; none is reported as within every threshold |
| Global block | `~/.claude/CLAUDE.md` contains the kit block (between the `ai-kit` markers) |

End with the fixes, each as the command or skill that applies it (`/ai-kit update`, `/trd-create` mode N2, `/prd-gate`).
