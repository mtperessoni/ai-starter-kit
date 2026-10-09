"""Build the PRD reading page from the markdown in docs/prd. Stdlib only, deterministic.

    python build_prd_html.py            write the page (repo.md `html`)
    python build_prd_html.py --check    exit 1 when the page differs from a fresh render

The commit and date in the page come from the last commit touching the PRD folder, never the clock, and
`--check` ignores them (`data-stamp`): the page is committed with the markdown, so it can only name the
commit before its own.
"""

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prd_html_markdown import (  # noqa: E402
    LEAD_ID, LOOSE_CELL, LOOSE_ID, SEVERITIES, Inline, attr, esc, parse, render_blocks, table,
)

DEFAULTS = {
    "prd_dir": "docs/prd",
    "html": "docs/prd/prd.html",
    "html_template": "docs/templates/prd.html",
    "change_via": "code, config, env, prompt, data, backend, frontend",
}
STAMP = re.compile(r"(<span data-stamp>)[^<]*(</span>)")
SLOT = re.compile(r"\{\{([A-Z_]+)\}\}")
NUMBERED = re.compile(r"^(\d{2}(?:-\d{2})?)\.?\s+(.*)$")
FILE_NUMBER = re.compile(r"^(\d{2}(?:-\d{2})?)-")
INDEX_PRD = re.compile(r"^##\s+PRD\s+(\S+)\s*·\s*([^(]+?)\s*(?:\((.*)\))?\s*$")
INDEX_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
RANK = {"high": 0, "medium": 1, "low": 2, "": 3}
ICON_PRD = '<path d="M4 19V5M4 19h16M8 15l4-4 3 3 5-6"/>'
ICON_OVERVIEW = '<circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/>'
ICON_DECISIONS = '<path d="M9 11l3 3 8-8"/><path d="M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9"/>'


@dataclass
class Section:
    path: Path
    tab: str
    sid: str
    num: str
    title: str
    blocks: list


@dataclass
class Prd:
    key: str
    number: str
    name: str
    scope: str
    letter: str
    sections: list = field(default_factory=list)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"


def norm(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def letter_of(n: int) -> str:
    return chr(ord("a") + n) if n < 26 else f"p{n}"


def index_entries(prd_dir: Path) -> list[tuple[str, str, str, list[tuple[Path, str]]]]:
    """(number, name, scope, [(file, section title)]) per PRD heading of INDEX.md, else one per folder."""
    index = prd_dir / "INDEX.md"
    entries: list = []
    if index.exists():
        for line in read(index).splitlines():
            m = INDEX_PRD.match(line.strip())
            if m:
                entries.append((m.group(1), m.group(2).strip(), (m.group(3) or "").strip(), []))
                continue
            link = INDEX_LINK.search(line) if entries and line.startswith("|") else None
            if link:
                cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
                entries[-1][3].append((prd_dir / link.group(1), cells[1] if len(cells) > 1 else ""))
    if entries:
        return entries
    folders = sorted(p for p in prd_dir.iterdir() if p.is_dir())
    return [(str(n + 1), f.name.replace("-", " ").capitalize(), "", [(p, "") for p in sorted(f.glob("*.md"))])
            for n, f in enumerate(folders)]


def load_prds(prd_dir: Path) -> list[Prd]:
    prds: list[Prd] = []
    for n, (number, name, scope, files) in enumerate(index_entries(prd_dir)):
        key = files[0][0].parent.name if files else slug(name)
        prd = Prd(key, number, name, scope, letter_of(n))
        used: set[str] = set()
        for path, title in files:
            if not path.exists():
                continue
            blocks = parse(read(path))
            num_m = FILE_NUMBER.match(path.stem)
            num = num_m.group(1) if num_m else ""
            if blocks and blocks[0][0] == "h" and blocks[0][1] <= 2:
                h = NUMBERED.match(blocks.pop(0)[2])
                num, title = (h.group(1), h.group(2)) if h else (num, title)
            base = slug(FILE_NUMBER.sub("", path.stem))
            sid = f"{prd.letter}-{base}" if base not in used else f"{prd.letter}-{base}-{num or len(used)}"
            used.add(base)
            prd.sections.append(Section(path, key, sid, num, title or path.stem, blocks))
        prds.append(prd)
    return prds


def split_by(blocks: list, level: int) -> list[tuple[str, list]]:
    parts: list[tuple[str, list]] = [("", [])]
    for b in blocks:
        if b[0] == "h" and b[1] == level:
            parts.append((b[2], []))
        else:
            parts[-1][1].append(b)
    return parts


def readme_parts(prd_dir: Path) -> tuple[str, list, list]:
    path = prd_dir / "README.md"
    if not path.exists():
        return "", [], []
    blocks = parse(read(path))
    title = next((b[2] for b in blocks if b[0] == "h" and b[1] == 1), "")
    overview, decisions = [], []
    for heading, body in split_by([b for b in blocks if not (b[0] == "h" and b[1] == 1)], 2):
        low = heading.lower()
        target = decisions if "decision" in low else overview if (low.startswith("overview") or not heading) else None
        if target is not None:
            target += [(h, body2) for h, body2 in split_by(body, 3) if h]
    return title, overview, decisions


class Page:
    def __init__(self, root: Path, cfg: dict) -> None:
        self.root = root
        self.cfg = {**DEFAULTS, **{k: v for k, v in cfg.items() if v}}
        self.prd_dir = root / self.cfg["prd_dir"]
        self.out = root / self.cfg["html"]
        self.prds = load_prds(self.prd_dir)
        self.by_path = {norm(s.path): s for p in self.prds for s in p.sections}
        self.sev = self.severities()

    def severities(self) -> dict[str, str]:
        found: dict[str, str] = {}
        for prd in self.prds:
            for s in prd.sections:
                for b in s.blocks:
                    for row in b[2] if b[0] == "table" else []:
                        m = LOOSE_CELL.match(row[0].strip()) if row else None
                        if m and (m.group(2) or "").lower() in SEVERITIES:
                            found[m.group(1)] = m.group(2).lower()
        return found

    def risk_of(self, row: list[str]) -> str:
        levels = [self.sev[i] for cell in row[1:] for i in re.findall(LOOSE_ID, cell) if i in self.sev]
        return min(levels, key=RANK.get) if levels else ""

    def inline(self, source: Path, tab: str, sid: str) -> Inline:
        def resolve(url: str) -> tuple[str, str]:
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", url):
                return url, ""
            path, _, frag = url.partition("#")
            if not path:
                return f"#{frag or sid}", ""
            target = norm(source.parent / path)
            hit = self.by_path.get(target)
            if hit:
                return f"#{hit.sid}", hit.tab if hit.tab != tab else ""
            if target in (norm(self.prd_dir / "README.md"), norm(self.out)):
                return "#overview", "overview" if tab != "overview" else ""
            rel = os.path.relpath(source.parent / path, self.out.parent).replace("\\", "/")
            return rel + (f"#{frag}" if frag else ""), ""
        return Inline(resolve)

    def section(self, sid: str, num: str, title: str, body: str, inline: Inline) -> str:
        badge = f'<span class="num">{esc(num)}</span>' if num else ""
        return f'<section id="{attr(sid)}">\n<h2>{badge}{inline(title)}</h2>\n{body}\n</section>'

    def panel(self, key: str, toc_title: str, toc: list[str], hero: str, sections: list[str], on: bool) -> str:
        items = "\n".join(toc)
        return (f'<div class="panel{"" if on else " off"}" id="panel-{attr(key)}" data-panel="{attr(key)}">\n'
                f'<aside class="toc"><h4>{toc_title}</h4><ol>\n{items}\n</ol></aside>\n<div class="doc">\n'
                f"{hero}\n\n" + "\n\n".join(sections) + "\n</div></div>")

    @staticmethod
    def hero(eyebrow: str, h1: str, text: str, stats: list[tuple[str, str, str]]) -> str:
        boxes = "".join(f'<div class="stat {c}"><b data-stat="{k}">·</b><span>{label}</span></div>' for k, label, c in stats)
        p = f"<p>{text}</p>" if text else ""
        return (f'<header class="hero"><span class="eyebrow">{eyebrow}</span><h1>{h1}</h1>{p}'
                + (f'<div class="stats">{boxes}</div>' if boxes else "") + "</header>")

    def overview(self) -> str:
        title, parts, _ = readme_parts(self.prd_dir)
        readme = self.prd_dir / "README.md"
        toc, sections, lead = [], [], ""
        for n, (heading, body) in enumerate(parts):
            m = NUMBERED.match(heading)
            num, name = (m.group(1), m.group(2)) if m else (f"{n:02d}", heading)
            sid = f"v-{slug(name)}"
            inline = self.inline(readme, "overview", sid)
            if not lead:
                first = next((b[1] for b in body if b[0] == "p"), "")
                lead = inline(" ".join(re.split(r"(?<=[.!?])\s+", first)[:2]))
            toc.append(f'<li><a href="#{sid}">{inline(name)}</a></li>')
            sections.append(self.section(sid, num, name, render_blocks(body, inline, self.mx_table), inline))
        stats = [("all", "documented rules", "acc"), ("highall", "high-level risks", "hot"), ("dec", "open decisions", "")]
        heading = esc(title or f"{self.project()} PRDs")
        return self.panel("overview", "Overview", toc, self.hero("Overview", heading, lead, stats), sections, True)

    @staticmethod
    def mx_table(header: list[str], rows: list[list[str]], inline: Inline) -> str:
        return table(header, rows, inline, mode="mx")

    def prd_panel(self, prd: Prd) -> str:
        toc, sections = [], []
        for s in prd.sections:
            inline = self.inline(s.path, prd.key, s.sid)
            label = f"{s.num}. {s.title}" if s.num else s.title
            toc.append(f'<li><a href="#{s.sid}">{inline(label)}</a></li>')
            sections.append(self.section(s.sid, s.num, s.title, render_blocks(s.blocks, inline), inline))
        scope = prd.scope[:1].upper() + prd.scope[1:] if prd.scope else ""
        scope_html = Inline(lambda u: (u, ""))(scope + ("." if scope and not scope.endswith(".") else ""))
        stats = [("rules", "rules", "acc"), ("high", "high", "hot"), ("medium", "medium", "")]
        hero = self.hero(f"PRD {esc(prd.number)}", esc(prd.name), scope_html, stats)
        return self.panel(prd.key, f"PRD {esc(prd.number)} · {esc(prd.name)}", toc, hero, sections, False)

    def decision_table(self, header: list[str], rows: list[list[str]], inline: Inline, rank: bool = False) -> str:
        lead = [LEAD_ID.match(r[0].strip()) if r else None for r in rows]
        if rows and all(lead) and not all(LOOSE_CELL.match(r[0].strip()) for r in rows):
            header = ["ID"] + header
            rows = [[m.group(1), m.group(2)] + r[1:] for m, r in zip(lead, rows)]
        elif not rows or not all(r and LOOSE_CELL.match(r[0].strip()) for r in rows):
            return table(header, rows, inline, mode="mx")
        if rank:
            rows = sorted(rows, key=lambda r: RANK[self.risk_of(r)])
        return table(header, rows, inline, mode="decision", sev_of=self.risk_of)

    def decisions(self) -> str:
        _, _, parts = readme_parts(self.prd_dir)
        readme = self.prd_dir / "README.md"
        toc, sections = [], []
        lead = "Every open question of the PRDs, ranked by the risk it blocks."
        for n, (heading, body) in enumerate(parts):
            sid = f"q-{slug(heading)}"
            inline = self.inline(readme, "decisions", sid)
            if n == 0 and len(body) == 1 and body[0][0] == "p":
                lead = inline(body[0][1])
                continue
            toc.append(f'<li><a href="#{sid}">{inline(heading)}</a></li>')
            sections.append(self.section(sid, f"{len(sections):02d}", heading,
                                         render_blocks(body, inline, self.decision_table), inline))
        for prd in self.prds:
            for s in (s for s in prd.sections if s.path.stem.endswith("open-questions")):
                sid = f"q-all-{s.sid}"
                inline = self.inline(s.path, "decisions", sid)
                title = f"All open questions · PRD {prd.number} {prd.name}"
                source = f'<a href="#{s.sid}" data-go="{attr(prd.key)}">{esc(s.num)}. {esc(s.title)}</a>'
                intro = f'<div class="explain"><p>Ranked by the risk each question blocks. Source: {source}.</p></div>'
                tables = [self.decision_table(b[1], b[2], inline, rank=True) for b in s.blocks if b[0] == "table"]
                toc.append(f'<li><a href="#{sid}">{esc(title)}</a></li>')
                sections.append(self.section(sid, f"{len(sections):02d}", title, intro + "\n" + "\n".join(tables), inline))
        hero = self.hero("Open decisions", "What needs an owner now", lead, [])
        return self.panel("decisions", "Open decisions", toc, hero, sections, False)

    def project(self) -> str:
        if self.cfg.get("project"):
            return self.cfg["project"]
        title, _, _ = readme_parts(self.prd_dir)
        name = re.sub(r"\s+PRDs?$", "", title).strip()
        return name or self.root.resolve().name

    @staticmethod
    def button(key: str, icon: str, title: str, sub: str, on: bool) -> str:
        return (f'<button role="tab" data-tab="{attr(key)}" aria-selected="{str(on).lower()}"><span class="ic">'
                f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
                f'stroke-linejoin="round">{icon}</svg></span><span><span class="t">{title}</span><span class="s">{sub}</span>'
                f'</span><span class="n" data-n="{attr(key)}"></span></button>')

    def tabs(self) -> str:
        button = self.button
        out = [button("overview", ICON_OVERVIEW, "Overview", "Journey, findings, how to change", True)]
        out += [button(p.key, ICON_PRD, f"PRD {esc(p.number)} · {esc(p.name)}", esc(p.scope[:1].upper() + p.scope[1:]), False)
                for p in self.prds]
        out.append(button("decisions", ICON_DECISIONS, "Open decisions", "Ranked by risk", False))
        return "\n      ".join(out)

    def vias(self, body: str) -> str:
        used = set(re.findall(r'<tr data-via="([^"]+)"', body))
        order = [v.strip() for v in self.cfg["change_via"].split(",") if v.strip()]
        names = [v for v in order if v in used] + sorted(used - set(order))
        chips = ['<button class="all" data-via="" aria-pressed="true"><span class="dot d-all"></span>All</button>']
        chips += [f'<button data-via="{attr(v)}" aria-pressed="false"><span class="dot d-{attr(v)}"></span>'
                  f"{esc(v.capitalize())}</button>" for v in names]
        return "\n      ".join(chips)

    def stamp_sources(self) -> list[str]:
        return [self.cfg["prd_dir"]]

    def labels(self) -> dict[str, str]:
        return {
            "DOC_LABEL": "PRDs", "SUBTITLE": "PRDs and product rules", "FILTER_TITLE": "Filter rules",
            "SEARCH_PLACEHOLDER": "ID, term, limit…", "BUILDER": "build_prd_html.py",
        }

    def attrs(self) -> dict[str, str]:
        return {"VIAS_ATTR": "", "FILTER_ATTR": ""}

    def source_dir(self) -> str:
        return self.cfg["prd_dir"]

    def required_slots(self) -> set[str]:
        return set()

    def stamp(self) -> tuple[str, str]:
        spec = self.stamp_sources()
        try:
            spec.append(":(exclude)" + self.out.resolve().relative_to(self.root.resolve()).as_posix())
        except ValueError:
            pass
        try:
            out = subprocess.run(  # noqa: S603
                ["git", "log", "-1", "--format=%h %cs", "--", *spec],  # noqa: S607
                cwd=self.root, capture_output=True, text=True, encoding="utf-8", check=False,
            ).stdout.split()
        except OSError:
            out = []
        return (out[0], out[1]) if len(out) == 2 else ("uncommitted", "not committed")

    def render(self) -> str:
        panels = "\n\n".join([self.overview()] + [self.prd_panel(p) for p in self.prds] + [self.decisions()])
        return self.fill(panels)

    def fill(self, panels: str) -> str:
        template_path = Path(self.cfg["html_template"])
        template = read(template_path if template_path.is_absolute() else self.root / template_path)
        commit, date = self.stamp()
        values = {
            "PROJECT": esc(self.project()), "TABS": self.tabs(), "VIAS": self.vias(panels), "PANELS": panels,
            "REPO": esc(self.root.resolve().name), "COMMIT": esc(commit), "DATE": esc(date),
            "PRD_DIR": esc(self.source_dir().rstrip("/") + "/"),
            **{k: esc(v) for k, v in self.labels().items()}, **self.attrs(),
        }
        absent = sorted(k for k in self.required_slots() if "{{" + k + "}}" not in template)
        if absent:
            raise ValueError(f"template {template_path} predates this page (slots absent: {absent}); "
                             "copy the kit's docs/templates/prd.html")
        missing = sorted(set(SLOT.findall(template)) - set(values))
        if missing or "{{PANELS}}" not in template:
            raise ValueError(f"template {template_path} predates the generated build (slots: {missing or 'PANELS absent'}); "
                             "copy the kit's docs/templates/prd.html")
        return SLOT.sub(lambda m: values[m.group(1)], template)


def render(root: Path, cfg: dict) -> str:
    return Page(Path(root), cfg).render()


def unstamped(text: str) -> str:
    return STAMP.sub(r"\1\2", text.replace("\r\n", "\n"))


def is_current(root: Path, cfg: dict) -> bool:
    out = Path(root) / {**DEFAULTS, **cfg}["html"]
    return out.exists() and unstamped(read(out)) == unstamped(render(root, cfg))


def load_cfg() -> dict:
    try:
        from gate_core import load_config
        cfg = load_config()
    except Exception:  # noqa: BLE001
        cfg = {}
    return {**DEFAULTS, **cfg}


def git_root() -> Path:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)  # noqa: S603,S607
    return Path(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip() else Path.cwd()


def main() -> int:
    parser = argparse.ArgumentParser(description="Render docs/prd into the HTML reading page.")
    parser.add_argument("--check", action="store_true", help="exit 1 when the page differs from a fresh render")
    parser.add_argument("--root", help="repository root (default: git top level)")
    parser.add_argument("--out", help="page path, overrides repo.md html")
    parser.add_argument("--template", help="template path, overrides repo.md html_template")
    args = parser.parse_args()
    root = Path(args.root) if args.root else git_root()
    cfg = load_cfg()
    if args.out:
        cfg["html"] = str(Path(args.out).resolve())
    if args.template:
        cfg["html_template"] = str(Path(args.template).resolve())
    out = root / cfg["html"]
    try:
        if args.check:
            if is_current(root, cfg):
                print(f"OK {cfg['html']} is current")
                return 0
            print(f"ERROR G29 {cfg['html']} is out of date: run python {Path(__file__).name} and commit the page")
            return 1
        page = render(root, cfg)
    except (ValueError, OSError) as exc:
        print(f"ERROR {exc}")
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8", newline="\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
