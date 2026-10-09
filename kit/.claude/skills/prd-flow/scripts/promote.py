"""The mechanical part of Promote: markers, Source, CHANGELOG, archive, state, final gate.

Usage: python .claude/skills/prd-flow/scripts/promote.py <slug> [--dry-run] [--root <repo>] [--hold ID[,ID] --reason TEXT]
Reads .claude/prd-flow/state/<slug>/rules.md (the state record) or, without it, approved-rules.md and changes/NNN-<slug>/decisions.md, and deliveries/*.md (or an older single deliveries.md).
Markers come from repo.md (pending_marker, planned_source). A delivered rule without a Source fails unless it is held (--hold keeps it planned, skips the archive and the final gate). After promote the state rows equal the PRD rows.
Prints at most 14 lines: on success the files changed and a ready commit message (a WARN names its `next:` dispatch); on each error `owner:` and `next:` lines. What it cannot decide (the TRD Planned merge, amendment folds) is a listed warning.
"""

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import state_record  # noqa: E402
from gate_core import load_config, needs_source, parse_supersedes  # noqa: E402

MAX_LINES = 14
OWNER_FIX = ("owner: executor fix", "next: executor fix with the printed lines, then executor close")
OWNER_FOLD = ("owner: docs fold", "next: docs fold (fix Supersedes or fold the rows), then executor close")
ID = r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d+"
SPLIT = re.compile(r"(?<!\\)\|")
SOURCE_LINE = re.compile(rf"^Source:\s*({ID}(?:\s*(?:,|\.\.)\s*(?:{ID}|\d+))*)\s*(?:->|=>|[:=])?\s*(\S.*?)\s*$", re.M)
ID_PIECE = re.compile(rf"({ID})|(,)|(\.\.)|(\d+)")


class PromoteError(Exception):
    def __init__(self, message: str, owner: str = "executor fix", next_step: str = "executor fix with the printed line, then executor close"):
        super().__init__(message)
        self.owner, self.next_step = owner, next_step


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,  # noqa: S603, S607
                          encoding="utf-8", check=False)


def parse_approved(text: str) -> tuple[dict[str, list[str]], dict[str, str], str]:
    """Approved IDs by PRD file heading, the old texts under Supersedes, and the approver."""
    files: dict[str, list[str]] = {}
    approver = "unknown"
    head = re.match(r"#\s*Approved rules\s*·\s*[^·]*·\s*[^·]*·\s*(.+)", text)
    if head:
        approver = head.group(1).strip()
    section = None
    body: list[str] = []
    for line in text.splitlines():
        h = re.match(r"#{2,3}\s+(.+?)\s*$", line)
        if h:
            section = "supersedes" if h.group(1).lower() == "supersedes" else h.group(1)
            continue
        if section == "supersedes":
            body.append(line)
        elif section and section.endswith(".md"):
            m = re.match(rf"\|\s*({ID})\s*\|", line)
            if m and not m.group(1).startswith(("Q-", "DEC-")):
                files.setdefault(section, []).append(m.group(1))
    return files, parse_supersedes(chr(10).join(body)), approver


def expand_ids(spec: str) -> list[str]:
    """`A-01`, `A-01, A-02` and `A-01..03` or `A-01..A-03` as the list of IDs."""
    ids: list[str] = []
    range_open = False
    for m in ID_PIECE.finditer(spec):
        if m.group(3):
            range_open = True
        elif m.group(1) or m.group(4):
            token = m.group(1) or m.group(4)
            if range_open and ids:
                start = re.match(r"(.*?)(\d+)$", ids[-1])
                end = int(re.search(r"(\d+)$", token).group(1))
                if start and int(start.group(2)) < end:
                    width = len(start.group(2))
                    ids += [f"{start.group(1)}{n:0{width}d}" for n in range(int(start.group(2)) + 1, end + 1)]
                range_open = False
            elif m.group(1):
                ids.append(token)
    return ids


def sources_from_deliveries(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for m in SOURCE_LINE.finditer(text):
        path = re.split(r"[,\s]", m.group(2).strip().strip("`"), maxsplit=1)[0].strip("`")
        if path and not path.startswith("::"):
            for rid in expand_ids(m.group(1)):
                found[rid] = path
    return found


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


def pending_marker(cfg: dict) -> re.Pattern:
    return re.compile(rf"\*\([^()]*,\s*{re.escape(cfg['pending_marker'])}\)\*\s*")


def edit_rows(text: str, ids: list[str], marker: re.Pattern, sources: dict[str, str], drop: set[str],
              planned: str = "planned", hold: frozenset[str] = frozenset()):
    """The new text, sources set, markers dropped, IDs without a source (code and non-code), and the removed rows by ID."""
    out, set_src, dropped, missing, own, removed = [], 0, 0, [], [], {}
    via = None
    for line in text.splitlines(keepends=True):
        parts = SPLIT.split(line.rstrip("\n"))
        cells = [c.strip().lower() for c in parts[1:-1]]
        if not line.lstrip().startswith("|"):
            via = None
        elif "id" in cells:
            via = cells.index("change via") + 1 if "change via" in cells else None
        rid = parts[1].strip() if len(parts) > 3 else ""
        if rid in drop and via is not None:
            removed[rid] = line.rstrip("\n")
            continue
        if rid in hold and rid in ids and marker.search(parts[2]):
            out.append(line)
            continue
        if rid in ids and marker.search(parts[2]):
            if rid not in sources and parts[3].strip() == planned:
                kind = parts[via].strip().lower() if via is not None and via < len(parts) else "code"
                (missing if needs_source(kind) else own).append(rid)
                out.append(line)
                continue
            parts[2] = marker.sub("", parts[2], count=1)
            dropped += 1
            if rid in sources:
                parts[3] = f" {sources[rid]} "
                set_src += 1
            line = "|".join(parts) + ("\n" if line.endswith("\n") else "")
        out.append(line)
    return "".join(out), set_src, dropped, missing, own, removed


def decision_rows(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [ln for ln in path.read_text(encoding="utf-8").splitlines() if re.match(r"\|\s*DEC-\d+", ln)]


PROMOTED = "Promoted: sources set."
OLD_BLOCK = re.compile(r"\*\*(\S+?)\*\*")


def entry_pieces(ids, files_old, rows, sources) -> tuple[list[str], dict[str, list[list[str]]]]:
    """The Decisions and Sources lines, and the old-text blocks by PRD file (one list of lines per rule)."""
    head = []
    if rows:
        head += ["Decisions:", "| ID | Question | Decision | Rejected alternative | Why | Rules |", "|---|---|---|---|---|---|", *rows, ""]
    given = [f"{rid}: {sources[rid]}" for rid in ids if rid in sources]
    head += [f"Sources: {'; '.join(given)}." if given else "Sources: none set.", PROMOTED, ""]
    blocks = {name: [[f"**{rid}** ({'whole row' if kind == 'superseded' else 'rule text'}). {kind.capitalize()}.", "", f"    {literal}", ""]
                     for rid, kind, literal in items] for name, items in files_old.items()}
    return head, blocks


def changelog_entry(slug, approver, folder, ids, files_old, rows, sources=None) -> str:
    out = [f"## {slug} ({date.today().isoformat()}, {approver}, {folder})", "",
           f"Reason: promoted from the approved rules of {slug}. IDs: {', '.join(ids)}.", ""]
    head, blocks = entry_pieces(ids, files_old, rows, sources or {})
    out += head
    for name, items in blocks.items():
        out += [f"### {name}", ""] + [ln for item in items for ln in item]
    return "\n".join(out) + "\n"


def complete_entry(text: str, slug: str, ids, files_old, rows, sources) -> str | None:
    """The CHANGELOG text with the step 5 entry of slug completed, or None when there is none or promote already did it."""
    m = re.search(rf"^## {re.escape(slug)} \(.*?(?=^## |\Z)", text, re.M | re.S)
    if not m or PROMOTED in m.group(0):
        return None
    section = m.group(0).rstrip("\n") + "\n"
    head, blocks = entry_pieces(ids, files_old, rows, sources)
    if "DEC-" in section:
        head = [ln for ln in head if not ln.startswith(("Decisions:", "| ID |", "|---", "| DEC-"))]
    for name, items in blocks.items():
        kept = []
        for item in items:
            first = OLD_BLOCK.match(item[0])
            if first and first.group(1) not in section:
                kept += item
        if not kept:
            continue
        heading = re.search(rf"^### {re.escape(name)}[ \t]*$", section, re.M)
        if heading:
            nxt = re.search(r"^### ", section[heading.end():], re.M)
            at = heading.end() + nxt.start() if nxt else len(section)
            section = section[:at].rstrip("\n") + "\n\n" + "\n".join(kept).rstrip("\n") + "\n\n" + section[at:]
        else:
            section = section.rstrip("\n") + f"\n\n### {name}\n\n" + "\n".join(kept).rstrip("\n") + "\n"
    first = re.search(r"^### ", section, re.M)
    at = first.start() if first else len(section)
    section = section[:at].rstrip("\n") + "\n\n" + "\n".join(head).rstrip("\n") + "\n\n" + section[at:]
    rest = text[m.end():].lstrip("\n")
    return text[:m.start()] + section.rstrip("\n") + "\n" + ("\n" + rest if rest else "")


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
            found.append(f"amendment file {f.relative_to(root).as_posix()}: fold its rows into their step sections (P3); next: docs fold")
    for f in sorted((root / cfg["trd_dir"]).rglob("*.md")):
        planned = rf"^##\s+{re.escape(cfg['planned_heading'])}\b"
        if re.search(planned, f.read_text(encoding="utf-8", errors="replace"), re.M):
            found.append(f"TRD {f.relative_to(root).as_posix()} still has {cfg['planned_heading']}: merge it into the body; next: executor fix")
    return found


def find_change(root: Path, slug: str) -> Path | None:
    base = root / "changes"
    for d in sorted(base.iterdir()) if base.is_dir() else []:
        if d.is_dir() and d.name != "archive" and (d.name == slug or d.name.split("-", 1)[-1] == slug):
            return d
    return None


def other_prd_files(root: Path, cfg: dict, taken: set[Path]) -> list[Path]:
    prd = root / cfg["prd_dir"]
    skip = {"CHANGELOG.md", "INDEX.md", "README.md"}
    return [f for f in sorted(prd.rglob("*.md")) if f.name not in skip and f not in taken] if prd.is_dir() else []


def plan_edits(root, cfg, slug, files, old, approver, sources, change, state, hold=frozenset(), reason=""):
    """Every file write in memory first: the PRD rows and the CHANGELOG."""
    marker = pending_marker(cfg)
    approved_ids = {i for ids in files.values() for i in ids}
    superseded = {i for i in old if i not in approved_ids}
    folder = f"changes/archive/{change.name if change else slug}"
    paths = {name: locate(root, cfg, name) for name in files}
    for name, path in paths.items():
        if path is None:
            raise PromoteError(f"{name}: PRD file not found", "docs rules", "docs rules (correct the PRD file heading in approved-rules.md), then executor close")
    log = root / cfg["prd_dir"] / "CHANGELOG.md"
    log_text = log.read_text(encoding="utf-8") if log.is_file() else ""
    entry = re.search(rf"^## {re.escape(slug)} \(.*?(?=^## |\Z)", log_text, re.M | re.S)
    done = entry is not None and PROMOTED in entry.group(0)
    writes: dict[Path, str] = {}
    stats = {"src": 0, "dropped": 0, "missing": [], "own": []}
    files_old: dict[str, list[tuple[str, str, str]]] = {}
    prd_dir = root / cfg["prd_dir"]
    targets = [(name, path, files[name]) for name, path in paths.items()]
    if superseded:
        targets += [(path.name, path, []) for path in other_prd_files(root, cfg, set(paths.values()))]
    seen: set[str] = set()
    for name, path, ids in targets:
        new, s, d, miss, own, removed = edit_rows(path.read_text(encoding="utf-8"), ids, marker, sources, superseded,
                                                  cfg["planned_source"], hold)
        if new != path.read_text(encoding="utf-8"):
            writes[path] = new
        stats["src"] += s
        stats["dropped"] += d
        stats["missing"] += miss
        stats["own"] += own
        seen |= set(removed)
        items = [(i, "rewritten", f"| {i} | {old[i]} |") for i in ids if i in old]
        items += [(i, "superseded", removed[i]) for i in sorted(removed)]
        if items:
            files_old[path.relative_to(prd_dir).as_posix() if prd_dir in path.parents else path.name] = items
    stats["unmatched"] = [] if done else sorted(superseded - seen)
    if not done:
        rows = state_record.decision_rows(state, change)
        all_ids = sorted((approved_ids - hold) | superseded)
        entry_text = complete_entry(log_text, slug, all_ids, files_old, rows, sources) or insert_entry(
            log, changelog_entry(slug, approver, folder, all_ids, files_old, rows, sources))
        if hold and PROMOTED in entry_text:
            entry_text = entry_text.replace(PROMOTED, f"{PROMOTED}\n\nHeld planned: {', '.join(sorted(hold))}. Reason: {reason}.", 1)
        writes[log] = entry_text
    return writes, stats, approved_ids, superseded, folder, log


def finish(lines: list[str], done: list[str], left: list[str]) -> tuple[list[str], int]:
    return lines + [f"done: {', '.join(done) or 'nothing'}", f"left: {', '.join(left)}; fix the cause and rerun promote", *OWNER_FIX], 1


def prd_row(text: str, rid: str) -> str | None:
    for line in text.splitlines():
        if re.match(rf"\|\s*{re.escape(rid)}\s*\|", line):
            return line
    return None


def realign_state(state: Path, writes: dict[Path, str], files: dict[str, list[str]], root: Path, cfg: dict, hold: frozenset[str]) -> None:
    rows: dict[str, str] = {}
    for name, ids in files.items():
        path = locate(root, cfg, name)
        text = writes.get(path) if path in writes else (path.read_text(encoding="utf-8") if path else "")
        for rid in ids:
            line = prd_row(text or "", rid)
            if line and rid not in hold:
                rows[rid] = line
    state_record.replace_rows(state, rows)


def promote(root: Path, slug: str, dry: bool, hold: frozenset[str] = frozenset(), reason: str = "") -> tuple[list[str], int]:
    cfg = load_config()
    state = root / ".claude" / "prd-flow" / "state" / slug
    approved_text = state_record.approved_text(state)
    if approved_text is None:
        approved = state / "approved-rules.md"
        raise PromoteError(f"no {approved.relative_to(root).as_posix()}: nothing to promote for {slug}", "user",
                           "user decides whether to restart the C5 (surveyor full) or stop; the run lost its scaffold")
    files, old, approver = parse_approved(approved_text)
    unknown = sorted(hold - {i for ids in files.values() for i in ids})
    if unknown:
        raise PromoteError(f"--hold names {', '.join(unknown)}, which is not an approved rule of {slug}", "user", "user corrects the --hold IDs")
    sources = sources_from_trd(root, cfg)
    delivery_files = sorted((state / "deliveries").glob("*.md")) if (state / "deliveries").is_dir() else []
    if (state / "deliveries.md").is_file():
        delivery_files.insert(0, state / "deliveries.md")
    for f in delivery_files:
        sources.update(sources_from_deliveries(f.read_text(encoding="utf-8")))
    change = find_change(root, slug)
    writes, stats, approved_ids, superseded, folder, log = plan_edits(root, cfg, slug, files, old, approver, sources, change, state, hold, reason)
    problems = [f"promote {slug}: ERROR {len(stats['missing'])} delivered rule(s) have no Source line: {', '.join(stats['missing'])}; "
                "add the Source or hold them with --hold ID --reason TEXT"] if stats["missing"] else []
    problems += [f"promote {slug}: ERROR superseded ID {rid} matches no row in any PRD file" for rid in stats["unmatched"]]
    if problems:
        owner = OWNER_FIX if stats["missing"] else OWNER_FOLD
        return problems + ["nothing was changed; add the Source: lines or correct Supersedes, then rerun promote", *owner], 1
    lines = [f"promote {slug}{' (dry-run)' if dry else ''}: {len(approved_ids)} approved, {len(superseded)} superseded",
             f"markers dropped {stats['dropped']}, sources set {stats['src']}",
             f"changelog: entry added to {log.relative_to(root).as_posix()}"]
    if stats["own"]:
        lines.append(f"closed by their own route (Source stays planned): {', '.join(stats['own'])}")
    if hold:
        lines.append(f"held: {', '.join(sorted(hold))} stay planned ({reason})")
    done = ["PRD rows and CHANGELOG"]
    if not dry:
        for path, text in writes.items():
            path.write_text(text, encoding="utf-8", newline="\n")
        realign_state(state, writes, files, root, cfg, hold)
    if hold:
        lines += ["archive: skipped, held rows remain", "state: kept for close", "gate --final: skipped (held rows)"]
        return lines + [f"commit: docs(prd): promote {slug} (partial)"], 0
    if change:
        lines.append(f"archive: {change.relative_to(root).as_posix()} -> {folder}")
        if not dry:
            (root / "changes" / "archive").mkdir(parents=True, exist_ok=True)
            r = run_git(root, "mv", change.relative_to(root).as_posix(), folder)
            if r.returncode != 0:
                lines.append(f"archive: ERROR {r.stderr.strip()}")
                return finish(lines, done, ["archive", "gate --final"])
    elif (root / "changes" / "archive").is_dir() and any(d.name == slug or d.name.split("-", 1)[-1] == slug for d in (root / "changes" / "archive").iterdir()):
        lines.append("archive: already archived")
    else:
        lines.append("archive: WARN no changes/NNN-<slug> folder found")
    lines.append("state: kept for close")
    if dry:
        lines.append("gate --final: skipped (dry-run)")
        code = 0
    else:
        gate = Path(__file__).with_name("gate.py")
        r = subprocess.run([sys.executable, str(gate), "--final"], capture_output=True, text=True, check=False,  # noqa: S603
                           cwd=root, encoding="utf-8")
        tail = (r.stdout.strip().splitlines() or [""])[-1]
        lines.append(f"gate --final: {tail} (exit {r.returncode})")
        code = int(r.returncode != 0)
        if code:
            lines += list(OWNER_FIX)
    if not code:
        changed = sorted(p.relative_to(root).as_posix() for p in writes)
        if change:
            changed.append(folder)
        ids = ", ".join(sorted(approved_ids | superseded))
        lines += [f"files: {', '.join(changed)}", f"commit: docs(prd): promote {slug}", f"Rules: {ids}"]
    warns = [f"WARN {w}" for w in warnings_for(root, cfg)]
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
    ap.add_argument("--hold", default="", help="comma separated IDs left planned")
    ap.add_argument("--reason", default="", help="why the held IDs stay planned")
    a = ap.parse_args()
    hold = frozenset(i.strip() for i in a.hold.split(",") if i.strip())
    if hold and not a.reason.strip():
        ap.error("--hold needs --reason")
    top = run_git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.strip()
    root = Path(a.root).resolve() if a.root else Path(top or ".")
    try:
        lines, code = promote(root, a.slug, a.dry_run, hold, a.reason.strip())
    except PromoteError as exc:
        print(f"promote: ERROR {exc}")
        print(f"owner: {exc.owner}")
        print(f"next: {exc.next_step}")
        return 2
    print("\n".join(lines))
    return 1 if code else 0


if __name__ == "__main__":
    sys.exit(main())
