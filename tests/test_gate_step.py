"""gate.py --step: one run per worker step with every check that step needs, and one report."""

import unittest

from tests.test_kit_scripts import Project, write
from tests.gate_report import full

GATE = ".claude/skills/prd-flow/scripts/gate.py"
TRD = "# TRD\n\n| File | Role |\n|---|---|\n| `src/nowhere/missing.py` | gone |\n\nThe order rule ORD-99 lives here.\n\n## Planned\nRules: ORD-77\n"
PLAN = "# Plan\n\n### T01 · do it\nContract: ORD-01\n"


class StepTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | hand |"), encoding="utf-8")

    def tearDown(self) -> None:
        self.p.close()

    def test_prd_step_runs_the_default_checks_in_one_report(self) -> None:
        write(self.p.root, "docs/trd/orders.md", "# TRD\n\nThe order rule ORD-99 lives here.\n")
        r = self.p.py(GATE, "--step", "prd")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G8", r.stdout)
        self.assertEqual(full(self.p, r).count("gate:"), 1, r.stdout)

    def test_prd_step_clean_passes(self) -> None:
        r = self.p.py(GATE, "--step", "prd")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_trd_step_runs_the_default_checks_and_the_trd_checks(self) -> None:
        write(self.p.root, "docs/trd/orders.md", TRD)
        r = self.p.py(GATE, "--step", "trd")
        self.assertIn("WARNING G23", full(self.p, r))
        self.assertIn("ERROR G8", full(self.p, r))
        self.assertEqual(full(self.p, r).count("gate:"), 1, full(self.p, r))

    def test_the_card_checks_are_gone(self) -> None:
        write(self.p.root, "changes/001-orders/plan.md", PLAN)
        out = full(self.p, self.p.py(GATE, "--step", "plan", "--plan", "changes/001-orders/plan.md"))
        for code in ("P2", "P3", "P4", "P10"):
            self.assertNotIn(code, out)

    def test_plan_step_checks_the_plan_and_the_change_folder(self) -> None:
        write(self.p.root, "changes/001-orders/plan.md", PLAN)
        r = self.p.py(GATE, "--step", "plan", "--plan", "changes/001-orders/plan.md", "--change", "changes/404-none")
        self.assertIn("WAVE 1: T01", full(self.p, r))
        self.assertIn("ERROR G22", full(self.p, r))
        self.assertEqual(full(self.p, r).count("gate:"), 1, full(self.p, r))


if __name__ == "__main__":
    unittest.main()
