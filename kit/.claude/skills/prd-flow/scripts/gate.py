"""Structural gate of prd-flow: PRD markdown, optional HTML, TRD and plan files.

Configuration comes from the "Gate config" table of ../repo.md.

Modules beside it: gate_core (state, parsing), gate_prd (changed rows), gate_changed (G8, D4), gate_plan (G15, G22),
gate_waves (--step plan: waves, P17), gate_status, gate_trd (G23), gate_sibling (G28), gate_html_build (G29, G32).

Usage: python .claude/skills/prd-flow/scripts/gate.py [--base REF]
       python .claude/skills/prd-flow/scripts/gate.py --status [--prd <folder>] [--state <state>]
       python .claude/skills/prd-flow/scripts/gate.py --plan <plan.md>
       python .claude/skills/prd-flow/scripts/gate.py --change <changes/NNN-slug>
       python .claude/skills/prd-flow/scripts/gate.py --docs <slug> [--fresh]
       python .claude/skills/prd-flow/scripts/gate.py --trd
       python .claude/skills/prd-flow/scripts/gate.py --sibling
       python .claude/skills/prd-flow/scripts/gate.py --html
       python .claude/skills/prd-flow/scripts/gate.py --history <ID>
       python .claude/skills/prd-flow/scripts/gate.py --step prd
       python .claude/skills/prd-flow/scripts/gate.py --step trd
       python .claude/skills/prd-flow/scripts/gate.py --step plan --plan <plan.md> [--change <changes/NNN-slug>]
Errors: G0 (base ref missing), G1 (duplicate rule ID), G8 (a rule ID added to a TRD file or a test that no PRD row defines, or a '## Planned' block citing one),
G15 and G22 (--change: brief.md cites an ID that does not exist, the folder is missing), G5 and G29 and G32 (--html only).
Warnings: G23 (TRD path matches no tracked file), G28 (shared PRD folder differs from the sibling repository), D4 (pending marker or '## Planned' TRD section added), P17 (shared file in one wave), G33 (a PRD or TRD markdown file over 40 KB).
--step: one run per agent step, one report. prd: default run and --sibling. trd: default run and --trd. plan: --plan and --change, plus the computed WAVE table and CRITICAL PATH.
--plan: prints the WAVE table and the CRITICAL PATH of the plan cards (never counted); P17 when two tasks of one wave touch a shared file.
--status: ID, state, file, Source and Change via of each rule; states proposed, approved, superseded, implemented.
--change: brief.md of a change folder against the PRD (G15).
--docs <slug>: the default run, trd, sibling, plan and change checks of one slug in one run; cached by input mtimes (--fresh reruns).
--trd: backticked paths in the TRD exist (G23).
--sibling: PRD folders listed under "Shared PRDs" of repo.md equal the sibling repository's (G28).
--history <ID>: commits (newest first) whose diff touched the rule's PRD row or whose Rules: trailer names it, with date, sha, subject and the Request:, Decided:, Assumed: body lines.
--html: the strict HTML check of the docs-html skill, html_mode generated only (G29, G32; hand is an error G5). No other run checks HTML.
Output: stdout carries the errors and one line 'warnings: N (see .claude/prd-flow/state/_gate/last-<mode>.txt)'; the full report with the warnings is in that file.
Exits with 1 when there is an ERROR. A WARNING does not fail.
"""

import argparse
import re
import sys
from pathlib import Path

from gate_changed import check_cited_ids, kit_tests, warn_added_planned
from gate_core import ID, err, git, load_config, read_md_rules, warn
from gate_history import history
from gate_html_build import check_html_strict
from gate_output import base_ref, changed_paths, report, start
from gate_plan import check_change
from gate_prd import changed_rows
from gate_scope import cache_load, cache_replay, cache_store, code_state, find_plan, inputs_key, slug_of, state_dir
from gate_sibling import check_sibling
from gate_status import STATES, status_lines
from gate_trd import check_trd
from gate_waves import check_waves

BIG_DOC_BYTES = 40 * 1024


def default_checks(root: Path, cfg: dict[str, str], rules, base_arg: str | None) -> str:
    prd_rel, trd_rel = cfg["prd_dir"].rstrip("/"), cfg["trd_dir"].rstrip("/")
    trd = root / trd_rel
    base = base_ref(root, cfg, base_arg)
    old, new, _, _ = changed_rows(root, base, prd_rel, cfg["prd_glob"])
    check_cited_ids(root, base, rules, trd_rel, kit_tests(root), changed_paths(root, cfg, base_arg))
    warn_added_planned(root, cfg, base, old, new, trd_rel)

    known = set(rules)
    for f in trd.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        for block in re.findall(r"^## " + re.escape(cfg["planned_heading"]) + r".*?(?=^## |\Z)", text, re.S | re.M):
            for rid in sorted(set(re.findall(r"\b(" + ID + r")\b", block))):
                if not rid.startswith("I-") and rid not in known:
                    err("G8", f"{f.name}: '{cfg['planned_heading']}' cites {rid}, which does not exist in the PRD")

    for f in [*(root / prd_rel).rglob("*.md"), *trd.rglob("*.md")]:
        if f.name == "CHANGELOG.md":
            continue
        size = f.stat().st_size
        if size > BIG_DOC_BYTES:
            warn("G33", f"{f.relative_to(root).as_posix()} is {size // 1024} KB, over {BIG_DOC_BYTES // 1024} KB: split it, an agent reads it whole")

    return f", base {base[:10]}, {len(rules)} rules"


def docs_checks(root: Path, cfg, rules, args, repo_md: Path, change_checks) -> str:
    slug = slug_of(args.docs)
    state = state_dir(root, slug)
    plan = find_plan(root, slug)
    prd_rel, trd_rel = cfg["prd_dir"].rstrip("/"), cfg["trd_dir"].rstrip("/")
    base = base_ref(root, cfg, args.base)
    head = git(root, "rev-parse", "HEAD").strip()
    watched = [prd_rel, trd_rel, state.relative_to(root).as_posix(), f"changes/{slug}", "ai-kit.json", repo_md.relative_to(root).as_posix()]
    key = inputs_key(root, watched, f"{base}|{head}|{args.docs}|{args.base}|{code_state(root)}")
    cache = state.parent / "_gate" / f"docs-{slug}.json"
    if not args.fresh:
        hit = cache_load(cache, key)
        if hit:
            return cache_replay(hit)
    suffix = default_checks(root, cfg, rules, args.base)
    check_sibling(root, repo_md)
    diff = changed_paths(root, cfg, args.base)
    check_trd(root, cfg, trd_rel, {n for n in diff if n.startswith(trd_rel + "/")})
    if plan:
        check_waves(plan, cfg)
    folder = root / "changes"
    if folder.is_dir() and any(d.is_dir() and d.name.endswith(slug) for d in folder.iterdir()):
        args.change = next(d for d in sorted(folder.iterdir()) if d.is_dir() and d.name.endswith(slug))
        change_checks()
    cache_store(cache, key, suffix)
    return suffix


def main() -> int:
    parser = argparse.ArgumentParser(
        description="prd-flow structural gate. No flag: the default PRD run. Exit 1 on an ERROR.",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=30, width=200),
    )
    parser.add_argument("--base", default=None, metavar="REF", help="comparison ref (default: merge-base with origin/<base_branch>)")
    parser.add_argument("--plan", type=Path, metavar="FILE", help="print the waves and the critical path of a plan (P17)")
    parser.add_argument("--change", type=Path, metavar="FOLDER", help="check a change folder (brief.md against the PRD)")
    parser.add_argument("--trd", action="store_true", help="check TRD paths against the tracked files (G23, a warning)")
    parser.add_argument("--html", action="store_true", help="strict check of the generated PRD and TRD pages (G29, G32; docs-html skill)")
    parser.add_argument("--sibling", action="store_true", help="check the shared PRD folders against the sibling repositories (G28, a warning)")
    parser.add_argument("--docs", metavar="SLUG", help="default, trd, sibling, plan and change checks of one change in one run (cached)")
    parser.add_argument("--fresh", action="store_true", help="with --docs: ignore the cache")
    parser.add_argument("--history", metavar="ID", help="print the history of one rule from git: commits that touched its PRD row or name it in Rules:")
    parser.add_argument("--status", action="store_true", help="print the state of every rule")
    parser.add_argument("--prd", metavar="FOLDER", help="with --status: only this PRD folder")
    parser.add_argument("--state", choices=STATES, help="with --status: only this state")
    parser.add_argument("--step", choices=("prd", "trd", "plan"), metavar="STEP", help="prd, trd or plan: every check of one agent step in one report")
    args = parser.parse_args()
    cfg = load_config()
    vias = {v.strip().lower() for v in cfg["change_via"].split(",") if v.strip()}
    root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").strip() or ".")
    prd_rel, trd_rel = cfg["prd_dir"].rstrip("/"), cfg["trd_dir"].rstrip("/")
    prd = root / prd_rel
    if args.history:
        print("\n".join(history(root, args.history, prd_rel)))
        return 0
    rules = read_md_rules(prd, cfg["prd_glob"], cfg["via_header"])
    flags = [n for n in ("plan", "change", "trd", "sibling", "html", "docs") if getattr(args, n)]
    mode = f"step-{args.step}" if args.step else ("-".join(flags) if flags else "default")
    start(mode, root, capped=mode != "trd")

    if args.status:
        print(chr(10).join(status_lines(rules, vias, cfg, prd, args.prd, args.state)))
        return report()

    repo_md = Path(__file__).resolve().parents[1] / "repo.md"

    def change_checks() -> None:
        folder = args.change if args.change.is_absolute() else root / args.change
        check_change(folder, rules)

    if args.docs:
        return report(docs_checks(root, cfg, rules, args, repo_md, change_checks))

    if args.step:
        suffix = default_checks(root, cfg, rules, args.base) if args.step in ("prd", "trd") else ""
        if args.step == "prd":
            check_sibling(root, repo_md)
        elif args.step == "trd":
            diff = changed_paths(root, cfg, args.base)
            check_trd(root, cfg, trd_rel, {n for n in diff if n.startswith(trd_rel + "/")})
        else:
            if args.plan:
                check_waves(args.plan, cfg)
            if args.change:
                change_checks()
        return report(suffix)

    if args.trd or args.sibling or args.html:
        if args.html:
            check_html_strict(root, cfg)
        if args.trd:
            check_trd(root, cfg, trd_rel)
        if args.sibling:
            check_sibling(root, repo_md)
        return report()

    if args.change or args.plan:
        if args.change:
            change_checks()
        if args.plan:
            check_waves(args.plan, cfg)
        return report()

    return report(default_checks(root, cfg, rules, args.base))


if __name__ == "__main__":
    sys.exit(main())
