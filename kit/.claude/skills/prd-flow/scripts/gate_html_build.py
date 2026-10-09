"""G29 and G32: with html_mode generated, the PRD and TRD pages equal a fresh render of their builders.

The change flow prints nothing about a stale page (check_html_flow warns only G5); the docs-html skill runs the strict check through gate.py --html.
"""

import importlib
from pathlib import Path

from gate_core import EM_DASH, err, warn

HINT = "fix: run /docs-html"
HAND_WARNING = "html_mode hand: the HTML is not checked; migrate to generated with /ai-kit update, then /docs-html"


PAGES = (("G29", "build_prd_html", "html", "prd_dir"), ("G32", "build_trd_html", "trd_html", "trd_dir"))


def html_on(cfg: dict[str, str], key: str = "html") -> bool:
    return cfg.get(key, "").lower() not in {"", "none", "no", "off"}


def pages(root: Path, cfg: dict[str, str]) -> list[tuple[str, str, str]]:
    return [(code, module, key) for code, module, key, source in PAGES
            if html_on(cfg, key) and (key == "html" or (root / cfg[source] / "README.md").exists())]


def is_generated(cfg: dict[str, str]) -> bool:
    return html_on(cfg) and cfg["html_mode"].lower() == "generated"


def check_page(root: Path, cfg: dict[str, str], code: str, module_name: str, path_key: str, strict: bool) -> None:
    report = err if strict else warn
    rel = cfg[path_key]
    try:
        current = importlib.import_module(module_name).is_current(root, cfg)
    except Exception as exc:  # noqa: BLE001
        report(code, f"cannot render the HTML ({type(exc).__name__}: {exc}); {HINT}")
        return
    if not (root / rel).exists():
        report(code, f"{rel} does not exist; {HINT}")
    elif not current:
        report(code, f"{rel} is out of date; {HINT}")


def check_page_em_dash(root: Path, cfg: dict[str, str], path_key: str) -> None:
    page = root / cfg[path_key]
    if page.exists():
        for n, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            if EM_DASH in line:
                err("G4", f"em dash in {page.relative_to(root).as_posix()}:{n}")


def check_html_flow(root: Path, cfg: dict[str, str]) -> None:
    if html_on(cfg) and not is_generated(cfg):
        warn("G5", HAND_WARNING)


def check_html_strict(root: Path, cfg: dict[str, str]) -> None:
    if not html_on(cfg):
        return
    if not is_generated(cfg):
        err("G5", "docs-html builds only html_mode generated; migrate with /ai-kit update")
        return
    for code, module, key in pages(root, cfg):
        check_page(root, cfg, code, module, key, True)
        check_page_em_dash(root, cfg, key)
