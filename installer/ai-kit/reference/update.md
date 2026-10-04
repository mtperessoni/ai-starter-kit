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
| U6 | New keys in `ai-kit.json` get their defaults; new linter rules from an updated recipe are proposed with a baseline |
| U7 | Plan table (K03): replace, merge, propose, skip; wait for yes |
| U8 | Apply, run the Verify list of `install.md`, update the manifest (version, date, hashes) |
| U9 | Commit `chore: update ai-starter-kit to <new>` with the kit log lines in the body; report |
