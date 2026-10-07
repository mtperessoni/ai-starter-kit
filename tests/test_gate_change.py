"""gate.py --trace, --change and --final (LT08, LT09, LT10) against a throwaway project."""

import json
import unittest
from pathlib import Path

from tests.test_kit_scripts import Project, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"
ORDERS = "docs/prd/shop/05-orders.md"

BRIEF = """\
# Brief

Size: M

## Why
Orders need a limit.

## Slices
| Slice | Priority | Rule IDs | Independent test |
|---|---|---|---|
| Cart check | P1 | ORD-01 | create an order from an empty cart |
| Timeout | P2 | ORD-02 | wait for the timeout |

## Success criteria
ORD-01, ORD-02
"""

PLAN = """\
# Plan

### T01 · Cart check
Owns: src/features/orders/order_service.py
Reviewer: none
Model: sonnet
Contract (literal):
| ORD-01 | An order is created only from a cart with at least one item. | src | code |

### T02 · Promote
Owns: docs
"""


class TraceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def allow(self, rules: list[str]) -> None:
        path = self.p.root / "ai-kit.json"
        cfg = json.loads(path.read_text(encoding="utf-8"))
        cfg["allowlist"]["untested_rules"] = rules
        path.write_text(json.dumps(cfg), encoding="utf-8")

    def cite(self, rid: str) -> None:
        write(self.p.root, "src/features/orders/tests/test_cites.py", f'"""{rid}."""\n')

    def test_a_new_untested_rule_is_an_error(self) -> None:
        r = self.p.py(GATE, "--trace")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G12", r.stdout)
        self.assertIn("ORD-02", r.stdout)
        self.assertNotIn("ORD-01", r.stdout)

    def test_a_listed_untested_rule_is_a_warning(self) -> None:
        self.allow(["ORD-02"])
        r = self.p.py(GATE, "--trace")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING G13", r.stdout)

    def test_a_listed_rule_that_is_now_tested_must_leave_the_list(self) -> None:
        self.allow(["ORD-02"])
        self.cite("ORD-02")
        r = self.p.py(GATE, "--trace")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G14", r.stdout)

    def test_every_rule_cited_passes(self) -> None:
        self.cite("ORD-02")
        r = self.p.py(GATE, "--trace")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_planned_rule_needs_no_test(self) -> None:
        section = self.p.root / ORDERS
        text = section.read_text(encoding="utf-8").replace("src/features/orders/order_service.py | config", "planned | config")
        section.write_text(text, encoding="utf-8")
        r = self.p.py(GATE, "--trace")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_source_file_that_does_not_exist_is_an_error(self) -> None:
        self.cite("ORD-02")
        section = self.p.root / ORDERS
        text = section.read_text(encoding="utf-8").replace("order_service.py::create_order", "missing_file.py::create_order")
        section.write_text(text, encoding="utf-8")
        r = self.p.py(GATE, "--trace")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G11", r.stdout)
        self.assertIn("missing_file.py", r.stdout)


class ChangeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        self.change = "changes/001-limit"
        write(self.p.root, f"{self.change}/brief.md", BRIEF)
        write(self.p.root, f"{self.change}/plan.md", PLAN)

    def tearDown(self) -> None:
        self.p.close()

    def gate(self):
        return self.p.py(GATE, "--change", self.change)

    def test_a_consistent_change_passes(self) -> None:
        r = self.gate()
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_an_id_missing_from_the_prd_is_an_error(self) -> None:
        write(self.p.root, f"{self.change}/brief.md", BRIEF + "\nAlso ORD-99.\n")
        r = self.gate()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G15", r.stdout)
        self.assertIn("ORD-99", r.stdout)

    def test_a_p1_id_outside_every_task_contract_is_an_error(self) -> None:
        write(self.p.root, f"{self.change}/plan.md", PLAN.replace("| ORD-01 |", "| ORD-02 |"))
        r = self.gate()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G16", r.stdout)
        self.assertIn("ORD-01", r.stdout)

    def test_a_p2_id_outside_the_plan_is_fine(self) -> None:
        r = self.gate()
        self.assertNotIn("ORD-02", r.stdout.replace("2 rules", ""))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_rule_row_in_the_brief_is_an_error(self) -> None:
        row = "\n| ORD-01 | An order is created only from a cart. | src | code |\n"
        write(self.p.root, f"{self.change}/brief.md", BRIEF + row)
        r = self.gate()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G17", r.stdout)

    def test_a_design_without_size_l_is_a_warning(self) -> None:
        write(self.p.root, f"{self.change}/design.md", "# Design\n")
        r = self.gate()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING G18", r.stdout)

    def test_a_design_with_size_l_is_clean(self) -> None:
        write(self.p.root, f"{self.change}/brief.md", BRIEF.replace("Size: M", "Size: L"))
        write(self.p.root, f"{self.change}/design.md", "# Design\n")
        r = self.gate()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("G18", r.stdout)

    def test_a_missing_change_folder_is_an_error(self) -> None:
        r = self.p.py(GATE, "--change", "changes/404-none")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G22", r.stdout)


class FinalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def test_a_clean_tree_passes(self) -> None:
        write(self.p.root, "changes/archive/001-done/plan.md", "# done\n")
        r = self.p.py(GATE, "--final")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_a_planned_source_is_an_error(self) -> None:
        section = self.p.root / ORDERS
        text = section.read_text(encoding="utf-8").replace("src/features/orders/order_service.py | config", "planned | config")
        section.write_text(text, encoding="utf-8")
        r = self.p.py(GATE, "--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G19", r.stdout)
        self.assertIn("ORD-02", r.stdout)

    def test_the_pending_marker_is_an_error(self) -> None:
        section = self.p.root / ORDERS
        text = section.read_text(encoding="utf-8").replace("An unpaid order", "*(approved 2026-01-01, pending code)* An unpaid order")
        section.write_text(text, encoding="utf-8")
        r = self.p.py(GATE, "--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G19", r.stdout)

    def test_a_planned_section_in_the_trd_is_an_error(self) -> None:
        write(self.p.root, "docs/trd/orders.md", "# Orders\n\n## Planned\nORD-02 moves.\n")
        r = self.p.py(GATE, "--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G20", r.stdout)

    def set_planned_heading(self, heading: str) -> None:
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        text = repo.read_text(encoding="utf-8")
        repo.write_text(text.replace("| pack_budget_lines |", f"| planned_heading | {heading} |\n| pack_budget_lines |", 1), encoding="utf-8")

    def test_a_configured_planned_heading_is_an_error_in_final(self) -> None:
        self.set_planned_heading("Planejado")
        write(self.p.root, "docs/trd/orders.md", "# Pedidos\n\n## Planejado\nORD-02 muda.\n")
        r = self.p.py(GATE, "--final")
        self.assertIn("ERROR G20", r.stdout)

    def test_the_default_heading_is_ignored_when_another_is_configured(self) -> None:
        self.set_planned_heading("Planejado")
        write(self.p.root, "docs/trd/orders.md", "# Pedidos\n\n## Planned\nORD-02 stays.\n")
        r = self.p.py(GATE, "--final")
        self.assertNotIn("ERROR G20", r.stdout)

    def test_a_configured_planned_heading_is_checked_for_unknown_ids(self) -> None:
        self.set_planned_heading("Planejado")
        write(self.p.root, "docs/trd/orders.md", "# Pedidos\n\n## Planejado\nXYZ-99 muda.\n")
        r = self.p.py(GATE)
        self.assertIn("ERROR G8", r.stdout)

    def test_an_open_change_folder_is_an_error(self) -> None:
        write(self.p.root, "changes/002-open/plan.md", "# open\n")
        r = self.p.py(GATE, "--final")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G21", r.stdout)
        self.assertIn("002-open", r.stdout)


if __name__ == "__main__":
    unittest.main()
