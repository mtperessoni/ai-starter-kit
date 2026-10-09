"""check_plan: P11 to P16 are retired, and the shared-file wave rule (P17) stays."""

import unittest

from tests.gate_report import full
from tests.test_kit_scripts import Project, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"
PLAN_PATH = "changes/001-orders/plan.md"
HEAD = "# Plan\n\n"
TRD = """# TRD

## Planned (orders, feat/orders)
Rules: ORD-01

| File | Changes or creates | Symbols | IDs |
|---|---|---|---|
| `src/orders/service.py` | changes | `create_order` | ORD-01, ORD-02 |

Tests to write:

| Test file | IDs |
|---|---|
| `src/orders/tests/test_service.py` | ORD-01 |
"""


def card(tid: str, contract: str = "ORD-01, ORD-02", owns: str = "src/orders/service.py, src/orders/tests/test_service.py",
         extra: str = "", depends: str = "none") -> str:
    lines = [f"### {tid} · do it", f"Contract: {contract}", f"Owns: {owns}", "Read: src/orders/service.py",
             f"Depends on: {depends}", "Model: sonnet", "Lens: none"]
    return "\n".join(lines) + "\n" + extra + "\n"


class RetiredAlignmentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        self.repo = repo
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | hand |"), encoding="utf-8")
        write(self.p.root, "docs/trd/orders.md", TRD)

    def tearDown(self) -> None:
        self.p.close()

    def run_plan(self, body: str) -> str:
        write(self.p.root, PLAN_PATH, HEAD + body)
        return full(self.p, self.p.py(GATE, "--step", "plan", "--plan", PLAN_PATH))

    def test_cards_that_used_to_trip_p11_to_p16_print_nothing(self) -> None:
        many = ", ".join(f"src/orders/f{i}.py" for i in range(9))
        bodies = [card("T01", contract="ORD-01", extra="Reached from: src/orders/service.py\n"),
                  card("T01", contract="ORD-01", owns=many),
                  card("T01", owns="src/orders/service.py"),
                  card("T01", extra="Creates / consumes: creates `Fresh.thing`\nReached from: nowhere/else.py\n")]
        for body in bodies:
            out = self.run_plan(body)
            for code in ("P11", "P12", "P13", "P14", "P15", "P16"):
                self.assertNotIn(code, out)

    def test_a_plan_without_an_execution_rules_heading_gets_no_p6(self) -> None:
        write(self.p.root, PLAN_PATH, "# Plan\n\n" + card("T01", owns="src/orders/service.py"))
        out = full(self.p, self.p.py(GATE, "--step", "plan", "--plan", PLAN_PATH))
        self.assertNotIn("P6", out)

    def test_plan_strict_no_longer_changes_anything(self) -> None:
        self.repo.write_text(self.repo.read_text(encoding="utf-8").replace("| html_mode | hand |", "| html_mode | hand |\n| plan_strict | yes |"), encoding="utf-8")
        write(self.p.root, PLAN_PATH, HEAD + card("T01", owns="src/orders/service.py"))
        r = self.p.py(GATE, "--step", "plan", "--plan", PLAN_PATH)
        self.assertEqual(r.returncode, 0, r.stdout)


class SharedFileWaveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def run_plan(self, body: str) -> str:
        write(self.p.root, PLAN_PATH, HEAD + body)
        return full(self.p, self.p.py(GATE, "--step", "plan", "--plan", PLAN_PATH))

    def strict(self) -> None:
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | generated |\n| plan_strict | yes |"), encoding="utf-8")

    def test_two_tasks_touching_ai_kit_json_in_one_wave_warn_and_fail_when_strict(self) -> None:
        a = card("T01", owns="ai-kit.json, src/a.py, src/tests/test_a.py")
        b = card("T02", owns="src/b.py, src/tests/test_b.py", extra="Creates / consumes: creates an entry in ai-kit.json\n")
        out = self.run_plan(a + b)
        self.assertIn("WARNING P17 T01 and T02", out)
        self.assertIn("ai-kit.json", out)
        self.strict()
        self.assertIn("ERROR P17 T01 and T02", self.run_plan(a + b))

    def test_a_single_task_wave_or_serial_tasks_are_fine(self) -> None:
        a = card("T01", owns="ai-kit.json, src/a.py, src/tests/test_a.py")
        b = card("T02", owns="src/b.py, src/tests/test_b.py", depends="T01", extra="Creates / consumes: creates an entry in ai-kit.json\n")
        self.assertNotIn("P17", self.run_plan(a + b))
        self.assertNotIn("P17", self.run_plan(a))

    def test_structure_allowlists_and_the_adapter_shared_files_count(self) -> None:
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | generated |\n| shared_files | src/settings.py |"), encoding="utf-8")
        a = card("T01", owns="src/settings.py, src/a.py, src/tests/test_a.py")
        b = card("T02", owns="src/b.py, src/tests/test_b.py", extra="Creates / consumes: changes src/settings.py\n")
        self.assertIn("WARNING P17", self.run_plan(a + b))
        c = card("T01", owns="scripts/structure_allowlist.json, src/a.py, src/tests/test_a.py")
        d = card("T02", owns="src/b.py, src/tests/test_b.py", extra="Creates / consumes: changes scripts/structure_allowlist.json\n")
        self.assertIn("WARNING P17", self.run_plan(c + d))


if __name__ == "__main__":
    unittest.main()
