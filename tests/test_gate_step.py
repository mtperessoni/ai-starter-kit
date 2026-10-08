"""gate.py --step: one run per worker step with every check that step needs, and one report."""

import unittest

from tests.test_kit_scripts import Project, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"
ORDERS = "docs/prd/shop/05-orders.md"
RULES = "state/orders/approved-rules.md"
APPROVED = "# Approved\n\n## shop/05-orders.md\n| ID | Rule | Source | Change via |\n|---|---|---|---|\n| ORD-03 | Orders can be reopened. | planned | code |\n"
TRD = "# TRD\n\n| File | Role | Main symbols | IDs |\n|---|---|---|---|\n| `src/nowhere/missing.py` | gone | `gone` | ORD-01 |\n\n## Planned\nRules: ORD-77\n"
PLAN = "# Plan\n\n## Plan execution rules\n- x\n\n### T01 · do it\nContract: ORD-01\n"


class StepTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | hand |"), encoding="utf-8")

    def tearDown(self) -> None:
        self.p.close()

    def em_dash_in_the_prd(self) -> None:
        path = self.p.root / ORDERS
        path.write_text(path.read_text(encoding="utf-8") + "\nA line with an em dash — here.\n", encoding="utf-8", newline="\n")

    def test_prd_step_runs_the_default_checks_and_the_rules_checks_in_one_report(self) -> None:
        self.em_dash_in_the_prd()
        write(self.p.root, RULES, APPROVED)
        r = self.p.py(GATE, "--step", "prd", "--rules", RULES, "--applied")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G4", r.stdout)
        self.assertIn("ERROR Q3", r.stdout)
        self.assertIn("ERROR Q4", r.stdout)
        self.assertEqual(r.stdout.count("gate:"), 1, r.stdout)

    def test_prd_step_without_rules_is_the_light_route(self) -> None:
        r = self.p.py(GATE, "--step", "prd")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("Q3", r.stdout)

    def test_trd_step_runs_the_default_checks_and_the_trd_checks(self) -> None:
        write(self.p.root, "docs/trd/orders.md", TRD)
        r = self.p.py(GATE, "--step", "trd")
        self.assertIn("ERROR G23", r.stdout)
        self.assertIn("ERROR G8", r.stdout)
        self.assertEqual(r.stdout.count("gate:"), 1, r.stdout)

    def test_a_task_names_its_lens(self) -> None:
        write(self.p.root, "changes/001-orders/plan.md", PLAN + "Owns: src/a.py\nModel: sonnet\n")
        out = self.p.py(GATE, "--step", "plan", "--plan", "changes/001-orders/plan.md").stdout
        self.assertIn("WARNING P3", out)
        self.assertIn("Lens:", out)
        write(self.p.root, "changes/001-orders/plan.md", PLAN + "Owns: src/a.py\nModel: sonnet\nLens: none\n")
        self.assertNotIn("P3", self.p.py(GATE, "--step", "plan", "--plan", "changes/001-orders/plan.md").stdout)

    def test_a_task_without_read_is_error_p10(self) -> None:
        base = PLAN + "Owns: src/a.py" + chr(10) + "Model: sonnet" + chr(10) + "Lens: none" + chr(10)
        write(self.p.root, "changes/001-orders/plan.md", base)
        out = self.p.py(GATE, "--step", "plan", "--plan", "changes/001-orders/plan.md").stdout
        self.assertIn("ERROR P10", out)
        write(self.p.root, "changes/001-orders/plan.md", base + "Read: src/a.py::f" + chr(10))
        self.assertNotIn("P10", self.p.py(GATE, "--step", "plan", "--plan", "changes/001-orders/plan.md").stdout)

    def test_the_reviewer_label_is_still_accepted_for_the_lens(self) -> None:
        card = chr(10).join(["Owns: src/a.py", "Read: src/a.py", "Model: sonnet", "Reviewer: none", ""])
        write(self.p.root, "changes/001-orders/plan.md", PLAN + card)
        self.assertNotIn("P3", self.p.py(GATE, "--step", "plan", "--plan", "changes/001-orders/plan.md").stdout)

    def test_plan_step_checks_the_plan_and_the_change_folder(self) -> None:
        write(self.p.root, "changes/001-orders/plan.md", PLAN)
        r = self.p.py(GATE, "--step", "plan", "--plan", "changes/001-orders/plan.md", "--change", "changes/404-none")
        self.assertIn("ERROR P2", r.stdout)
        self.assertIn("ERROR G22", r.stdout)
        self.assertEqual(r.stdout.count("gate:"), 1, r.stdout)


if __name__ == "__main__":
    unittest.main()
