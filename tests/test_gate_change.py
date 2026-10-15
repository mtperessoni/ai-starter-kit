"""gate.py --change (G15, G22) and the configured planned heading (G8) against a throwaway project."""

import unittest

from tests.test_kit_scripts import Project, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"

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

    def test_the_brief_and_plan_shape_checks_are_gone(self) -> None:
        write(self.p.root, f"{self.change}/plan.md", PLAN.replace("| ORD-01 |", "| ORD-02 |"))
        write(self.p.root, f"{self.change}/brief.md", BRIEF + "\n| ORD-01 | An order is created only from a cart. | src | code |\n")
        write(self.p.root, f"{self.change}/design.md", "# Design\n")
        r = self.gate()
        self.assertEqual(r.returncode, 0, r.stdout)
        for code in ("G16", "G17", "G18"):
            self.assertNotIn(code, r.stdout)

    def test_a_missing_change_folder_is_an_error(self) -> None:
        r = self.p.py(GATE, "--change", "changes/404-none")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G22", r.stdout)

    def test_the_final_and_trace_modes_are_gone(self) -> None:
        for flag in ("--final", "--trace"):
            self.assertEqual(self.p.py(GATE, flag).returncode, 2, flag)


class PlannedHeadingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def set_planned_heading(self, heading: str) -> None:
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        text = repo.read_text(encoding="utf-8")
        repo.write_text(text.replace("| plan_strict |", f"| planned_heading | {heading} |\n| plan_strict |", 1), encoding="utf-8")

    def test_a_configured_planned_heading_is_checked_for_unknown_ids(self) -> None:
        self.set_planned_heading("Planejado")
        write(self.p.root, "docs/trd/orders.md", "# Pedidos\n\n## Planejado\nXYZ-99 muda.\n")
        r = self.p.py(GATE)
        self.assertIn("ERROR G8", r.stdout)


if __name__ == "__main__":
    unittest.main()
