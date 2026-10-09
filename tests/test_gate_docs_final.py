"""gate.py --final --change <slug>, --snapshot <slug> and --docs <slug> (W3.6, W3.8) against a throwaway project."""

import unittest

from tests.test_kit_scripts import Project, write
from tests.gate_report import full

GATE = ".claude/skills/prd-flow/scripts/gate.py"
ORDERS = "docs/prd/shop/05-orders.md"
SLUG = "003-mine"
APPROVED = """\
# Approved rules

## 05-orders.md
| ID | Rule | Source | Change via |
|---|---|---|---|
| ORD-02 | An unpaid order is cancelled after the payment timeout (`OrderConfig.timeout`). | src/features/orders/order_service.py | config |
"""


RULES_ONLY = APPROVED.replace("# Approved rules", "# Rules · mine · 2026-10-07 · Ana")


class ScopedFinalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        write(self.p.root, f".claude/prd-flow/state/{SLUG}/approved-rules.md", APPROVED)

    def tearDown(self) -> None:
        self.p.close()

    def plan_row(self, rid: str, old: str) -> None:
        section = self.p.root / ORDERS
        section.write_text(section.read_text(encoding="utf-8").replace(old, "planned | code"), encoding="utf-8")

    def final(self) -> object:
        return self.p.py(GATE, "--final", "--change", SLUG)

    def test_a_rules_md_only_state_still_scopes_the_final_gate(self) -> None:
        (self.p.root / f".claude/prd-flow/state/{SLUG}/approved-rules.md").unlink()
        write(self.p.root, f".claude/prd-flow/state/{SLUG}/rules.md", RULES_ONLY)
        self.plan_row("ORD-02", "src/features/orders/order_service.py | config")
        r = self.final()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G19", r.stdout)

    def test_another_changes_planned_row_is_a_warning(self) -> None:
        self.plan_row("ORD-01", "src/features/orders/order_service.py::create_order | code")
        r = self.final()
        self.assertEqual(r.returncode, 0, full(self.p, r))
        self.assertIn("WARNING G19", full(self.p, r))
        self.assertIn("ORD-01", full(self.p, r))

    def test_this_changes_planned_row_is_an_error(self) -> None:
        self.plan_row("ORD-02", "src/features/orders/order_service.py | config")
        r = self.final()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G19", r.stdout)
        self.assertIn("ORD-02", r.stdout)

    def test_other_open_folders_warn_and_this_folder_errors(self) -> None:
        write(self.p.root, "changes/002-other/plan.md", "# other\n")
        r = self.final()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING G21", full(self.p, r))
        write(self.p.root, f"changes/{SLUG}/plan.md", "# mine\n")
        r = self.final()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(f"ERROR G21 changes/{SLUG}", r.stdout)

    def test_planned_sections_are_scoped_by_heading(self) -> None:
        write(self.p.root, "docs/trd/orders.md", "# Orders\n\n## Planned (002-other)\nORD-01 moves.\n")
        r = self.final()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING G20", full(self.p, r))
        write(self.p.root, "docs/trd/billing.md", f"# Billing\n\n## Planned ({SLUG})\nBIL-01 moves.\n")
        r = self.final()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G20 billing.md", r.stdout)

    def test_unscoped_final_is_unchanged(self) -> None:
        write(self.p.root, "changes/002-other/plan.md", "# other\n")
        r = self.p.py(GATE, "--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G21", r.stdout)

    def test_snapshot_marks_older_drift_as_pre_existing(self) -> None:
        write(self.p.root, "changes/002-other/plan.md", "# other\n")
        self.plan_row("ORD-01", "src/features/orders/order_service.py::create_order | code")
        s = self.p.py(GATE, "--snapshot", SLUG)
        self.assertEqual(s.returncode, 0, s.stdout)
        write(self.p.root, "changes/004-new/plan.md", "# new\n")
        r = self.final()
        self.assertEqual(r.returncode, 0, full(self.p, r))
        self.assertIn("pre-existing", full(self.p, r))
        lines = [ln for ln in full(self.p, r).splitlines() if "004-new" in ln]
        self.assertTrue(lines and "pre-existing" not in lines[0], full(self.p, r))
        old = [ln for ln in full(self.p, r).splitlines() if "002-other" in ln]
        self.assertTrue(old and "pre-existing" in old[0], full(self.p, r))


class DocsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def test_approved_rules_run_the_rules_checks(self) -> None:
        write(self.p.root, f".claude/prd-flow/state/{SLUG}/approved-rules.md", APPROVED)
        r = self.p.py(GATE, "--docs", SLUG)
        self.assertIn("Q3", r.stdout)
        self.assertEqual(r.stdout.count("gate:"), 1, full(self.p, r))

    def test_a_rules_md_only_state_runs_the_rules_checks(self) -> None:
        write(self.p.root, f".claude/prd-flow/state/{SLUG}/rules.md", RULES_ONLY)
        r = self.p.py(GATE, "--docs", SLUG)
        self.assertIn("Q3", r.stdout)

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
        section = self.p.root / ORDERS
        section.write_text(section.read_text(encoding="utf-8").replace("payment timeout", "payment limit"), encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
