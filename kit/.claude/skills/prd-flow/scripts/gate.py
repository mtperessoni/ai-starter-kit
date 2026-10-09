"""Structural gate of prd-flow: PRD markdown, optional HTML, INDEX, CHANGELOG, TRD and state files.

Configuration comes from the "Gate config" table of ../repo.md.

Modules beside it: gate_core (state, parsing), gate_prd, gate_plan, gate_rules (Q4), gate_interview (Q3),
gate_status, gate_remote (G27), gate_trd (G23 to G26), gate_sibling (G28), gate_html_build (G29, G32).

Usage: python .claude/skills/prd-flow/scripts/gate.py [--base REF]
       python .claude/skills/prd-flow/scripts/gate.py --pack <pack.md>
       python .claude/skills/prd-flow/scripts/gate.py --rules <approved-rules.md>
       python .claude/skills/prd-flow/scripts/gate.py --rules <approved-rules.md> --applied
       python .claude/skills/prd-flow/scripts/gate.py --status [--prd <folder>] [--state <state>]
       python .claude/skills/prd-flow/scripts/gate.py --plan <plan.md>
       python .claude/skills/prd-flow/scripts/gate.py --sheet <slug>
       python .claude/skills/prd-flow/scripts/gate.py --trace
       python .claude/skills/prd-flow/scripts/gate.py --change <changes/NNN-slug>
       python .claude/skills/prd-flow/scripts/gate.py --final [--change <slug>]
       python .claude/skills/prd-flow/scripts/gate.py --snapshot <slug>
       python .claude/skills/prd-flow/scripts/gate.py --docs <slug> [--fresh]
       python .claude/skills/prd-flow/scripts/gate.py --trd
       python .claude/skills/prd-flow/scripts/gate.py --sibling
       python .claude/skills/prd-flow/scripts/gate.py --html
       python .claude/skills/prd-flow/scripts/gate.py --step prd [--rules <approved-rules.md> --applied]
       python .claude/skills/prd-flow/scripts/gate.py --step trd
       python .claude/skills/prd-flow/scripts/gate.py --step plan --plan <plan.md> [--change <changes/NNN-slug>]
--step: one run per agent step, one report. prd: default run, --rules and --applied when given, --sibling.
        trd: default run and --trd. plan: --plan and --change, plus the computed WAVE table and CRITICAL PATH (Owns overlap in a wave fails).
--sheet: sheet.md (and sheet-2.md) of the slug: decisions complete (S1), pack rules in the diff (S2), no repeated topic or over 8 items (S3), plain_words (S4 warn), numbers named (S5 warn), interactions exist (S6); S0 is the structure. --questions is the old name.
--plan: P11 to P16 (Contract covers the TRD Planned IDs of the Owns, Reached from, at most 8 Owns files, a test path) warn unless plan_strict is yes; P12 (open TRD-only decision) always fails.
--rules and --applied read rules.md through state_record (approved-rules.md only as the legacy file).
--rules also runs Q5 (every conflict of the pack is resolved under '## Conflicts', a rewrite keeps its ID).
G31: a PRD section file over prd_section_budget_lines (warning).
--rules: rows against the PRD (Q2), every sheet item answered in answers.md and no unasked mechanism (Q3), and G27 for IDs used on remote branches.
--applied: with --rules, every approved row exists in the PRD file named by its heading, identical (Q4).
--status: ID, state, file, Source and Change via of each rule; states proposed, approved, superseded, implemented.
--trace: every PRD rule not planned is cited by a test file (test_patterns of ai-kit.json);
         untested rules are held to allowlist.untested_rules, which only shrinks.
--change: brief.md of a change folder against the PRD and its plan.md.
--final: nothing planned, pending, proposed (G30) or open is left (CI, on pushes to the base branch).
--final --change <slug>: G19 to G21 only for the slug's approved rows, its '## Planned (<slug>' heading and its folder; the rest is a warning (gate_scope).
--snapshot <slug>: records the older G19 to G21 drift (final-snapshot.json in the slug state) so a scoped final reports it as pre-existing.
--docs <slug>: default prd checks, --rules --applied when approved-rules.md exists, trd and plan in one run; cached by input mtimes (--fresh reruns).
--trd: backticked paths exist (G23), symbols (G24) are in the row's files, files within trd_budget_lines (G26).
--sibling: PRD folders listed under "Shared PRDs" of repo.md equal the sibling repository's (G28).
The default run and --step never print a stale page (G29, G32 only under --html); html_mode hand warns G5. G25 and the G28 absent-sibling warning are not printed.
--html: the strict HTML check of the docs-html skill, html_mode generated only (G29, G32 and G4 on the pages are errors, hand is an error G5).
Modules: gate_output (capped stdout, artifact .claude/prd-flow/state/_gate/last-<mode>.txt, --step trd scoped to TRD files changed since the base).
Exits with 1 when there is an ERROR. A WARNING does not fail.
"""

import argparse
import re
import sys
from pathlib import Path

from gate_core import (
    EM_DASH, ID, ROW, git, is_proposed, joined, literal_rows, load_config, read_md_rules, rule_table_ids, err, warn,
)
from gate_interview import check_answers, check_sheet
from state_record import approved_text
from gate_budget import added_lines, names_id, check_sections, strip_markers
from gate_output import base_ref, changed_paths, report, start
from gate_plan import check_change, check_final, check_plan, check_trace, snapshot_drift
from gate_scope import code_state, cache_load, cache_replay, cache_store, find_plan, inputs_key, slug_of, state_dir
from gate_core import notes
from gate_prd import changed_rows, check_index, check_pack, check_rules
from gate_html_build import check_html_flow, check_html_strict
from gate_remote import warn_remote_change, warn_remote_ids
from gate_rules import check_applied, check_conflicts
from gate_sibling import check_sibling
from gate_status import STATES, status_lines
from gate_trd import check_trd
from gate_waves import check_waves


def approved_ids(text: str) -> set[str]:
    ids = set()
    for _, line in literal_rows(text):
        m = ROW.match(line)
        if m:
            ids.add(m.group(1))
    return ids


def default_checks(root: Path, cfg: dict[str, str], rules, vias: set[str], base_arg: str | None, scoped: bool = False) -> str:
    prd_rel, trd_rel = cfg["prd_dir"].rstrip("/"), cfg["trd_dir"].rstrip("/")
    prd, trd = root / prd_rel, root / trd_rel
    base = base_ref(root, cfg, base_arg)
    old, new, touched, plain = changed_rows(root, base, prd_rel, cfg["prd_glob"])
    check_index(prd, rules, set(new) - set(old))
    changelog = f"{prd_rel}/CHANGELOG.md"
    added = added_lines(root, base, changelog)
    check_sections(root, cfg, prd, changed_paths(root, cfg, base_arg) if scoped else None)

    if cfg["forbid_em_dash"].lower() in {"yes", "true", "on"}:
        for f in [*prd.rglob("*.md"), *trd.rglob("*.md")]:
            for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if EM_DASH in line:
                    err("G4", f"em dash in {f.relative_to(root).as_posix()}:{n}")

    for rid, row in sorted(new.items()):
        rule_row = rid in rule_table_ids and len(row) >= 3
        if rule_row and (not row[1] or not row[2]):
            err("G3", f"{rid} without Source or Change via")
        elif rule_row and row[2].strip("` ").lower() not in vias:
            warn("G3", f"{rid}: Change via '{row[2]}' outside {sorted(vias)}")
        marked = cfg["pending_marker"] if cfg["pending_marker"] in row[0] else cfg["proposed_marker"]
        if (cfg["pending_marker"] in row[0] or is_proposed(row[0], cfg)) and len(row) >= 2 and cfg["planned_source"] not in row[1].lower():
            warn("G9", f"{rid} marked '{marked}' with Source other than '{cfg['planned_source']}'")
        if rid in old:
            before, after = joined(strip_markers(old[rid][0], cfg)), joined(strip_markers(row[0], cfg))
            if before not in after and not names_id(added, rid):
                err("G7", f"{rid} was reworded without an added CHANGELOG line naming {rid}", f"add a line naming {rid} to {changelog}, or revert the text change")
    for rid in sorted(set(old) - set(new) - set(rules)):
        if not names_id(added, rid):
            err("G7", f"{rid} left the PRD without an added CHANGELOG line naming {rid}", f"add a line naming {rid} to {changelog}")
    if set(new) - set(old) and f"{prd_rel}/INDEX.md" not in touched:
        warn("G2", "new IDs and INDEX.md was not touched")

    check_html_flow(root, cfg)

    known = set(rules)
    for f in trd.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        for block in re.findall(r"^## " + re.escape(cfg["planned_heading"]) + r".*?(?=^## |\Z)", text, re.S | re.M):
            for rid in sorted(set(re.findall(r"\b(" + ID + r")\b", block))):
                if not rid.startswith("I-") and rid not in known:
                    err("G8", f"{f.name}: '{cfg['planned_heading']}' cites {rid}, which does not exist in the PRD")

    return f", base {base[:10]}, {len(rules)} rules"


def docs_checks(root: Path, cfg, rules, vias, args, repo_md: Path, rules_checks, change_checks) -> str:
    slug = slug_of(args.docs)
    state = state_dir(root, slug)
    approved = state / "approved-rules.md"
    has_rules = approved_text(state) is not None
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
    suffix = default_checks(root, cfg, rules, vias, args.base, True)
    if has_rules:
        args.rules, args.applied = approved, True
        rules_checks()
    if (state / "sheet.md").is_file():
        check_sheet(state, cfg)
    check_sibling(root, repo_md)
    diff = changed_paths(root, cfg, args.base)
    check_trd(root, cfg, trd_rel, {n for n in diff if n.startswith(trd_rel + "/")}, diff)
    if plan:
        check_plan(plan, rules, cfg, root)
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
    parser.add_argument("--pack", type=Path, metavar="FILE", help="check a pack.md of the state folder (Q1)")
    parser.add_argument("--rules", type=Path, metavar="FILE|SLUG", help="check the approved rules of a state folder: rows, conflicts, answers (Q2 to Q5)")
    parser.add_argument("--plan", type=Path, metavar="FILE", help="check a plan for agents (P1 to P17)")
    parser.add_argument("--sheet", "--questions", dest="sheet", metavar="SLUG", help="lint sheet.md and sheet-2.md of a change (S0 to S6); --questions is the old name")
    parser.add_argument("--trace", action="store_true", help="every non-planned PRD rule is cited by a test file")
    parser.add_argument("--change", type=Path, metavar="FOLDER", help="check a change folder (brief.md, design.md, plan.md)")
    parser.add_argument("--final", action="store_true", help="nothing planned, pending, proposed or open is left (with --change: scoped to the slug)")
    parser.add_argument("--applied", action="store_true", help="with --rules: the approved rows exist in the PRD, identical (Q4)")
    parser.add_argument("--trd", action="store_true", help="check TRD paths, symbols and size against the tracked files (G23, G24, G26)")
    parser.add_argument("--html", action="store_true", help="strict check of the generated PRD and TRD pages (G29, G32; docs-html skill)")
    parser.add_argument("--sibling", action="store_true", help="check the shared PRD folders against the sibling repositories (G28)")
    parser.add_argument("--snapshot", metavar="SLUG", help="record the older final-gate drift so a scoped final reports it as pre-existing")
    parser.add_argument("--docs", metavar="SLUG", help="sheet, rules, prd, trd and plan checks of one change in one run (cached)")
    parser.add_argument("--fresh", action="store_true", help="with --docs: ignore the cache")
    parser.add_argument("--status", action="store_true", help="print the state of every rule")
    parser.add_argument("--prd", metavar="FOLDER", help="with --status: only this PRD folder")
    parser.add_argument("--state", choices=STATES, help="with --status: only this state")
    parser.add_argument("--step", choices=("prd", "trd", "plan"), metavar="STEP", help="prd, trd or plan: every check of one agent step in one report")
    args = parser.parse_args()
    cfg = load_config()
    vias = {v.strip().lower() for v in cfg["change_via"].split(",") if v.strip()}
    root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").strip() or ".")
    if args.rules and args.rules.suffix != ".md":
        args.rules = state_dir(root, slug_of(str(args.rules))) / "approved-rules.md"
    prd_rel, trd_rel = cfg["prd_dir"].rstrip("/"), cfg["trd_dir"].rstrip("/")
    prd, trd = root / prd_rel, root / trd_rel
    rules = read_md_rules(prd, cfg["prd_glob"], cfg["via_header"])
    flags = [n for n in ("pack", "rules", "plan", "sheet", "trace", "change", "final", "trd", "sibling", "html", "snapshot", "docs") if getattr(args, n)]
    mode = f"step-{args.step}" if args.step else ("-".join(flags) if flags else "default")
    start(mode, root, capped=mode != "trd")

    if args.status:
        print(chr(10).join(status_lines(rules, vias, cfg, prd, args.prd, args.state)))
        return report()

    repo_md = Path(__file__).resolve().parents[1] / "repo.md"

    def rules_checks() -> None:
        text = approved_text(args.rules.parent)
        if text is None and args.rules.is_file():
            text = args.rules.read_text(encoding="utf-8")
        if text is None:
            err("Q2", f"no rules.md and no {args.rules.name} in {args.rules.parent}", "write the state record with the docs agent in rules mode")
            return
        check_rules(args.rules, rules, cfg, vias, text)
        check_conflicts(args.rules, rules, text)
        check_answers(args.rules.parent, cfg)
        if args.applied:
            check_applied(args.rules, rules, cfg, text)
        warn_remote_ids(root, prd_rel, approved_ids(text) - set(rules))

    def change_checks() -> None:
        folder = args.change if args.change.is_absolute() else root / args.change
        check_change(folder, rules)
        warn_remote_change(root, folder)

    if args.sheet:
        given = Path(args.sheet)
        check_sheet(given if given.is_file() else state_dir(root, slug_of(args.sheet)), cfg)
        return report()

    if args.snapshot:
        path = snapshot_drift(root, rules, cfg, trd, slug_of(args.snapshot))
        notes.append(f"snapshot: older final-gate drift recorded in {path.relative_to(root).as_posix()}")
        return report()

    if args.docs:
        return report(docs_checks(root, cfg, rules, vias, args, repo_md, rules_checks, change_checks))

    if args.step:
        suffix = default_checks(root, cfg, rules, vias, args.base, True) if args.step in ("prd", "trd") else ""
        if args.step == "prd":
            if args.rules:
                rules_checks()
            check_sibling(root, repo_md)
        elif args.step == "trd":
            diff = changed_paths(root, cfg, args.base)
            check_trd(root, cfg, trd_rel, {n for n in diff if n.startswith(trd_rel + "/")}, diff)
        else:
            if args.plan:
                check_plan(args.plan, rules, cfg, root)
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

    if args.trace or args.change or args.final:
        if args.trace:
            check_trace(root, rules, cfg, vias)
        if args.change and not args.final:
            change_checks()
        if args.final:
            check_final(root, rules, cfg, trd, str(args.change) if args.change else None)
        return report()

    if args.pack or args.rules or args.plan:
        if args.pack:
            check_pack(root, args.pack, rules, cfg)
        if args.rules:
            rules_checks()
        if args.plan:
            check_plan(args.plan, rules, cfg, root)
        return report()

    return report(default_checks(root, cfg, rules, vias, args.base))


if __name__ == "__main__":
    sys.exit(main())
