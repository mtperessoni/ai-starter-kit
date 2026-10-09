"""gate.py --trd: TRD paths, symbols and IDs against the tracked files (G23 to G26)."""

import re
from pathlib import Path

from gate_core import SEPARATOR, cells, errors, git, err, warn, warnings
from gate_output import park

EXTENSIONS = {
    "ts", "tsx", "js", "jsx", "mjs", "cjs", "py", "md", "json", "yml", "yaml", "sql", "css", "html", "sh", "toml",
    "go", "rs", "java", "kt", "rb", "php", "cs", "swift", "txt", "env", "mdx", "scss", "vue", "svelte", "ini", "cfg",
}
TICKS = re.compile(r"`([^`\n]+)`")
EXT = re.compile(r"\.([A-Za-z0-9]+)$")
IDENT = re.compile(r"[A-Za-z_$][\w$]*")
MAX_ROW_FILES = 20


class Tracked:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.files = [f for f in git(root, "-c", "core.quotepath=false", "ls-files", "-co", "--exclude-standard", "-z").split("\0") if f]
        self.tops = {f.split("/")[0] for f in self.files if "/" in f}
        self.texts: dict[str, str] = {}

    def matches(self, token: str) -> list[str]:
        if token.endswith("/") and "*" not in token:
            return [f for f in self.files if f.startswith(token) or ("/" + token) in f]
        pattern = re.escape(token).replace(r"\*\*/", "(.*/)?").replace(r"\*\*", ".*").replace(r"\*", ".*")
        rx = re.compile(r"(^|/)" + pattern + ("" if token.endswith("/") else "(/|$)"))
        return [f for f in self.files if rx.search(f)]

    def ignored(self, token: str) -> bool:
        return bool(git(self.root, "check-ignore", token.rstrip("/")).strip())

    def text(self, rel: str) -> str:
        if rel not in self.texts:
            try:
                self.texts[rel] = (self.root / rel).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                self.texts[rel] = ""
        return self.texts[rel]


def path_of(token: str, tracked: Tracked) -> str:
    tok = token.split("::")[0].strip()
    while tok.startswith(("./", ".../", "../")):
        tok = tok.split("/", 1)[1]
    if not tok or "..." in tok or tok.startswith(("/", "~", "http", "@")) or re.search(r"[\s<>{}()$|,;:=?#]", tok.replace("[", "").replace("]", "")):
        return ""
    ext = EXT.search(tok.rstrip("/"))
    has_ext = bool(ext) and ext.group(1).lower() in EXTENSIONS and not tok.endswith("/")
    if "/" in tok:
        first = tok.split("/")[0]
        return tok if has_ext or tok.endswith("/") or first in tracked.tops else ""
    return tok if has_ext and not tok.startswith(".") else ""


def trd_files(root: Path, trd_dir: str) -> list[Path]:
    return sorted((root / trd_dir).rglob("*.md")) if (root / trd_dir).is_dir() else []


def strip_planned(lines: list[str], heading: str) -> list[str]:
    kept, skipping, fenced = [], False, False
    for line in lines:
        if line.startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith("## "):
            skipping = line[3:].strip().lower().startswith(heading.lower())
        if not skipping:
            kept.append(line)
    return kept


def check_row(rel: str, header: list[str], row: list[str], tracked: Tracked, g23: set[str]) -> None:
    low = [h.lower() for h in header]
    row = row + [""] * (len(header) - len(row))
    if "changes or creates" in low and "creates" in row[low.index("changes or creates")].lower():
        return
    paths = []
    for tok in TICKS.findall(row[0]):
        p = path_of(tok, tracked)
        if p:
            paths.append(p)
    files: list[str] = []
    for p in paths:
        found = tracked.matches(p)
        if not found and p not in g23 and not tracked.ignored(p):
            g23.add(p)
            err("G23", f"{rel}: `{p}` matches no tracked file")
        files.extend(found)
    if not files or len(set(files)) > MAX_ROW_FILES:
        return
    blob = "\n".join(tracked.text(f) for f in sorted(set(files)))
    where = ", ".join(paths)
    for name in ("main symbols", "symbols"):
        if name in low:
            for tok in TICKS.findall(row[low.index(name)]):
                m = IDENT.match(tok.strip())
                if m and not re.search(r"(?<![\w$])" + re.escape(m.group(0)) + r"(?![\w$])", blob):
                    warn("G24", f"{rel}: symbol `{m.group(0)}` not found in {where}")
            break


def check_file(root: Path, f: Path, cfg: dict[str, str], tracked: Tracked) -> None:
    rel = f.relative_to(root).as_posix()
    text = f.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    budget = int(cfg["trd_budget_lines"])
    if len(lines) > budget:
        warn("G26", f"{rel} has {len(lines)} lines, over trd_budget_lines {budget}; split it into docs/trd/<area>/<part>.md")
    g23: set[str] = set()
    header: list[str] = []
    for line in strip_planned(lines, cfg["planned_heading"]):
        if not line.startswith("|"):
            header = []
            for tok in TICKS.findall(line):
                p = path_of(tok, tracked)
                if p and not tracked.matches(p) and p not in g23 and not tracked.ignored(p):
                    g23.add(p)
                    err("G23", f"{rel}: `{p}` matches no tracked file")
            continue
        if SEPARATOR.match(line):
            continue
        row = cells(line.strip().strip("|"))
        if not header:
            header = row
        else:
            check_row(rel, header, row, tracked, g23)


def cites_diff(line: str, diff: set[str]) -> bool:
    m = re.search(r"`([^`]+)` matches no tracked file", line)
    if not m or not line.startswith("ERROR"):
        return False
    cited = m.group(1).rstrip("/")
    return any(d == cited or d.startswith(cited + "/") or d.endswith("/" + cited) for d in diff)


def check_trd(root: Path, cfg: dict[str, str], trd_dir: str, changed: set[str] | None = None, diff: set[str] | None = None) -> None:
    tracked = Tracked(root)
    for f in trd_files(root, trd_dir):
        rel = f.relative_to(root).as_posix()
        if changed is None or rel in changed:
            check_file(root, f, cfg, tracked)
            continue
        e, w = len(errors), len(warnings)
        check_file(root, f, cfg, tracked)
        found = [*errors[e:], *warnings[w:]]
        kept = [x for x in errors[e:] if cites_diff(x, diff or set())]
        del errors[e:], warnings[w:]
        errors.extend(kept)
        park([x for x in found if x not in kept], rel)
