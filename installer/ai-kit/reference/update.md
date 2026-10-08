# update

Brings kit improvements into a project that already has the kit, without overwriting what the project made its own.

## Steps
| Step | Does |
|---|---|
| U1 | K01 and K02. Read `.ai-kit/manifest.json`; `old` = its kit version, `new` = the kit's HEAD. Nothing to do when equal |
| U2 | `git -C <kit> diff --stat <old>..<new> -- kit/` and `git -C <kit> log --oneline <old>..<new>`: what changed and why |
| U3 | For each kit-owned file changed in the kit: hash the project's copy. Equal to the manifest hash → replace with the new version. Different → the project edited it: build a three-way view (kit old via `git -C <kit> show <old>:kit/<path>`, kit new, project) and propose a merge |
| U4 | For each project-owned file whose template changed in the kit: show only the new sections, keys or rules and propose adding them; never replace values |
| U5 | New kit files: add them (kit-owned) or propose them (project-owned). Files removed from the kit: ask before deleting the project's copy |
| U6 | New keys in `ai-kit.json` get their defaults; after adding them, run `python scripts/ratchet.py --init` and merge only the new allowlist keys (`crowded_dirs`, `generated_without_marker`) into `allowlist`, so the ratchet stays green right after the update; new linter rules from an updated recipe are proposed with a baseline. Layout keys (`layout`, `areas`, `map_dirs`, `generated_patterns`, `contracts`) and the seeds `.ignore` and `.claude/settings.json` are proposed from the detection of install I3 and I8, never applied silently |
| U6a | `repo.md` Gate config: add the keys the kit introduced since `old` (`language`, `planned_heading`, `via_header`) filled from the project's existing docs as in install, never from the defaults when the docs say otherwise |
| U6b | Read `CHANGELOG.md` of the kit: for each entry between `old` and `new`, in order, execute its `On update:` line (create folders, add `ai-kit.json` keys, seed allowlists, propose new sections) and list each in the plan table of U7 |
| U6c | Telemetry: copy `telemetry_hook.py`, `run_probe.py` and `retro.py` (kit-owned, U3 rules); merge the kit's hooks into `.claude/settings.json` keeping the project's own; add the `telemetry` section and the `.ai-kit/runs/` gitignore line; run the hook once on the sample payload of `install.md`. `.ai-kit/runs/` is never touched |
| U6d | Migration from `prd-gate`, when `.claude/skills/prd-gate/` exists. List first, then ask; apply only after yes. See the table below |
| U6e | Migration from the prd-flow workers, when `.claude/skills/prd-flow/reference/workers/` exists. List first, then ask; apply only after yes. See the second table below |
| U7 | Plan table (K03): replace, merge, propose, skip; wait for yes |
| U8 | Apply, run the Verify list of `install.md`, update the manifest (version, date, hashes) |
| U9 | Commit `chore: update ai-starter-kit to <new>` with the kit log lines in the body; report |

## Migration from prd-gate
Shows this list, asks, and never overwrites a project-owned file blindly: when the target exists, show a diff and ask.

| Change | How |
|---|---|
| `.claude/skills/prd-gate/repo.md` | Moved to `.claude/skills/prd-flow/repo.md` (project-owned, values kept). The kit's other skill files are installed as kit-owned |
| `.claude/skills/prd-gate/` | Deleted after the move, once the user confirms nothing else in it was edited (hash versus manifest; an edited file is shown and kept aside) |
| `.claude/prd-gate/state/` | Moved to `.claude/prd-flow/state/` (git-ignored; nothing to commit) |
| References | `prd-gate` replaced by `prd-flow` in `CLAUDE.md`, `AGENTS.md`, the constitution, `.claude/settings.json`, `.gitignore`, `ai-kit.json`, `docs/prd/README.md`, `docs/trd/`, `docs/templates/`, each as a shown diff; a project sentence that merely mentions the old name is rewritten, never dropped |
| `repo.md` keys | Added with their defaults: `proposed_marker` `proposed`, `html_mode` (`hand` for a project with a hand HTML until the next row is accepted), `html_template` `docs/templates/prd.html`, `trd_budget_lines` `250`; sections "Rule owners" and "Shared PRDs" added empty (ask for owners and siblings) |
| HTML | When `html_mode` is `hand`: render `build_prd_html.py` to a preview, show it, and if the user accepts set `html_mode` to `generated` and replace the hand HTML by the build output; otherwise keep `hand` |
| `.github/CODEOWNERS` | Added from the template, filled from "Rule owners" or left commented; an existing file only gets the `docs/prd/**` line proposed |
| `settings.json` | Allow entries for `gate.py` and `build_prd_html.py` under the new path; the old `prd-gate` entries are removed |
| Contracts | When "Consumers in sibling repositories" lists a consumer and `ai-kit.json` `contracts` is empty, propose snapshots |
| Manifest | Paths rewritten to the new folder, hashes recomputed |

## Migration to the chief contract
No new installed file. The five agents and the `prd-create` and `trd-create` skills (their `SKILL.md` and `reference/workers.md`) gain new modes and a five-field return (`Status`, `Files`, `Commit`, `Route`, `Next`); replace them when unchanged, otherwise three-way diff and ask. The executor gains `close` and `fix` modes and the docs agent `rules` and `fold`; nothing to configure. Per-task deliveries are written by the agents to `.claude/prd-flow/state/<slug>/deliveries/<task>.md` in the git-ignored state folder; a change in flight with a single `deliveries.md` finishes as it is. `CLAUDE.md` and `AGENTS.md` keep their project text; only the sentence about the prd-flow main thread is proposed as a diff.

## Migration from prd-flow workers to agents
List first, then ask; apply only after yes. A kit-owned file edited since install (hash versus manifest) is shown and kept aside, not deleted.

| Change | How |
|---|---|
| `.claude/skills/prd-flow/reference/workers/` | Removed (kit-owned) |
| Agents | The five `prd-flow-{surveyor,docs,executor,reviewer,recheck}.md` added to `.claude/agents/`; a project agent with the same name is shown as a diff and never overwritten silently |
| Scripts | `.claude/skills/prd-flow/scripts/promote.py` and `scripts/close_gate.py` added (kit-owned); `scripts/gates.sh` replaced (new targets `close [slug]` and `html`) |
| `repo.md` key | `prd_section_budget_lines` added with its default `200` |
| `ai-kit.json` keys | `limits.skill_md_bytes` `6144` and `allowlist.skill_md_bytes` added; the allowlist is computed from the project's current `SKILL.md` sizes (every `.claude/skills/*/SKILL.md` over 6144 bytes, at its current size) so the ratchet stays green; then `python scripts/ratchet.py` to confirm |
| `settings.json` | Allow entry `Bash(python .claude/skills/prd-flow/scripts/promote.py:*)` added |
| References | Mentions of `reference/workers` in project files are rewritten to the matching agent, each as a shown diff |
