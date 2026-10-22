"""G33: a PRD or TRD markdown file over 40 KB is a warning, never a failure."""

import unittest

from tests.gate_report import full
from tests.test_kit_scripts import Project, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"


class BigDocsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | hand |"), encoding="utf-8")

    def tearDown(self) -> None:
        self.p.close()

    def test_a_trd_file_over_40_kb_warns_and_does_not_fail(self) -> None:
        write(self.p.root, "docs/trd/orders.md", "# TRD\n\n" + "A line of prose about orders.\n" * 1500)
        r = self.p.py(GATE)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING G33 docs/trd/orders.md", full(self.p, r))

    def test_a_prd_file_over_40_kb_warns_and_does_not_fail(self) -> None:
        section = self.p.root / "docs/prd/shop/05-orders.md"
        section.write_text(section.read_text(encoding="utf-8") + "\n" + "Prose that is not a rule row.\n" * 1500, encoding="utf-8")
        r = self.p.py(GATE)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING G33 docs/prd/shop/05-orders.md", full(self.p, r))

    def test_files_under_the_limit_do_not_warn(self) -> None:
        write(self.p.root, "docs/trd/orders.md", "# TRD\n\n" + "A line of prose about orders.\n" * 100)
        self.assertNotIn("G33", full(self.p, self.p.py(GATE)))


if __name__ == "__main__":
    unittest.main()
