"""Deterministic, read-only sweep and functional proof for prd-flow (WF75).

Run from the repository root:
  python .claude/skills/prd-flow/scripts/prd_sweep.py --ids ID[,ID...] [--terms "w1,w2"] [--out FILE] [--root DIR]

Collects the mechanical part of the survey (K01, K02, K05, K06, K11, K12, K14 candidates and F1, F2); the judgment
(K14 verdicts, F3) stays with the agent.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from fnmatch import fnmatchcase
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_core as core  # noqa: E402

ABSOLUTE = re.compile(
    r"\b(always|every|never|all|any|sempre|nunca|todo|toda|todos|todas|cada|qualquer|nenhum)\b|\d", re.I
)
ID_ANY = re.compile(core.ID)
DEFINITION = re.compile(r"\b(def|class|function|const|let|var|fn|func|type|interface|struct|enum)\s+(\w+)")
MD_PATH = re.compile(r"[\w./-]+\.md")
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", "target", ".next", "vendor"}

CAPS = {"rules": 12, "cited": 20, "same": 30, "rows": 40, "files": 8, "unconditional": 20, "history": 3,
        "active": 15, "tests": 15, "code": 14, "callers": 5}


def config(root: Path) -> dict[str, str]:
    cfg = dict(core.DEFAULTS)
    here = Path(__file__).resolve().parents[1] / "repo.md"
    for repo in (root / ".claude" / "skills" / "prd-flow" / "repo.md", here):
        if not repo.is_file():
            continue
        text = repo.read_text(encoding="utf-8")
        block = re.search(r"^## Gate config\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
        if block:
            for line in block.group(1).splitlines():
                m = re.match(r"^\|\s*([a-z_]+)\s*\|\s*(.*?)\s*\|\s*$", line)
                if m and m.group(1) in core.DEFAULTS:
                    cfg[m.group(1)] = m.group(2).strip("` ")
            break
    return cfg


def matches(relpath: str, patterns: list[str]) -> bool:
    candidate = "/" + relpath
    return any(fnmatchcase(relpath, p) or fnmatchcase(candidate, "*/" + p.removeprefix("**/")) for p in patterns)


def walk(root: Path, ignore: list[str]) -> list[str]:
    out = subprocess.run(  # noqa: S603
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],  # noqa: S607
        cwd=root, capture_output=True, check=False,
    )
    if out.returncode == 0 and out.stdout and (root / ".git").exists():
        names = {n for n in out.stdout.decode("utf-8", errors="replace").split(chr(0)) if n}
        return sorted(n for n in names if (root / n).is_file() and not matches(n, ignore))
    found = []
    for dirpath, dirs, files in os.walk(root):
        base = Path(dirpath).relative_to(root).as_posix()
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not matches(f"{base}/{d}/x".lstrip("./"), ignore)]
        found += [f"{base}/{f}".removeprefix("./") for f in files]
    return sorted(f for f in found if not matches(f, ignore))


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


class Rule:
    def __init__(self, rid: str, rel: str, line: int, text: str, rule: str, source: str, table: int) -> None:
        self.rid, self.rel, self.line, self.text, self.rule, self.source, self.table = rid, rel, line, text, rule, source, table


def parse_rules(root: Path, cfg: dict[str, str]) -> dict[str, Rule]:
    prd = root / cfg["prd_dir"]
    via = cfg["via_header"].lower()
    rules: dict[str, Rule] = {}
    for path in sorted(prd.glob(cfg["prd_glob"])):
        rel = core_rel(path, root)
        header: list[str] | None = None
        table = 0
        for no, line in enumerate(read_lines(path), 1):
            if not line.startswith("|"):
                header = None
                continue
            if core.SEPARATOR.match(line):
                continue
            row = core.ROW.match(line)
            if header is None:
                cols = [c.lower() for c in core.cells(line.strip().strip("|"))]
                header = cols if via in cols else []
                table = no
                continue
            if not row or not header:
                continue
            body = core.cells(row.group(2))
            idx = header.index("rule") - 1 if "rule" in header else 0
            sidx = header.index("source") - 1 if "source" in header else -1
            rule = body[idx] if 0 <= idx < len(body) else ""
            source = body[sidx].strip("` ") if 0 <= sidx < len(body) else ""
            rules.setdefault(row.group(1), Rule(row.group(1), rel, no, line.strip(), rule, source, table))
    return rules


def core_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def cap(items: list[str], limit: int) -> list[str]:
    if len(items) <= limit:
        return items
    return [*items[:limit], f"... {len(items) - limit} more"]


def id_re(rid: str) -> re.Pattern[str]:
    return re.compile(r"(?<![\w-])" + re.escape(rid) + r"(?!\w)")


def rule_part(line: str) -> str:
    m = core.ROW.match(line.strip())
    return ID_ANY.sub(" ", core.cells(m.group(2))[0] if m else line)


def unconditional(text: str) -> bool:
    return bool(ABSOLUTE.search(rule_part(text)))


def doc_files(root: Path, cfg: dict[str, str]) -> list[Path]:
    prd = root / cfg["prd_dir"]
    skip = {"INDEX.md", "CHANGELOG.md", "README.md"}
    return sorted(p for p in prd.rglob("*.md") if p.name not in skip)


def sweep_cited(root: Path, cfg: dict[str, str], ids: list[str], rules: dict[str, Rule]) -> list[tuple[str, str]]:
    out = []
    for path in doc_files(root, cfg):
        rel = core_rel(path, root)
        for no, line in enumerate(read_lines(path), 1):
            for rid in ids:
                own = rules.get(rid)
                if id_re(rid).search(line) and not (own and own.rel == rel and own.line == no):
                    out.append((rid, f"{rel}:{no}: {line.strip()}"))
    return out


def sweep_same_table(ids: list[str], rules: dict[str, Rule]) -> list[str]:
    seen: set[tuple[str, int]] = set()
    out = []
    for rid in ids:
        r = rules.get(rid)
        if not r or (r.rel, r.table) in seen:
            continue
        seen.add((r.rel, r.table))
        for other in rules.values():
            if other.rel == r.rel and other.table == r.table and other.rid not in ids:
                out.append(f"- {r.rel}:{other.line}: {other.rid} {other.rule[:80]}")
    return out


def sweep_candidates(root: Path, cfg: dict[str, str], terms: list[str], rules: dict[str, Rule]) -> tuple[list[str], list[str]]:
    index = read_lines(root / cfg["prd_dir"] / "INDEX.md")
    lines, files = [], []
    for no, line in enumerate(index, 1):
        if any(t in line.lower() for t in terms):
            lines.append(f"- INDEX.md:{no}: {line.strip()}")
            for ref in MD_PATH.findall(line):
                target = (root / cfg["prd_dir"] / ref)
                rel = core_rel(target, root) if target.is_file() else None
                if rel and rel not in files:
                    files.append(rel)
    rows = []
    for rel in files[: CAPS["files"]]:
        for r in rules.values():
            if r.rel == rel and any(t in r.text.lower() for t in terms):
                rows.append(f"- {r.rel}:{r.line}: {r.text}")
    out = [*cap(lines, CAPS["rows"]), *(f"- file: {f}" for f in files[: CAPS["files"]])]
    if len(files) > CAPS["files"]:
        out.append(f"... {len(files) - CAPS['files']} more")
    return out, cap(rows, CAPS["rows"])


def sweep_history(root: Path, cfg: dict[str, str], ids: list[str]) -> list[str]:
    path = root / cfg["prd_dir"] / "CHANGELOG.md"
    if not path.is_file():
        return []
    heading, entries = "", []
    for no, line in enumerate(read_lines(path), 1):
        if line.startswith("#"):
            heading = line.lstrip("# ").strip()
        entries.append((no, heading, line))
    out = []
    for rid in ids:
        hits = [f"- {rid}: CHANGELOG.md:{no} [{h}] {ln.strip()}" for no, h, ln in entries if id_re(rid).search(ln)]
        out.extend(cap(hits, CAPS["history"]))
    return out


def scan(root: Path, files: list[str], ids: list[str]) -> list[str]:
    out = []
    for rel in files:
        try:
            lines = read_lines(root / rel)
        except OSError:
            continue
        for rid in ids:
            rx = id_re(rid)
            for no, line in enumerate(lines, 1):
                if rx.search(line):
                    out.append(f"- {rid}: {rel}:{no}")
                    break
    return out


def split_source(source: str) -> tuple[str, str]:
    path, _, symbol = source.partition("::")
    return path.strip(), symbol.strip()


def callers(root: Path, files: list[str], symbol: str, defining: tuple[str, ...]) -> list[str]:
    word = re.compile(r"(?<!\w)" + re.escape(symbol.split(".")[-1]) + r"(?!\w)")
    out = []
    for rel in files:
        for no, line in enumerate(read_lines(root / rel), 1):
            if not word.search(line):
                continue
            m = DEFINITION.search(line)
            if m and m.group(2) == symbol.split(".")[-1]:
                continue
            out.append(f"{rel}:{no}")
    return out


def sweep_code(root: Path, ak: dict, cfg: dict[str, str], ids: list[str], rules: dict[str, Rule], listing: list[str]) -> list[str]:
    exts = set(ak.get("code_extensions", []))
    prefixes = ["" if s in (".", "./", "") else s.strip("/") + "/" for s in ak.get("source_dirs", ["src"])]
    ignore, tests = ak.get("ignore", []), ak.get("test_patterns", [])
    src = [r for r in listing if Path(r).suffix in exts and any(r.startswith(p) for p in prefixes)
           and not matches(r, ignore) and not matches(r, tests)]
    out = []
    for rid in ids:
        r = rules.get(rid)
        if not r:
            continue
        if r.source.lower() == cfg["planned_source"].lower() or not r.source:
            out.append(f"- {rid}: planned")
            continue
        path, symbol = split_source(r.source)
        target = root / path
        if not target.is_file():
            out.append(f"- {rid}: missing: {path} not found")
            continue
        body = target.read_text(encoding="utf-8", errors="replace")
        if symbol and not re.search(r"(?<!\w)" + re.escape(symbol.split(".")[-1]) + r"(?!\w)", body):
            out.append(f"- {rid}: missing: {path}::{symbol} not found")
            continue
        if not symbol:
            out.append(f"- {rid}: found {path}")
            out.append(f"  F3: read {path}")
            continue
        found = callers(root, src, symbol, (path,))
        if not found:
            out.append(f"- {rid}: not wired: no caller of {path}::{symbol} outside tests")
        else:
            out.append(f"- {rid}: found {path}::{symbol}, callers: {', '.join(found[: CAPS['callers']])}"
                       + (f" ... {len(found) - CAPS['callers']} more" if len(found) > CAPS["callers"] else ""))
            out.append(f"  F3: read {path}::{symbol}")
    return cap(out, CAPS["code"] * 2)


def build(root: Path, ids: list[str], terms: list[str]) -> tuple[list[str], dict[str, int]]:
    cfg = config(root)
    ak_path = root / "ai-kit.json"
    ak = json.loads(ak_path.read_text(encoding="utf-8")) if ak_path.is_file() else {}
    rules = parse_rules(root, cfg)
    listing = walk(root, ak.get("ignore", []))
    tests = ak.get("test_patterns", [])
    ignore = ak.get("ignore", [])
    exts = set(ak.get("code_extensions", []))
    test_listing = [r for r in listing if Path(r).suffix in exts and matches(r, tests) and not matches(r, ignore)]
    changes = [r for r in listing if r.startswith("changes/") and not r.startswith("changes/archive/") and r.endswith(".md")]

    rule_lines = []
    for rid in ids:
        r = rules.get(rid)
        rule_lines.append(f"- {r.rel}:{r.line}: {r.text}" if r else f"- {rid}: not found in {cfg['prd_dir']}")
    cited = sweep_cited(root, cfg, ids, rules)
    cited_lines = [f"- {rid} <- {text}" for rid, text in cited]
    same = sweep_same_table(ids, rules)
    cand_idx, cand_rows = sweep_candidates(root, cfg, terms, rules) if terms else ([], [])
    pool = [f"- {r.rel}:{r.line}: {r.text}" for rid in ids if (r := rules.get(rid)) and unconditional(r.rule)]
    pool += [f"- {text}" for _, text in cited if unconditional(text.split(": ", 1)[-1])]
    pool += [ln for ln in same if unconditional(ln.split(" ", 3)[-1])]
    pool += [ln for ln in cand_rows if unconditional(ln.split(": ", 1)[-1])]
    pool = list(dict.fromkeys(pool))
    history = sweep_history(root, cfg, ids)
    active = scan(root, changes, ids)
    tested = scan(root, test_listing, ids)
    code = sweep_code(root, ak, cfg, ids, rules, listing)

    sections = [
        ("Rules", cap(rule_lines, CAPS["rules"])),
        ("Cited by", cap(cited_lines, CAPS["cited"])),
        ("Same table", cap(same, CAPS["same"])),
        ("Candidates", [*cand_idx, *cand_rows]),
        ("Unconditional", cap(pool, CAPS["unconditional"])),
        ("History", cap(history, CAPS["same"])),
        ("Active changes", cap(active, CAPS["active"])),
        ("Tests", cap(tested, CAPS["tests"])),
        ("Code", code),
    ]
    out, counts = ["# Sweep", ""], {}
    for name, lines in sections:
        out += [f"## {name}", *(lines or ["- none"]), ""]
        counts[name] = len([ln for ln in lines if not ln.startswith(("...", "  F3"))])
    return out, counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ids", required=True)
    ap.add_argument("--terms", default="")
    ap.add_argument("--out")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    ids = [i.strip() for i in args.ids.split(",") if i.strip()]
    terms = [t.strip().lower() for t in args.terms.split(",") if t.strip()]
    cfg = config(root)
    if not ids or not (root / cfg["prd_dir"] / "INDEX.md").is_file():
        print(f"prd_sweep: need --ids and {cfg['prd_dir']}/INDEX.md under {root}", file=sys.stderr)
        return 2
    lines, counts = build(root, ids, terms)
    report = "\n".join(lines).rstrip() + "\n"
    sys.stdout.reconfigure(encoding="utf-8")
    summary = ["sweep: " + ", ".join(f"{k} {v}" for k, v in list(counts.items())[:5]),
               "sweep: " + ", ".join(f"{k} {v}" for k, v in list(counts.items())[5:])]
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        summary.append(f"written: {out}")
    else:
        sys.stdout.write(report)
        summary.append("written: stdout")
    print("\n".join(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
