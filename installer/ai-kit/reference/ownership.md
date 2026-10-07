# Ownership of installed files

Every file the kit installs is either **kit-owned** (the project never edits it; update replaces it) or **project-owned** (seeded once from a template, then the project's; update never replaces it, only proposes the kit's changes as a diff). The manifest records which.

| Path in the project | Owner | On install, if the file already exists | On update |
|---|---|---|---|
| `.claude/skills/prd-flow/` (except `repo.md`) | kit | Replace after showing the diff | Replace when unchanged since install; otherwise show a three-way diff and ask |
| `.claude/skills/prd-flow/repo.md` | project | Merge: keep existing values, add missing sections | Propose new sections only |
| `.claude/skills/prd-gate/` (legacy name) | kit, removed | Not installed | Removed by the prd-gate migration of `update.md`, after the user confirms |
| `.claude/skills/prd-flow/scripts/build_prd_html.py`, `docs/templates/prd.html` | kit | Replace | Replace when unchanged |
| `scripts/commit_trailers.py` | kit | Replace | Replace when unchanged |
| `.github/CODEOWNERS` | project | Fill from "Rule owners" of `repo.md`, or leave commented; an existing file only gets the `docs/prd/**` line added | Never touched; propose only |
| `docs/prd/prd.html` (when `html_mode` is `generated`) | kit output | Built by `build_prd_html.py`, never by hand | Rebuilt |
| `.claude/skills/prd-create/`, `trd-create/`, `adr/` | kit | Replace after showing the diff | Same as prd-flow |
| `scripts/gates.sh`, `ratchet.py`, `related_tests.py`, `new_failures.py`, `move_lines.py`, `kit_config.py`, `hotspots.py`, `contract_drift.py`, `docker_hygiene.py`, `clean_task_outputs.py`, `telemetry_hook.py`, `run_probe.py`, `retro.py` | kit | Ask (an existing `scripts/gates.sh` is renamed to `scripts/gates.project.sh`; the kit's `gates.sh` delegates to it, see the next row) | Replace when unchanged |
| `scripts/gates.project.sh` | project | The project's former `gates.sh`, renamed. Wired: the kit's `gates.sh` sends it every target the kit does not define and every target in `ai-kit.json` `commands.project_targets`, with the arguments. List there the targets the project keeps (for example `full`, `offline`, `divergence`) | Never touched |
| `docs/templates/` (includes `folder-CLAUDE.md`) | kit | Replace | Replace when unchanged |
| `docs/ai-readiness.md` | kit | Replace | Replace when unchanged |
| `.ignore` | project | Append the lines that are missing | Propose missing lines |
| `docs/code-structure.md` | project | Merge the AR table; keep project additions | Propose new rules only |
| `ai-kit.json` | project | Create | Add new keys with defaults; never change values |
| `CLAUDE.md`, `AGENTS.md` | project | Merge: keep every existing line, add the kit sections that are missing, resolve contradictions with the user | Propose new sections only |
| `.specify/memory/constitution.md` | project | Merge: existing principles stay, the kit's process principles are added and numbered after them; with spec-kit already initialized, run its versioning rule (MINOR bump) and keep the file at its path | Propose new kit principles only |
| `changes/`, `changes/archive/` | project | Create `changes/archive/` (with `.gitkeep`) when missing; a legacy `specs/` is never touched or moved | Never touched; only `changes/archive/` is created when missing |
| `docs/prd/`, `docs/trd/`, `docs/flow.md`, `docs/adr/` | project | Never overwrite; `docs/adr/README.md` created only when missing | Never touched |
| `.github/workflows/ci.yml`, `claude-review.yml` | project | When a CI file exists, add the kit's steps to it instead of a second workflow; other CI platforms get the same steps translated | Propose new steps only |
| `.gitattributes`, `.gitleaks.toml`, `.gitignore` | project | Append the kit lines that are missing | Propose missing lines |
| `.claude/settings.json` | project | Merge the kit's telemetry hooks (command `python scripts/telemetry_hook.py`, async, the 12 events of TM03) and its `permissions` `allow` entries, plus `deny` entries for the generated and vendored paths (CE22, IN11), into the existing file; every hook and permission the project already has stays, unchanged and in order; create the file when missing | Add missing kit hooks and permission entries only; never remove or reorder the project's own |
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
