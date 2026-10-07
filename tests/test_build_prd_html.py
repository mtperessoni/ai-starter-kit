"""build_prd_html.py: the generated PRD reading page (K-50, K-60, K-61)."""

import html
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

import build_prd_html  # noqa: E402

GATE_ROW = re.compile(r"<tr[^>]*>\s*<td>([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d+[a-z]?)</td>\s*<td[^>]*>(.*?)</td>", re.S)

INDEX = """# PRD index

Entry point for agents.

## PRD 1 · Shop (orders and carts)
| File | Section | IDs | TRD |
|---|---|---|---|
| [01-summary.md](shop/01-summary.md) | Summary |  |  |
| [05-orders.md](shop/05-orders.md) | Step 1 · Orders | ORD-01..03 |  |
| [17-open-questions.md](shop/17-open-questions.md) | Open questions | Q1..Q2 |  |

## PRD 2 · Billing (invoices)
| File | Section | IDs | TRD |
|---|---|---|---|
| [01-summary.md](billing/01-summary.md) | Summary |  |  |
| [16-risks.md](billing/16-risks.md) | Risks | R2-01..02 |  |
"""

README = """# Shop PRDs

Overview for people. Agents start at [INDEX.md](INDEX.md).

## Overview

### 00. What the product is

Shop sells things online. It has two PRDs and a long tail of rules.

### 01. How to read this document

Every behavior is a row with an ID (`ORD-01`).

## Open decisions

### How to use this tab

Each row is a decision nobody has made.

### Decide now

| Question | Default adopted | Blocks |
|---|---|---|
| Q1 Should orders expire? | No | R2-01 |
"""

SUMMARY = """## 01. Summary

The shop takes **orders** from customers.

**Read next.** Orders [05](05-orders.md), billing risks [16](../billing/16-risks.md).
"""

ORDERS = """## 05. Step 1 · Orders

An order is a cart the customer confirmed. It holds *at least* one item.

A customer confirms a cart of 3 items → the order is created → the cart empties.

> [!IMPORTANT]
> Billing starts after this step ([summary](01-summary.md)).

> [!CAUTION]
> **An empty cart can be confirmed *(checked in code)***
>
> The button stays enabled (`src/cart.ts::confirm`).

```mermaid
flowchart TD
  A[Cart] -->|confirm| B{Valid?}
```

```text
raw <block> & code
```

| ID | Rule | Source | Change via | Example |
|---|---|---|---|---|
| ORD-01 | *(approved 2026-10-07, pending code)* An order needs `items.length >= 1`. | planned | code | Cart of 0 items → refused |
| ORD-02 | The total uses <script>alert(1)</script> \\| tax. | src/order.ts::total | config | |

| ID | Rule | Source | Change via |
|---|---|---|---|
| ORD-03 | Orders are listed. | src/list.ts | frontend |

- one
- two
  - nested
"""

QUESTIONS = """## 17. Open questions

| ID | Question | Default adopted | Blocks |
|---|---|---|---|
| Q1 | Should orders expire? | No | R2-01 |
| Q2 | Should carts merge? | No | no |
"""

BILLING_SUMMARY = """## 01. Summary

Billing issues invoices. See [orders](../shop/05-orders.md).
"""

RISKS = """## 16. Risks

| Risk | Scenario | Mitigation |
|---|---|---|
| R2-01 · high | An invoice is sent twice | Idempotency key |
| R2-02 · low | A late invoice | Retry |
"""

CFG = {
    "prd_dir": "docs/prd",
    "html": "docs/prd/prd.html",
    "html_template": "docs/templates/prd.html",
    "change_via": "code, config, env, prompt, data, backend, frontend",
}


def body_of(page: str) -> str:
    page = re.sub(r"<style>.*?</style>", "", page, flags=re.S)
    return re.sub(r"<script.*?</script>", "", page, flags=re.S)


class BuildPrdHtmlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        files = {
            "docs/prd/INDEX.md": INDEX,
            "docs/prd/README.md": README,
            "docs/prd/shop/01-summary.md": SUMMARY,
            "docs/prd/shop/05-orders.md": ORDERS,
            "docs/prd/shop/17-open-questions.md": QUESTIONS,
            "docs/prd/billing/01-summary.md": BILLING_SUMMARY,
            "docs/prd/billing/16-risks.md": RISKS,
        }
        for rel, text in files.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
        (self.root / "docs/templates").mkdir(parents=True)
        shutil.copy(TEMPLATE, self.root / "docs/templates/prd.html")
        self.page = build_prd_html.render(self.root, dict(CFG))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(  # noqa: S603
            [sys.executable, str(SCRIPTS / "build_prd_html.py"), "--root", str(self.root), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_tabs_overview_prds_in_index_order_then_decisions(self) -> None:
        tabs = re.findall(r'<button role="tab" data-tab="([^"]+)"', self.page)
        self.assertEqual(tabs, ["overview", "shop", "billing", "decisions"])
        panels = re.findall(r'class="panel[^"]*"[^>]*data-panel="([^"]+)"', self.page)
        self.assertEqual(panels, tabs)

    def test_one_section_per_file_with_number_and_toc(self) -> None:
        self.assertIn('<section id="a-orders">', self.page)
        self.assertIn('<h2><span class="num">05</span>Step 1 · Orders</h2>', self.page)
        self.assertIn('<section id="b-risks">', self.page)
        self.assertIn('<a href="#a-orders">05. Step 1 · Orders</a>', self.page)

    def test_every_rule_row_appears_once_with_its_text(self) -> None:
        rows = {m.group(1): m.group(2) for m in GATE_ROW.finditer(self.page)}
        self.assertEqual(sorted(rows), ["ORD-01", "ORD-02", "ORD-03", "R2-01", "R2-02"])
        self.assertEqual(len(GATE_ROW.findall(self.page)), 5)
        self.assertIn("Orders are listed.", rows["ORD-03"])

    def test_rule_rows_carry_change_via_and_severity(self) -> None:
        self.assertRegex(self.page, r'<tr data-via="frontend"><td>ORD-03</td>')
        self.assertRegex(self.page, r'<tr data-sev="high"><td>R2-01</td>')
        self.assertIn('<span class="via-tag v-frontend">frontend</span>', self.page)

    def test_example_column_is_rendered(self) -> None:
        self.assertIn("<th>Example</th>", self.page)
        self.assertIn('<td class="ex" data-label="Example">Cart of 0 items → refused</td>', self.page)

    def test_ids_never_break_and_paths_break_at_separators(self) -> None:
        self.assertIn('<span class="nw">R2-01</span>', self.page)
        self.assertIn('src/<wbr>order.ts::<wbr>total', self.page)

    def test_callouts_markers_and_checked_in_code(self) -> None:
        self.assertIn('<div class="callout info">', self.page)
        self.assertIn('<div class="callout risk"><b class="t">An empty cart can be confirmed', self.page)
        self.assertIn('<span class="verified">checked in code</span>', self.page)
        self.assertIn('<i class="mk mk-pending">(approved 2026-10-07, pending code)</i>', self.page)

    def test_mermaid_and_code_blocks_keep_their_source(self) -> None:
        m = re.search(r'<pre class="mermaid">(.*?)</pre>', self.page, re.S)
        self.assertEqual(html.unescape(m.group(1)), "flowchart TD\n  A[Cart] -->|confirm| B{Valid?}")
        self.assertIn("raw &lt;block&gt; &amp; code", self.page)

    def test_links_within_and_across_prds(self) -> None:
        self.assertIn('<a href="#a-orders">05</a>', self.page)
        self.assertIn('<a href="#b-risks" data-go="billing">16</a>', self.page)
        self.assertIn('<a href="#a-orders" data-go="shop">orders</a>', self.page)

    def test_html_is_escaped_and_inline_markup_converted(self) -> None:
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; | tax.", self.page)
        self.assertNotIn("<script>alert(1)", self.page)
        self.assertIn("<code>items.length &gt;= 1</code>", self.page)
        self.assertIn("<b>orders</b>", self.page)
        self.assertIn("<em>at least</em>", self.page)

    def test_no_raw_markdown_or_placeholder_left(self) -> None:
        body = body_of(self.page)
        for raw in ("**", "`", "[!", "{{", "](", "| ---"):
            self.assertNotIn(raw, body, raw)

    def test_decisions_tab_from_readme_and_open_questions(self) -> None:
        panel = self.page[self.page.index('data-panel="decisions"'):]
        self.assertIn('<td class="qid">Q1</td>', panel)
        self.assertIn("Should orders expire?", panel)
        self.assertIn("Should carts merge?", panel)
        self.assertRegex(panel, r'<tr data-sev="high"><td class="qid">Q1</td>')

    def test_overview_from_readme(self) -> None:
        self.assertIn('<section id="v-what-the-product-is">', self.page)
        self.assertIn("<h1>Shop PRDs</h1>", self.page)
        self.assertIn("Shop sells things online.", self.page)

    def test_nested_lists_and_story_lists(self) -> None:
        self.assertRegex(self.page, r"<li>two<ul><li>nested</li></ul></li>")

    def test_two_renders_are_identical(self) -> None:
        self.assertEqual(self.page, build_prd_html.render(self.root, dict(CFG)))

    def test_check_exit_codes(self) -> None:
        self.assertEqual(self.cli("--check").returncode, 1, "missing file must fail")
        self.assertEqual(self.cli().returncode, 0)
        r = self.cli("--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        orders = self.root / "docs/prd/shop/05-orders.md"
        orders.write_text(ORDERS.replace("Orders are listed.", "Orders are paged."), encoding="utf-8")
        self.assertEqual(self.cli("--check").returncode, 1)

    def test_an_old_template_is_refused_with_a_clear_error(self) -> None:
        (self.root / "docs/templates/prd.html").write_text("<html>{{PROJECT}}</html>", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_prd_html.render(self.root, dict(CFG))
        self.assertEqual(self.cli().returncode, 2)

    def test_check_ignores_the_commit_stamp(self) -> None:
        out = self.root / "docs/prd/prd.html"
        out.write_text(self.page, encoding="utf-8", newline="\n")
        stamped = re.sub(r"(<span data-stamp>)[^<]*", r"\1abc1234", self.page)
        self.assertNotEqual(stamped, self.page)
        out.write_text(stamped, encoding="utf-8", newline="\n")
        self.assertTrue(build_prd_html.is_current(self.root, dict(CFG)))


class LinkSchemeTest(unittest.TestCase):
    def test_only_safe_schemes_become_hrefs(self) -> None:
        import prd_html_markdown

        inline = prd_html_markdown.Inline(lambda url: (url, ""))
        out = inline("[a](javascript:void) [b](data:text/html,x) [c](VBScript:x) [d](https://a.b) [e](mailto:a@b.c) [f](#x)")
        for bad in ("javascript", "data:", "VBScript"):
            self.assertNotIn(bad, out)
        for good in ('href="https://a.b"', 'href="mailto:a@b.c"', 'href="#x"'):
            self.assertIn(good, out)
        for label in (">a<", ">b<"):
            self.assertNotIn(label, out)
        self.assertIn("a b c", re.sub(r"<[^>]*>", "", out))


class IndexEntriesTest(unittest.TestCase):
    def test_an_escaped_pipe_in_a_title_stays_in_its_cell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prd = Path(tmp)
            index = "## PRD 1 · Shop\n| File | Section | IDs |\n|---|---|---|\n| [a.md](shop/a.md) | Orders \\| Carts | X-01 |\n"
            (prd / "INDEX.md").write_text(index, encoding="utf-8", newline="\n")
            entries = build_prd_html.index_entries(prd)
        self.assertEqual(entries[0][3][0][1], "Orders | Carts")
