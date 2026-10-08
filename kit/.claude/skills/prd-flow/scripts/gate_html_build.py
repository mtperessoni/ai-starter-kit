"""G29: with html_mode generated, the HTML equals a fresh render of build_prd_html.py."""

import importlib
from pathlib import Path

from gate_core import err

HINT = "fix: run python .claude/skills/prd-flow/scripts/build_prd_html.py"


def check_generated(root: Path, cfg: dict[str, str]) -> None:
    try:
        current = importlib.import_module("build_prd_html").is_current(root, cfg)
    except Exception as exc:  # noqa: BLE001
        err("G29", f"cannot render the HTML ({type(exc).__name__}: {exc}); {HINT}")
        return
    if not (root / cfg["html"]).exists():
        err("G29", f"{cfg['html']} does not exist; {HINT}")
    elif not current:
        err("G29", f"{cfg['html']} is out of date; {HINT}")
