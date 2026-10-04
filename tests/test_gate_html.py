"""gate.py HTML checks (G5 touched page, G10 plain rows) through a real git diff of PRD and HTML."""

import unittest

from tests.test_kit_scripts import Project, write

GATE = ".claude/skills/prd-gate/scripts/gate.py"
ORDERS = "docs/prd/shop/05-orders.md"
PAGE = "docs/prd/prd.html"

EXTRA_TABLE = """
| ID | Rule | Source | Change via |
|---|---|---|---|
| n/a | Orders are listed. | src | code |
"""

EXTRA_ROW = "<tr><td>n/a</td><td>Orders are listed.</td><td>src</td></tr>\n"


class GateHtmlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def edit(self, rel: str, old: str, new: str) -> None:
        path = self.p.root / rel
        path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8", newline="\n")

    def reword_in_both(self) -> None:
        self.edit(ORDERS, "at least one item", "at least two items")
        self.edit(PAGE, "at least one item", "at least two items")
        self.edit("docs/prd/CHANGELOG.md", "# CHANGELOG\n", "# CHANGELOG\n\nORD-01 reworded.\n")

    def test_a_touched_html_satisfies_g5(self) -> None:
        self.reword_in_both()
        r = self.p.py(GATE, "--base", "HEAD")
        self.assertNotIn("HTML was not touched", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_an_untouched_html_still_fails_g5(self) -> None:
        self.edit(ORDERS, "at least one item", "at least two items")
        self.edit("docs/prd/CHANGELOG.md", "# CHANGELOG\n", "# CHANGELOG\n\nORD-01 reworded.\n")
        r = self.p.py(GATE, "--base", "HEAD")
        self.assertIn("HTML was not touched", r.stdout)

    def test_a_table_header_row_is_not_compared_with_the_html(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8") + EXTRA_TABLE, encoding="utf-8", newline="\n")
        self.edit(PAGE, "</tbody>", EXTRA_ROW + "</tbody>")
        r = self.p.py(GATE, "--base", "HEAD")
        self.assertNotIn("G10", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_plain_row_missing_from_the_html_still_fails_g10(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8") + EXTRA_TABLE, encoding="utf-8", newline="\n")
        self.edit(PAGE, "<body>", "<body>\n")
        r = self.p.py(GATE, "--base", "HEAD")
        self.assertIn("G10", r.stdout)
        self.assertIn("Orders are listed", r.stdout)
        self.assertNotIn("Change via", r.stdout)


if __name__ == "__main__":
    unittest.main()
