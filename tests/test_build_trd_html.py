"""build_trd_html.py: the generated TRD reading page, beside the PRD page, one template for both."""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "kit/.claude/skills/prd-flow/scripts"
TEMPLATE = REPO / "kit/docs/templates/prd.html"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_prd_html  # noqa: E402
import build_trd_html  # noqa: E402
from test_build_prd_html import BILLING_SUMMARY, INDEX, ORDERS, QUESTIONS, README as PRD_README, RISKS, SUMMARY  # noqa: E402

CFG = {"trd_dir": "docs/trd", "trd_html": "docs/trd/trd.html", "html_template": "docs/templates/prd.html"}

README = """# Shop TRD

One TRD per area. Load only the file of the task's area.

| Area | TRD | Folder or files | PRD sections |
|---|---|---|---|
| Billing and invoices | [billing/README.md](billing/README.md) | `src/billing/` | [16](../prd/billing/16-risks.md) |
| Shop orders | [orders.md](orders.md) | `src/orders/` | [05](../prd/shop/05-orders.md) |

Cross-cutting:

- [testing.md](testing.md): gates.
- [infra.md](infra.md): infra.
- [invariants.md](invariants.md): rules.
- [../flow.md](../flow.md): the diagram.
"""

BILLING_README = """# Billing TRD

Billing lives in `src/billing/`. Parts: [invoices](invoices.md), [retries](retries.md).
"""

ORDERS_TRD = """# Orders TRD

Orders are created in `src/orders/create.ts`.

## Entry points

`createOrder` is called by the cart. See [billing](billing/README.md).

## What must not break

An order has one item at least.
"""

FLOW = """# Flow

The end-to-end path.

```mermaid
flowchart TD
  A[Cart] --> B[Order]
```
"""


OLD_LITERALS = {
    "{{DOC_LABEL}}": "PRDs", "{{SUBTITLE}}": "PRDs and product rules", "{{FILTER_TITLE}}": "Filter rules",
    "{{SEARCH_PLACEHOLDER}}": "ID, term, limit…", "{{BUILDER}}": "build_prd_html.py", "{{VIAS_ATTR}}": "",
    "{{FILTER_ATTR}}": "",
}


def old_template() -> str:
    """HEAD's template while it predates the slots, else the current one with the literals put back."""
    shown = subprocess.run(
        ["git", "show", "HEAD:kit/docs/templates/prd.html"], cwd=REPO, capture_output=True, check=False,
    ).stdout.decode("utf-8").replace("\r\n", "\n")
    if shown and "{{BUILDER}}" not in shown:
        return shown
    text = TEMPLATE.read_text(encoding="utf-8").replace("\r\n", "\n")
    for slot, literal in OLD_LITERALS.items():
        text = text.replace(slot, literal)
    return text


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


class BuildTrdHtmlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        files = {
            "docs/trd/README.md": README,
            "docs/trd/billing/README.md": BILLING_README,
            "docs/trd/billing/retries.md": "# Retries\n\nRetries are idempotent.\n",
            "docs/trd/billing/invoices.md": "# Invoices\n\nInvoices are issued once.\n",
            "docs/trd/billing/zeta.md": "# Zeta\n\nNot linked, sorted last.\n",
            "docs/trd/orders.md": ORDERS_TRD,
            "docs/trd/infra.md": "# Infra\n\nPersistence.\n",
            "docs/trd/invariants.md": "# Invariants\n\nRules by kind of change.\n",
            "docs/trd/testing.md": "# Testing\n\nRun one file offline.\n",
            "docs/trd/extra.md": "# Extra\n\nLeft over.\n",
            "docs/flow.md": FLOW,
        }
        for rel, text in files.items():
            write(self.root, rel, text)
        (self.root / "docs/templates").mkdir(parents=True)
        shutil.copy(TEMPLATE, self.root / "docs/templates/prd.html")
        self.page = build_trd_html.render(self.root, dict(CFG))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(  # noqa: S603
            [sys.executable, str(SCRIPTS / "build_trd_html.py"), "--root", str(self.root), *args],
            capture_output=True, text=True, check=False,
        )

    def test_tab_order_readme_links_then_cross_cutting_flow_then_rest(self) -> None:
        tabs = re.findall(r'<button role="tab" data-tab="([^"]+)"', self.page)
        self.assertEqual(tabs, ["overview", "billing", "orders", "infra", "invariants", "testing", "flow", "extra"])
        panels = re.findall(r'class="panel[^"]*"[^>]*data-panel="([^"]+)"', self.page)
        self.assertEqual(panels, tabs)

    def test_folder_area_is_one_tab_with_one_section_per_file(self) -> None:
        panel = re.search(r'data-panel="billing">(.*?)(?=<div class="panel)', self.page, re.S).group(1)
        ids = re.findall(r'<section id="([^"]+)"', panel)
        self.assertEqual(ids, ["billing-billing-trd", "billing-invoices", "billing-retries", "billing-zeta"])

    def test_single_file_area_splits_by_second_level_heading(self) -> None:
        self.assertIn('<section id="orders-entry-points">', self.page)
        self.assertIn('<section id="orders-what-must-not-break">', self.page)
        self.assertIn('<a href="#orders-entry-points">Entry points</a>', self.page)

    def test_flow_keeps_mermaid_and_link_to_folder_area_crosses_tabs(self) -> None:
        self.assertIn('<pre class="mermaid">flowchart TD', self.page)
        self.assertRegex(self.page, r'<a href="#billing-billing-trd" data-go="billing">billing</a>')

    def test_trd_page_hides_the_vias_block_and_names_itself(self) -> None:
        self.assertIn("<title>Shop TRD</title>", self.page)
        self.assertIn("<code>build_trd_html.py</code>", self.page)
        self.assertIn('<div hidden>\n    <h5>Where it changes</h5>', self.page)
        self.assertNotIn("{{", self.page)

    def test_a_bare_trd_title_takes_the_project_name_from_the_prd_readme(self) -> None:
        write(self.root, "docs/trd/README.md", README.replace("# Shop TRD", "# TRD"))
        write(self.root, "docs/prd/README.md", PRD_README)
        self.assertIn("<title>Shop TRD</title>", build_trd_html.render(self.root, dict(CFG)))

    def test_deterministic(self) -> None:
        self.assertEqual(self.page, build_trd_html.render(self.root, dict(CFG)))

    def test_check_stale_then_current(self) -> None:
        self.assertEqual(self.cli("--check").returncode, 1)
        result = self.cli("--check")
        self.assertIn("ERROR G32 docs/trd/trd.html is out of date: run /docs-html", result.stdout)
        self.assertEqual(self.cli().returncode, 0)
        ok = self.cli("--check")
        self.assertEqual(ok.returncode, 0)
        self.assertIn("OK docs/trd/trd.html is current", ok.stdout)
        write(self.root, "docs/trd/infra.md", "# Infra\n\nChanged.\n")
        self.assertEqual(self.cli("--check").returncode, 1)

    def test_no_trd_readme_skips_build_and_check(self) -> None:
        (self.root / "docs/trd/README.md").unlink()
        built = self.cli()
        self.assertEqual(built.returncode, 0, built.stdout)
        self.assertIn("skip docs/trd/trd.html: no docs/trd/README.md", built.stdout)
        self.assertFalse((self.root / "docs/trd/trd.html").exists())
        self.assertEqual(self.cli("--check").returncode, 0)

    def test_check_ignores_the_stamp(self) -> None:
        self.cli()
        out = self.root / "docs/trd/trd.html"
        text = out.read_text(encoding="utf-8")
        out.write_text(re.sub(r"(<span data-stamp>)[^<]*", r"\1zzz", text), encoding="utf-8", newline="\n")
        self.assertEqual(self.cli("--check").returncode, 0)

    def test_old_template_fails_the_trd_build_with_a_clear_message(self) -> None:
        old = old_template()
        (self.root / "docs/templates/prd.html").write_text(old, encoding="utf-8", newline="\n")
        result = self.cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("copy the kit's docs/templates/prd.html", result.stdout)


class TemplateSharedByBothPagesTest(unittest.TestCase):
    def test_prd_render_is_byte_identical_with_the_previous_template(self) -> None:
        old = old_template()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel, text in {
                "docs/prd/INDEX.md": INDEX, "docs/prd/README.md": PRD_README, "docs/prd/shop/01-summary.md": SUMMARY,
                "docs/prd/shop/05-orders.md": ORDERS, "docs/prd/shop/17-open-questions.md": QUESTIONS,
                "docs/prd/billing/01-summary.md": BILLING_SUMMARY, "docs/prd/billing/16-risks.md": RISKS,
            }.items():
                write(root, rel, text)
            cfg = {"prd_dir": "docs/prd", "html": "docs/prd/prd.html", "html_template": "docs/templates/prd.html"}
            write(root, "docs/templates/prd.html", old)
            before = build_prd_html.render(root, dict(cfg))
            shutil.copy(TEMPLATE, root / "docs/templates/prd.html")
            self.assertEqual(before, build_prd_html.render(root, dict(cfg)))


if __name__ == "__main__":
    unittest.main()
