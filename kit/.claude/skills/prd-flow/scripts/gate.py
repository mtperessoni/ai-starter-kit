"""Structural gate of prd-flow: PRD markdown, optional HTML, INDEX, CHANGELOG, TRD and state files.

Configuration comes from the "Gate config" table of ../repo.md.

Modules beside it: gate_core (state, parsing), gate_prd, gate_plan, gate_rules (Q4), gate_interview (Q3),
gate_status, gate_remote (G27), gate_trd (G23 to G26), gate_sibling (G28), gate_html_build (G29).

Usage: python .claude/skills/prd-flow/scripts/gate.py [--base REF]
       python .claude/skills/prd-flow/scripts/gate.py --pack <pack.md>
       python .claude/skills/prd-flow/scripts/gate.py --rules <approved-rules.md>
       python .claude/skills/prd-flow/scripts/gate.py --rules <approved-rules.md> --applied
       python .claude/skills/prd-flow/scripts/gate.py --status [--prd <folder>] [--state <state>]
       python .claude/skills/prd-flow/scripts/gate.py --plan <plan.md>
       python .claude/skills/prd-flow/scripts/gate.py --trace
       python .claude/skills/prd-flow/scripts/gate.py --change <changes/NNN-slug>
       python .claude/skills/prd-flow/scripts/gate.py --final
       python .claude/skills/prd-flow/scripts/gate.py --trd
       python .claude/skills/prd-flow/scripts/gate.py --sibling
       python .claude/skills/prd-flow/scripts/gate.py --step prd [--rules <approved-rules.md> --applied]
       python .claude/skills/prd-flow/scripts/gate.py --step trd
       python .claude/skills/prd-flow/scripts/gate.py --step plan --plan <plan.md> [--change <changes/NNN-slug>]
--step: one run per agent step, one report. prd: default run, --rules and --applied when given, --sibling.
        trd: default run and --trd. plan: --plan and --change, plus the computed WAVE table and CRITICAL PATH (Owns overlap in a wave fails).
--rules also runs Q5 (every conflict of the pack is resolved under '## Conflicts', a rewrite keeps its ID).
G31: a PRD section file over prd_section_budget_lines (warning).
--rules: rows against the PRD (Q2), the interview.md beside the file (Q3), and G27 for IDs used on remote branches.
--applied: with --rules, every approved row exists in the PRD file named by its heading, identical (Q4).
--status: ID, state, file, Source and Change via of each rule; states proposed, approved, superseded, implemented.
--trace: every PRD rule not planned is cited by a test file (test_patterns of ai-kit.json);
         untested rules are held to allowlist.untested_rules, which only shrinks.
--change: brief.md of a change folder against the PRD and its plan.md.
--final: nothing planned, pending, proposed (G30) or open is left (CI, on pushes to the base branch).
--trd: backticked paths exist (G23), symbols (G24) and IDs (G25) are in the row's files, files within trd_budget_lines (G26).
--sibling: PRD folders listed under "Shared PRDs" of repo.md equal the sibling repository's (G28).
With html_mode generated the default run checks the HTML against build_prd_html.py (G29) instead of G5, G6 and G10.
Modules: gate_output (capped stdout, artifact .claude/prd-flow/state/_gate/last-<mode>.txt, --step trd scoped to TRD files changed since the base).
Exits with 1 when there is an ERROR. A WARNING does not fail.
"""

import argparse
import re
import sys
from pathlib import Path

from gate_core import (
    EM_DASH, ID, ROW, git, is_proposed, joined, literal_rows, load_config, read_html_rules, read_md_rules, rule_table_ids, err, warn,
)
from gate_interview import check_interview
from gate_budget import added_lines, names_id, check_sections, strip_markers
from gate_output import base_ref, changed_paths, report, start
from gate_plan import check_change, check_final, check_plan, check_trace
from gate_prd import changed_rows, check_html, check_index, check_pack, check_rules
from gate_html_build import check_generated
from gate_remote import warn_remote_change, warn_remote_ids
from gate_rules import check_applied, check_conflicts
from gate_sibling import check_sibling
from gate_status import STATES, status_lines
from gate_trd import check_trd
from gate_waves import check_waves


def approved_ids(path: Path) -> set[str]:
    ids = set()
    for _, line in literal_rows(path.read_text(encoding="utf-8")):
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
    html_on = cfg["html"].lower() not in {"", "none", "no", "off"}
    generated = html_on and cfg["html_mode"].lower() == "generated"

    if cfg["forbid_em_dash"].lower() in {"yes", "true", "on"}:
        scanned = [*prd.rglob("*.md"), *trd.rglob("*.md")]
        if html_on and (root / cfg["html"]).exists():
            scanned.append(root / cfg["html"])
        for f in scanned:
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

    page_ids: set[str] = set()
    if generated:
        check_generated(root, cfg)
    elif html_on:
        page_path = root / cfg["html"]
        if page_path.exists():
            check_html(page_path, rules, old, new, touched, plain, vias)
            page_ids = set(read_html_rules(page_path))
        else:
            err("G5", f"html is set to {cfg['html']} and the file does not exist")

    known = set(rules) | page_ids
    for f in trd.rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        for block in re.findall(r"^## " + re.escape(cfg["planned_heading"]) + r".*?(?=^## |\Z)", text, re.S | re.M):
            for rid in sorted(set(re.findall(r"\b(" + ID + r")\b", block))):
                if not rid.startswith("I-") and rid not in known:
                    err("G8", f"{f.name}: '{cfg['planned_heading']}' cites {rid}, which does not exist in the PRD")

    return f", base {base[:10]}, {len(rules)} rules"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=None, help="comparison ref; default: merge-base with origin/<base_branch>")
    parser.add_argument("--pack", type=Path, help="check a pack.md from the state folder")
    parser.add_argument("--rules", type=Path, help="check an approved-rules.md from the state folder")
    parser.add_argument("--plan", type=Path, help="check a plan for agents")
    parser.add_argument("--trace", action="store_true", help="every non-planned PRD rule is cited by a test file")
    parser.add_argument("--change", type=Path, help="check a change folder (brief.md, design.md, plan.md)")
    parser.add_argument("--final", action="store_true", help="nothing planned, pending or open is left")
    parser.add_argument("--applied", action="store_true", help="with --rules: the rows were written to the PRD literally")
    parser.add_argument("--trd", action="store_true", help="check the TRD paths, symbols, IDs and size against the tracked files")
    parser.add_argument("--sibling", action="store_true", help="check the shared PRD folders against the sibling repositories")
    parser.add_argument("--status", action="store_true", help="print the state of every rule")
    parser.add_argument("--prd", help="with --status: only this PRD folder")
    parser.add_argument("--state", choices=STATES, help="with --status: only this state")
    parser.add_argument("--step", choices=("prd", "trd", "plan"), help="every check of one agent step in one run and one report")
    args = parser.parse_args()
    cfg = load_config()
    vias = {v.strip().lower() for v in cfg["change_via"].split(",") if v.strip()}
    root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").strip() or ".")
    prd_rel, trd_rel = cfg["prd_dir"].rstrip("/"), cfg["trd_dir"].rstrip("/")
    prd, trd = root / prd_rel, root / trd_rel
    rules = read_md_rules(prd, cfg["prd_glob"], cfg["via_header"])
    flags = [n for n in ("pack", "rules", "plan", "trace", "change", "final", "trd", "sibling") if getattr(args, n)]
    mode = f"step-{args.step}" if args.step else ("-".join(flags) if flags else "default")
    start(mode, root, capped=mode != "trd")

    if args.status:
        print(chr(10).join(status_lines(rules, vias, cfg, prd, args.prd, args.state)))
        return report()

    repo_md = Path(__file__).resolve().parents[1] / "repo.md"

    def rules_checks() -> None:
        check_rules(args.rules, rules, cfg, vias)
        check_conflicts(args.rules, rules)
        check_interview(args.rules, prd, rules)
        if args.applied:
            check_applied(args.rules, rules, cfg)
        warn_remote_ids(root, prd_rel, approved_ids(args.rules) - set(rules))

    def change_checks() -> None:
        folder = args.change if args.change.is_absolute() else root / args.change
        check_change(folder, rules)
        warn_remote_change(root, folder)

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
                check_plan(args.plan, rules, cfg)
                check_waves(args.plan)
            if args.change:
                change_checks()
        return report(suffix)

    if args.trd or args.sibling:
        if args.trd:
            check_trd(root, cfg, trd_rel)
        if args.sibling:
            check_sibling(root, repo_md)
        return report()

    if args.trace or args.change or args.final:
        if args.trace:
            check_trace(root, rules, cfg, vias)
        if args.change:
            change_checks()
        if args.final:
            check_final(root, rules, cfg, trd)
        return report()

    if args.pack or args.rules or args.plan:
        if args.pack:
            check_pack(root, args.pack, rules, cfg)
        if args.rules:
            rules_checks()
        if args.plan:
            check_plan(args.plan, rules, cfg)
        return report()

    return report(default_checks(root, cfg, rules, vias, args.base))


if __name__ == "__main__":
    sys.exit(main())
