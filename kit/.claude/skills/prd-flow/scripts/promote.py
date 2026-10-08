"""The mechanical part of Promote: markers, Source, CHANGELOG, HTML, archive, state, final gate.

Usage: python .claude/skills/prd-flow/scripts/promote.py <slug> [--dry-run] [--root <repo>]
Reads .claude/prd-flow/state/<slug>/approved-rules.md, deliveries.md and changes/NNN-<slug>/decisions.md.
Prints at most 10 lines. What it cannot decide (the TRD Planned merge, amendment folds) is a listed warning.
"""

import argparse
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_core import load_config  # noqa: E402

MAX_LINES = 10
ID = r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d+"
SPLIT = re.compile(r"(?<!\\)\|")
SOURCE_LINE = re.compile(rf"^Source:\s*({ID})\s*(?:->|=>|[:=])?\s*(\S+)\s*$", re.M)
SUPERSEDES = re.compile(rf"^-\s*({ID})\s*(?:\((.*)\)|:\s*(.*))\s*$")


class PromoteError(Exception):
    pass


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,  # noqa: S603, S607
                          encoding="utf-8", check=False)


def parse_approved(text: str) -> tuple[dict[str, list[str]], dict[str, str], str]:
    """Approved IDs by PRD file heading, the old texts under Supersedes, and the approver."""
    files: dict[str, list[str]] = {}
    old: dict[str, str] = {}
    approver = "unknown"
    head = re.match(r"#\s*Approved rules\s*·\s*[^·]*·\s*[^·]*·\s*(.+)", text)
    if head:
        approver = head.group(1).strip()
    section = None
    for line in text.splitlines():
        h = re.match(r"#{2,3}\s+(.+?)\s*$", line)
        if h:
            section = "supersedes" if h.group(1).lower() == "supersedes" else h.group(1)
            continue
        if section == "supersedes":
            m = SUPERSEDES.match(line.strip())
            if m:
                old[m.group(1)] = (m.group(2) if m.group(2) is not None else m.group(3)).strip()
        elif section and section.endswith(".md"):
            m = re.match(rf"\|\s*({ID})\s*\|", line)
            if m:
                files.setdefault(section, []).append(m.group(1))
    return files, old, approver


def sources_from_deliveries(text: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in SOURCE_LINE.finditer(text)}


def sources_from_trd(root: Path, cfg: dict) -> dict[str, str]:
    found: dict[str, str] = {}
    heading = cfg["planned_heading"]
    for f in sorted((root / cfg["trd_dir"]).rglob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(rf"^##\s+{re.escape(heading)}\b.*?(?=^## |\Z)", text, re.M | re.S)
        for line in m.group(0).splitlines() if m else []:
            cells = [c.strip() for c in SPLIT.split(line.strip().strip("|"))]
            if len(cells) >= 2 and cells[0].startswith("`"):
                for rid in re.findall(ID, cells[-1]):
                    found.setdefault(rid, cells[0].strip("`"))
    return found


def locate(root: Path, cfg: dict, name: str) -> Path | None:
    direct = root / name
    if direct.is_file():
        return direct
    hits = sorted((root / cfg["prd_dir"]).rglob(Path(name).name))
    return hits[0] if hits else None


def edit_rows(text: str, ids: list[str], marker: re.Pattern, sources: dict[str, str], drop: set[str]):
    """The new text, sources set, markers dropped, IDs left without a source, and the removed row lines by ID."""
    out, set_src, dropped, missing, removed = [], 0, 0, [], {}
    for line in text.splitlines(keepends=True):
        parts = SPLIT.split(line.rstrip("\n"))
        rid = parts[1].strip() if len(parts) > 3 else ""
        if rid in drop:
            removed[rid] = line.rstrip("\n")
            continue
        if rid in ids and marker.search(parts[2]):
            parts[2] = marker.sub("", parts[2], count=1)
            dropped += 1
            if rid in sources:
                parts[3] = f" {sources[rid]} "
                set_src += 1
            elif parts[3].strip() == "planned":
                missing.append(rid)
            line = "|".join(parts) + ("\n" if line.endswith("\n") else "")
        out.append(line)
    return "".join(out), set_src, dropped, missing, removed


def decision_rows(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [ln for ln in path.read_text(encoding="utf-8").splitlines() if re.match(r"\|\s*DEC-\d+", ln)]


def changelog_entry(slug, approver, folder, ids, files_old, rows) -> str:
    out = [f"## {slug} ({date.today().isoformat()}, {approver}, {folder})", "",
           f"Reason: promoted from the approved rules of {slug}. IDs: {', '.join(ids)}.", ""]
    if rows:
        out += ["Decisions:", "| ID | Question | Decision | Rejected alternative | Why | Rules |", "|---|---|---|---|---|---|", *rows, ""]
    for name, items in files_old.items():
        out += [f"### {name}", ""]
        for rid, kind, literal in items:
            out += [f"**{rid}** ({'whole row' if kind == 'superseded' else 'rule text'}). {kind.capitalize()}.", "", f"    {literal}", ""]
    return "\n".join(out) + "\n"


def insert_entry(path: Path, entry: str) -> str:
    text = path.read_text(encoding="utf-8") if path.is_file() else "# CHANGELOG\n\n"
    m = re.search(r"^## ", text, re.M)
    pos = m.start() if m else len(text)
    head = text[:pos]
    if head and not head.endswith("\n\n"):
        head += "\n" if head.endswith("\n") else "\n\n"
    return head + entry + text[pos:]


def warnings_for(root: Path, cfg: dict) -> list[str]:
    found = []
    prd = root / cfg["prd_dir"]
    for f in sorted(prd.rglob("*.md")) if prd.is_dir() else []:
        if "amendment" in f.name.lower():
            found.append(f"amendment file {f.relative_to(root).as_posix()}: fold its rows into their step sections (P3)")
    for f in sorted((root / cfg["trd_dir"]).rglob("*.md")):
        planned = rf"^##\s+{re.escape(cfg['planned_heading'])}\b"
        if re.search(planned, f.read_text(encoding="utf-8", errors="replace"), re.M):
            found.append(f"TRD {f.relative_to(root).as_posix()} still has {cfg['planned_heading']}: merge it into the body")
    return found


def find_change(root: Path, slug: str) -> Path | None:
    base = root / "changes"
    for d in sorted(base.iterdir()) if base.is_dir() else []:
        if d.is_dir() and d.name != "archive" and (d.name == slug or d.name.split("-", 1)[-1] == slug):
            return d
    return None


def plan_edits(root, cfg, slug, files, old, approver, sources, change):
    """Every file write in memory first: the PRD rows and the CHANGELOG."""
    marker = re.compile(rf"\*\(approved[^)]*,\s*{re.escape(cfg['pending_marker'])}\)\*\s*")
    approved_ids = {i for ids in files.values() for i in ids}
    superseded = {i for i in old if i not in approved_ids}
    folder = f"changes/archive/{change.name if change else slug}"
    paths = {name: locate(root, cfg, name) for name in files}
    for name, path in paths.items():
        if path is None:
            raise PromoteError(f"{name}: PRD file not found")
    home = next(iter(paths.values()), None)
    writes: dict[Path, str] = {}
    stats = {"src": 0, "dropped": 0, "missing": []}
    files_old: dict[str, list[tuple[str, str, str]]] = {}
    prd_dir = root / cfg["prd_dir"]
    for name, path in paths.items():
        new, s, d, miss, removed = edit_rows(path.read_text(encoding="utf-8"), files[name], marker, sources,
                                             superseded if path == home else set())
        writes[path] = new
        stats["src"] += s
        stats["dropped"] += d
        stats["missing"] += miss
        items = [(i, "rewritten", f"| {i} | {old[i]} |") for i in files[name] if i in old]
        items += [(i, "superseded", removed[i]) for i in sorted(removed)]
        if items:
            files_old[path.relative_to(prd_dir).as_posix() if prd_dir in path.parents else path.name] = items
    log = prd_dir / "CHANGELOG.md"
    rows = decision_rows(change / "decisions.md") if change else []
    entry = changelog_entry(slug, approver, folder, sorted(approved_ids | superseded), files_old, rows)
    writes[log] = insert_entry(log, entry)
    return writes, stats, approved_ids, superseded, folder, log


def rebuild_html(root: Path, dry: bool) -> tuple[str, int]:
    if dry:
        return "html: would rebuild", 0
    script = Path(__file__).with_name("build_prd_html.py")
    r = subprocess.run([sys.executable, str(script), "--root", str(root)], capture_output=True, text=True,  # noqa: S603
                       check=False, cwd=root, encoding="utf-8")
    if r.returncode == 0:
        return "html: rebuilt", 0
    return f"html: ERROR {(r.stdout or r.stderr).strip()[-120:]}", 1


def promote(root: Path, slug: str, dry: bool) -> tuple[list[str], int]:
    cfg = load_config()
    state = root / ".claude" / "prd-flow" / "state" / slug
    approved = state / "approved-rules.md"
    if not approved.is_file():
        raise PromoteError(f"no {approved.relative_to(root).as_posix()}: nothing to promote for {slug}")
    files, old, approver = parse_approved(approved.read_text(encoding="utf-8"))
    sources = sources_from_trd(root, cfg)
    deliveries = state / "deliveries.md"
    if deliveries.is_file():
        sources.update(sources_from_deliveries(deliveries.read_text(encoding="utf-8")))
    change = find_change(root, slug)
    writes, stats, approved_ids, superseded, folder, log = plan_edits(root, cfg, slug, files, old, approver, sources, change)
    lines = [f"promote {slug}{' (dry-run)' if dry else ''}: {len(approved_ids)} approved, {len(superseded)} superseded",
             f"markers dropped {stats['dropped']}, sources set {stats['src']}",
             f"changelog: entry added to {log.relative_to(root).as_posix()}"]
    code = 0
    if not dry:
        for path, text in writes.items():
            path.write_text(text, encoding="utf-8", newline="\n")
    if cfg.get("html_mode") == "generated":
        line, bad = rebuild_html(root, dry)
        lines.append(line)
        code |= bad
    if change:
        lines.append(f"archive: {change.relative_to(root).as_posix()} -> {folder}")
        if not dry:
            (root / "changes" / "archive").mkdir(parents=True, exist_ok=True)
            r = run_git(root, "mv", change.relative_to(root).as_posix(), folder)
            if r.returncode != 0:
                lines.append(f"archive: ERROR {r.stderr.strip()}")
                code = 1
    else:
        lines.append("archive: WARN no changes/NNN-<slug> folder found")
    lines.append("state: cleared, deliveries.md kept")
    if not dry:
        for item in state.iterdir():
            if item.name != "deliveries.md":
                shutil.rmtree(item) if item.is_dir() else item.unlink()
        gate = Path(__file__).with_name("gate.py")
        r = subprocess.run([sys.executable, str(gate), "--final"], capture_output=True, text=True, check=False,  # noqa: S603
                           cwd=root, encoding="utf-8")
        tail = (r.stdout.strip().splitlines() or [""])[-1]
        lines.append(f"gate --final: {tail} (exit {r.returncode})")
        code |= r.returncode != 0
    else:
        lines.append("gate --final: skipped (dry-run)")
    warns = [f"WARN {m}: no Source, left as planned" for m in stats["missing"]] + [f"WARN {w}" for w in warnings_for(root, cfg)]
    room = max(MAX_LINES - len(lines), 0)
    if len(warns) > room:
        keep = max(room - 1, 0)
        warns = warns[:keep] + ([f"WARN ... {len(warns) - keep} more"] if room else [])
    return lines + warns, code


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--root")
    a = ap.parse_args()
    top = run_git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.strip()
    root = Path(a.root).resolve() if a.root else Path(top or ".")
    try:
        lines, code = promote(root, a.slug, a.dry_run)
    except PromoteError as exc:
        print(f"promote: ERROR {exc}")
        return 2
    print("\n".join(lines))
    return 1 if code else 0


if __name__ == "__main__":
    sys.exit(main())
