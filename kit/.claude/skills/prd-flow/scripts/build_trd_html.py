"""Build the TRD reading page from the markdown in docs/trd and docs/flow.md. Stdlib only, deterministic.

    python build_trd_html.py            write the page
    python build_trd_html.py --check    exit 1 when the page differs from a fresh render

Tabs: the README overview, one tab per area in the order of the README area table, infra, invariants, testing,
the flow diagram, then any other file of the folder. The commit and date come from git, never the clock, and
`--check` ignores them (`data-stamp`), like the PRD page.
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_prd_html as base  # noqa: E402
from build_prd_html import (  # noqa: E402
    DEFAULTS as PRD_DEFAULTS, ICON_OVERVIEW, ICON_PRD, INDEX_LINK, NUMBERED, Section, git_root, norm, read, slug, split_by,
    unstamped,
)
from prd_html_markdown import esc, parse, render_blocks  # noqa: E402

DEFAULTS = {
    "trd_dir": "docs/trd",
    "trd_html": "docs/trd/trd.html",
    "html_template": PRD_DEFAULTS["html_template"],
}
CROSS_CUTTING = ("infra", "invariants", "testing")
REQUIRED_SLOTS = {"DOC_LABEL", "SUBTITLE", "FILTER_TITLE", "SEARCH_PLACEHOLDER", "BUILDER", "VIAS_ATTR", "FILTER_ATTR"}
ICON_FLOW = '<circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="12" r="2.5"/><circle cx="6" cy="18" r="2.5"/><path d="M8.5 6H12a3 3 0 0 1 3 3M8.5 18H12a3 3 0 0 0 3-3"/>'


@dataclass
class Tab:
    key: str
    title: str
    sub: str
    icon: str
    files: list
    split: bool


def title_of(blocks: list, fallback: str) -> str:
    return next((b[2] for b in blocks if b[0] == "h" and b[1] == 1), fallback)


def area_files(trd_dir: Path) -> list[tuple[Path, str]]:
    """(file, row label) of the first TRD file linked in each README table row, in order."""
    readme = trd_dir / "README.md"
    found: list[tuple[Path, str]] = []
    if not readme.exists():
        return found
    for line in read(readme).splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        for link in INDEX_LINK.finditer(line):
            target = (trd_dir / link.group(1).partition("#")[0]).resolve()
            if target.suffix == ".md" and target.exists() and trd_dir.resolve() in target.parents and target != readme.resolve():
                found.append((target, cells[0] if cells else ""))
                break
    return found


def folder_parts(readme: Path) -> list[Path]:
    folder = readme.parent.resolve()
    linked: list[Path] = []
    for m in INDEX_LINK.finditer(read(readme)):
        path = (readme.parent / m.group(1).partition("#")[0]).resolve()
        if path.suffix == ".md" and path.exists() and path.parent == folder and path != readme.resolve() and path not in linked:
            linked.append(path)
    rest = sorted(p.resolve() for p in folder.glob("*.md") if p.resolve() not in linked and p.resolve() != readme.resolve())
    return [readme.resolve()] + linked + rest


def plan_tabs(trd_dir: Path) -> list[Tab]:
    tabs: list[Tab] = []
    placed: set[str] = {norm(trd_dir / "README.md")}
    used: set[str] = {"overview"}

    def add(path: Path, label: str, icon: str, parts: list[Path] | None = None) -> None:
        if norm(path) in placed or not path.exists():
            return
        key = slug(path.parent.name if path.name == "README.md" else path.stem)
        key = key if key not in used else f"{key}-{len(used)}"
        used.add(key)
        files = parts or [path]
        placed.update(norm(p) for p in files)
        title = title_of(parse(read(path)), path.stem.replace("-", " ").capitalize())
        tabs.append(Tab(key, title, label, icon, files, split=len(files) == 1))

    for path, label in area_files(trd_dir):
        add(path, label, ICON_PRD, folder_parts(path) if path.name == "README.md" else None)
    for name in CROSS_CUTTING:
        add(trd_dir / f"{name}.md", "", ICON_PRD)
    add(trd_dir.parent / "flow.md", "End-to-end diagram", ICON_FLOW)
    for path in sorted(trd_dir.rglob("*.md"), key=lambda p: p.as_posix()):
        add(path, "", ICON_PRD)
    return tabs


class TrdPage(base.Page):
    def __init__(self, root: Path, cfg: dict) -> None:
        self.root = root
        self.cfg = {**PRD_DEFAULTS, **DEFAULTS, **{k: v for k, v in cfg.items() if v}}
        self.prd_dir = (root / self.cfg["trd_dir"]).resolve()
        self.out = (root / self.cfg["trd_html"]).resolve()
        self.prds = []
        self.sev = {}
        self.by_path = {}
        self.plan = plan_tabs(self.prd_dir)
        self.sections = {tab.key: self.load(tab) for tab in self.plan}

    def load(self, tab: Tab) -> list[Section]:
        out: list[Section] = []
        used: set[str] = set()
        for path in tab.files:
            blocks = parse(read(path))
            head = title_of(blocks, path.stem)
            body = [b for b in blocks if not (b[0] == "h" and b[1] == 1)]
            for heading, chunk in split_by(body, 2) if tab.split else [("", body)]:
                if not chunk:
                    continue
                m = NUMBERED.match(heading) if heading else None
                title = (m.group(2) if m else heading) or head
                sid, n = f"{tab.key}-{slug(title)}", 2
                while sid in used:
                    sid, n = f"{tab.key}-{slug(title)}-{n}", n + 1
                used.add(sid)
                section = Section(path, tab.key, sid, m.group(1) if m else "", title, chunk)
                out.append(section)
                self.by_path.setdefault(norm(path), section)
        return out

    def project(self) -> str:
        if self.cfg.get("project"):
            return self.cfg["project"]
        readme = self.prd_dir / "README.md"
        title = title_of(parse(read(readme)), "") if readme.exists() else ""
        name = re.sub(r"\s*\bTRDs?$", "", title).strip()
        if not name:
            prd_title, _, _ = base.readme_parts(self.root / self.cfg["prd_dir"])
            name = re.sub(r"\s*\bPRDs?$", "", prd_title).strip()
        return name or self.root.resolve().name

    @staticmethod
    def lead_of(blocks: list, inline) -> str:
        first = next((b[1] for b in blocks if b[0] == "p"), "")
        return inline(" ".join(re.split(r"(?<=[.!?])\s+", first)[:2]))

    def overview(self) -> str:
        readme = self.prd_dir / "README.md"
        blocks = parse(read(readme)) if readme.exists() else []
        title = title_of(blocks, "")
        toc, sections, lead = [], [], ""
        for heading, body in split_by([b for b in blocks if not (b[0] == "h" and b[1] == 1)], 2):
            if not body:
                continue
            name = heading or title or "Overview"
            sid = f"v-{slug(name)}"
            inline = self.inline(readme, "overview", sid)
            lead = lead or self.lead_of(body, inline)
            toc.append(f'<li><a href="#{sid}">{inline(name)}</a></li>')
            sections.append(self.section(sid, "", name, render_blocks(body, inline, self.mx_table), inline))
        hero = self.hero("Overview", esc(title or f"{self.project()} TRD"), lead, [])
        return self.panel("overview", "Overview", toc, hero, sections, True)

    def tab_panel(self, tab: Tab) -> str:
        toc, rendered, lead = [], [], ""
        for s in self.sections[tab.key]:
            inline = self.inline(s.path, tab.key, s.sid)
            lead = lead or self.lead_of(s.blocks, inline)
            label = f"{s.num}. {s.title}" if s.num else s.title
            toc.append(f'<li><a href="#{s.sid}">{inline(label)}</a></li>')
            rendered.append(self.section(s.sid, s.num, s.title, render_blocks(s.blocks, inline, self.mx_table), inline))
        hero = self.hero("TRD", esc(tab.title), lead, [])
        return self.panel(tab.key, esc(tab.title), toc, hero, rendered, False)

    def shown(self) -> list[Tab]:
        return [t for t in self.plan if self.sections[t.key]]

    def tabs(self) -> str:
        out = [self.button("overview", ICON_OVERVIEW, "Overview", "Areas, cross-cutting maps, flow", True)]
        out += [self.button(t.key, t.icon, esc(t.title), esc(t.sub), False) for t in self.shown()]
        return "\n      ".join(out)

    def stamp_sources(self) -> list[str]:
        sources = [self.cfg["trd_dir"]]
        try:
            sources.append((self.prd_dir.parent / "flow.md").resolve().relative_to(self.root.resolve()).as_posix())
        except ValueError:
            pass
        return sources

    def labels(self) -> dict[str, str]:
        return {
            "DOC_LABEL": "TRD", "SUBTITLE": "Technical map of the code", "FILTER_TITLE": "Filter",
            "SEARCH_PLACEHOLDER": "Search this tab", "BUILDER": "build_trd_html.py",
        }

    def attrs(self) -> dict[str, str]:
        return {"VIAS_ATTR": " hidden", "FILTER_ATTR": " hidden"}

    def source_dir(self) -> str:
        return self.cfg["trd_dir"]

    def required_slots(self) -> set[str]:
        return REQUIRED_SLOTS

    def render(self) -> str:
        return self.fill("\n\n".join([self.overview()] + [self.tab_panel(t) for t in self.shown()]))


def render(root: Path, cfg: dict) -> str:
    return TrdPage(Path(root), cfg).render()


def is_current(root: Path, cfg: dict) -> bool:
    out = Path(root) / {**DEFAULTS, **cfg}["trd_html"]
    return out.exists() and unstamped(read(out)) == unstamped(render(root, cfg))


def load_cfg() -> dict:
    try:
        from gate_core import load_config
        cfg = load_config()
    except Exception:  # noqa: BLE001
        cfg = {}
    return {**DEFAULTS, **{k: v for k, v in cfg.items() if v and k in {*DEFAULTS, "project", "prd_dir"}}}


def main() -> int:
    parser = argparse.ArgumentParser(description="Render docs/trd into the HTML reading page.")
    parser.add_argument("--check", action="store_true", help="exit 1 when the page differs from a fresh render")
    parser.add_argument("--root", help="repository root (default: git top level)")
    parser.add_argument("--out", help="page path, overrides repo.md trd_html")
    parser.add_argument("--template", help="template path, overrides repo.md html_template")
    args = parser.parse_args()
    root = Path(args.root) if args.root else git_root()
    cfg = load_cfg()
    if args.out:
        cfg["trd_html"] = str(Path(args.out).resolve())
    if args.template:
        cfg["html_template"] = str(Path(args.template).resolve())
    out = root / cfg["trd_html"]
    readme = f"{cfg['trd_dir'].rstrip('/')}/README.md"
    if cfg["trd_html"].lower() in {"", "none", "no", "off"}:
        print(f"skip: trd_html is '{cfg['trd_html']}'")
        return 0
    if not (root / readme).exists():
        print(f"skip {cfg['trd_html']}: no {readme}")
        return 0
    try:
        if args.check:
            if is_current(root, cfg):
                print(f"OK {cfg['trd_html']} is current")
                return 0
            print(f"ERROR G32 {cfg['trd_html']} is out of date: run /docs-html")
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
