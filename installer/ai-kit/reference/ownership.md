# Ownership of installed files

Every file the kit installs is either **kit-owned** (the project never edits it; update replaces it) or **project-owned** (seeded once from a template, then the project's; update never replaces it, only proposes the kit's changes as a diff). The manifest records which.

| Path in the project | Owner | On install, if the file already exists | On update |
|---|---|---|---|
| `.claude/skills/prd-flow/` (except `repo.md`) | kit | Replace after showing the diff | Replace when unchanged since install; otherwise show a three-way diff and ask |
| `.claude/skills/prd-flow/repo.md` | project | Merge: keep existing values, add missing sections | Propose new sections only |
| `.claude/skills/prd-gate/` (legacy name) | kit, removed | Not installed | Removed by the prd-gate migration of `update.md`, after the user confirms |
| `.claude/skills/prd-flow/scripts/build_prd_html.py`, `build_trd_html.py`, `promote.py`, `docs/templates/prd.html` | kit | Replace | Replace when unchanged |
| `.claude/skills/prd-flow/repo.md` keys `prd_section_budget_lines`, `trd_html` | project | Written with their defaults (200, `docs/trd/trd.html`) | Added with their defaults; never changes a value |
| `.claude/agents/prd-flow-surveyor.md`, `prd-flow-docs.md`, `prd-flow-executor.md`, `prd-flow-reviewer.md`, `prd-flow-recheck.md` | kit | Copied to `.claude/agents/`; a project agent with the same name is shown as a diff and never overwritten silently | Replace when unchanged; otherwise three-way diff and ask |
| `.claude/prd-flow/state/<slug>/deliveries/<task>.md` | agent output | Never installed; written by the executors, one file per task, in the git-ignored state folder | Never touched |
| `.claude/skills/prd-flow/reference/workers/` | kit, removed | Not installed | Removed by the workers migration of `update.md`, after the user confirms |
| `scripts/commit_trailers.py` | kit | Replace | Replace when unchanged |
| `.github/CODEOWNERS` | project | Fill from "Rule owners" of `repo.md`, or leave commented; an existing file only gets the `docs/prd/**` line added | Never touched; propose only |
| `docs/prd/prd.html`, `docs/trd/trd.html` (when `html_mode` is `generated`) | kit output | Built only by `/docs-html`, never by hand nor by the update | Never touched; `/docs-html` offered after the update |
| `.claude/skills/prd-create/`, `trd-create/`, `adr/`, `docs-html/` | kit | Replace after showing the diff | Same as prd-flow |
| `scripts/gates.sh`, `ratchet.py`, `related_tests.py`, `new_failures.py`, `move_lines.py`, `kit_config.py`, `hotspots.py`, `contract_drift.py`, `docker_hygiene.py`, `clean_task_outputs.py`, `telemetry_hook.py`, `run_probe.py`, `retro.py`, `retro_detectors.py`, `close_gate.py`, `baseline.py`, `config_get.py` | kit | Ask (an existing `scripts/gates.sh` is renamed to `scripts/gates.project.sh`; the kit's `gates.sh` delegates to it, see the next row) | Replace when unchanged |
| `scripts/gates.project.sh` | project | The project's former `gates.sh`, renamed. Wired: the kit's `gates.sh` sends it every target the kit does not define and every target in `ai-kit.json` `commands.project_targets`, with the arguments. List there the targets the project keeps (for example `full`, `offline`, `divergence`) | Never touched |
| `docs/templates/` (includes `folder-CLAUDE.md`) | kit | Replace | Replace when unchanged |
| `docs/ai-readiness.md` | kit | Replace | Replace when unchanged |
| `.ignore` | project | Append the lines that are missing | Propose missing lines |
| `docs/code-structure.md` | project | Merge the AR table; keep project additions | Propose new rules only |
| `ai-kit.json` | project | Create (includes `limits.skill_md_bytes` 6144 and `allowlist.skill_md_bytes`) | Add new keys with defaults; never change values |
| `CLAUDE.md`, `AGENTS.md` | project | Merge: keep every existing line, add the kit sections that are missing, resolve contradictions with the user | Propose new sections only |
| `.specify/memory/constitution.md` | project | Merge: existing principles stay, the kit's process principles are added and numbered after them; with spec-kit already initialized, run its versioning rule (MINOR bump) and keep the file at its path | Propose new kit principles only |
| `changes/`, `changes/archive/` | project | Create `changes/archive/` (with `.gitkeep`) when missing; a legacy `specs/` is never touched or moved | Never touched; only `changes/archive/` is created when missing |
| `docs/prd/`, `docs/trd/`, `docs/flow.md`, `docs/adr/` | project | Never overwrite; `docs/adr/README.md` created only when missing | Never touched |
| `.github/workflows/ci.yml`, `claude-review.yml` | project | When a CI file exists, add the kit's steps to it instead of a second workflow; other CI platforms get the same steps translated | Propose new steps only |
| `.gitattributes`, `.gitleaks.toml`, `.gitignore` | project | Append the kit lines that are missing | Propose missing lines |
| `.claude/settings.json` | project | Merge the kit's hooks and its `permissions` `allow` entries: the telemetry hooks (async, the 12 events of TM03), each a launcher command copied from `kit/.claude/settings.json` that resolves `${CLAUDE_PROJECT_DIR:-.}/scripts/telemetry_hook.py` with the interpreter of `commands.python` when set, else `python` or `python3`, and exits 0 when the interpreter or the script is missing (never the bare `python scripts/telemetry_hook.py`, which breaks from another cwd). Add the `allow` entries and `deny` entries for the generated and vendored paths (CE22, IN11), into the existing file; every hook and permission the project already has stays, unchanged and in order; create the file when missing | Add missing kit hooks and permission entries only (a project hook that still runs `python scripts/telemetry_hook.py` is replaced by the launcher, shown as a diff); never remove or reorder the project's own; remove a guard hook entry (`agent_guard_hook.py`) the kit registered earlier |
| `.ai-kit/runs/` | project | Never created by install (the hook creates it); its `.gitignore` line is appended | Never touched |
| `.ai-kit/manifest.json` | kit | Create | Rewrite |

## Manifest
`.ai-kit/manifest.json`, committed:
```json
{
  "kit": {"repo": "https://github.com/mtperessoni/ai-starter-kit", "version": "<short commit>", "installed": "YYYY-MM-DD", "updated": "YYYY-MM-DD"},
  "stack": {"recipes": ["python"], "package_manager": "uv", "test_runner": "pytest", "ci": "github"},
  "files": {"<path>": {"owner": "kit|project", "sha256": "<hash of the content as written>"}}
}
```
The hash of a kit-owned file tells update whether the project changed it since install.
