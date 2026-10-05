---
name: ai-kit
description: Installs, updates and checks the AI starter kit in the current repository. install detects the stack and the code layout (feature folders recommended, any layout works), copies the kit (prd-create, trd-create, prd-gate and adr skills, the docs system, the scripts, CI, CLAUDE.md, AGENTS.md, the constitution), fills every placeholder for this project, configures the linter to enforce the structure rules with a day-one baseline, verifies everything by running it, and commits on a branch. update brings kit improvements into a repository that already has it without overwriting what the project made its own. doctor reports what drifted. Use when the user says "install the kit", "set up the AI starter kit", "adapt the kit to this project", "/ai-kit", "update the kit", "check the kit", or starts a new project and wants the AI rules in it. Not for writing the PRD itself (prd-create) or for product changes (prd-gate).
---

# ai-kit

The kit lives in a git repository on this machine; its path is in `kit-path` next to this file (written by `install.sh` or `install.ps1`). Everything the kit writes into a project is in English. Talk to the user in their language.

## Modes
| Mode | Command | Reference |
|---|---|---|
| install | `/ai-kit install` (or `/ai-kit` in a repository without `.ai-kit/manifest.json`) | `reference/install.md` |
| update | `/ai-kit update` | `reference/update.md` |
| doctor | `/ai-kit doctor` | `reference/doctor.md` |

## Always
| ID | Rule |
|---|---|
| K01 | Read `kit-path`, then `git -C <kit> pull --ff-only -q` and `git -C <kit> rev-parse --short HEAD`: that commit is the kit version written to the manifest |
| K02 | Work on a branch (`chore/ai-kit-install` or `chore/ai-kit-update`) created from the project's base branch; never on the base branch itself. Stop if the working tree has uncommitted changes and ask |
| K03 | Show the plan (files to create, merge or skip, commands detected, questions) as a table and get an explicit yes before writing anything |
| K04 | Never overwrite a project file that already exists: merge (`reference/ownership.md` says how for each file) or ask |
| K05 | Every command written into `ai-kit.json` was run once and its result read. A command that fails is not written; it becomes a question |
| K06 | Commit with Conventional Commits in English; never push and never open a pull request without an explicit request |
| K07 | At most 4 questions per round, each with the detected value as the recommended option |
| K08 | Budget: detection reads manifests and configuration only, never source files whole; a sweep of a large tree goes to an Explore agent with questions |

## Files
| File | Read when |
|---|---|
| `reference/install.md` | install |
| `reference/update.md` | update |
| `reference/doctor.md` | doctor |
| `reference/ownership.md` | install and update, to know which files belong to the kit and which to the project |
| `<kit>/stacks/README.md`, then only the matching recipes | install, detection |
| `<kit>/kit/` | the payload copied into the project |
