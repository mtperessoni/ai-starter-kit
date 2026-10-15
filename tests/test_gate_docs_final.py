"""gate.py --docs <slug> (W3.6, W3.8) against a throwaway project."""

import unittest

from tests.test_kit_scripts import Project, write
from tests.gate_report import full

GATE = ".claude/skills/prd-flow/scripts/gate.py"
SLUG = "003-mine"


class DocsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def test_a_code_file_change_invalidates_the_cache(self) -> None:
        self.p.py(GATE, "--docs", SLUG)
        write(self.p.root, "src/features/orders/order_service.py", "def create_order():" + chr(10) + "    pass" + chr(10))
        r = self.p.py(GATE, "--docs", SLUG)
        self.assertNotIn("cache hit", r.stdout)
        write(self.p.root, "src/features/orders/order_service.py", "def renamed():" + chr(10) + "    pass" + chr(10))
        again = self.p.py(GATE, "--docs", SLUG)
        self.assertNotIn("cache hit", again.stdout)
        self.assertIn("cache hit", self.p.py(GATE, "--docs", SLUG).stdout)

    def test_one_run_prints_one_summary(self) -> None:
        r = self.p.py(GATE, "--docs", SLUG)
        self.assertEqual(r.returncode, 0, full(self.p, r))
        self.assertEqual(full(self.p, r).count("gate:"), 1, full(self.p, r))
        self.assertNotIn("cache hit", full(self.p, r))

    def test_the_second_call_reuses_the_cache(self) -> None:
        self.p.py(GATE, "--docs", SLUG)
        r = self.p.py(GATE, "--docs", SLUG)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("cache hit", r.stdout)

    def test_a_changed_input_runs_again_and_a_failure_is_cached_too(self) -> None:
        self.p.py(GATE, "--docs", SLUG)
        write(self.p.root, "docs/trd/orders.md", "# T\n\nThe order rule ORD-99 lives here.\n")
        r = self.p.py(GATE, "--docs", SLUG)
        self.assertNotIn("cache hit", r.stdout)
        self.assertEqual(r.returncode, 1, r.stdout)
        again = self.p.py(GATE, "--docs", SLUG)
        self.assertEqual(again.returncode, 1, again.stdout)
        self.assertIn("cache hit", again.stdout)

    def test_fresh_skips_the_cache(self) -> None:
        self.p.py(GATE, "--docs", SLUG)
        r = self.p.py(GATE, "--docs", SLUG, "--fresh")
        self.assertNotIn("cache hit", r.stdout)

    def test_help_has_one_line_per_flag(self) -> None:
        out = self.p.py(GATE, "--help").stdout
        for flag in ("--docs", "--html", "--history", "--status", "--step", "--trd", "--sibling", "--change", "--plan"):
            self.assertEqual(sum(1 for ln in out.splitlines() if ln.lstrip().startswith(flag)), 1, flag)
        for flag in ("--rules", "--pack", "--sheet", "--final", "--snapshot", "--trace", "--fix", "--applied"):
            self.assertNotIn(flag, out)


if __name__ == "__main__":
    unittest.main()
