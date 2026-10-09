"""check_plan alignment (P11 to P16) and the shared-file wave rule (P17)."""

import unittest

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


class PlanAlignTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        self.repo = repo
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | hand |"), encoding="utf-8")
        write(self.p.root, "docs/trd/orders.md", TRD)

    def tearDown(self) -> None:
        self.p.close()

    def strict(self) -> None:
        self.repo.write_text(self.repo.read_text(encoding="utf-8").replace("| html_mode | hand |", "| html_mode | hand |\n| plan_strict | yes |"), encoding="utf-8")

    def run_plan(self, body: str) -> str:
        write(self.p.root, PLAN_PATH, HEAD + body)
        return self.p.py(GATE, "--step", "plan", "--plan", PLAN_PATH).stdout

    def test_a_contract_missing_a_trd_id_of_an_owned_file_warns_on_an_old_plan_and_fails_when_strict(self) -> None:
        out = self.run_plan(card("T01", contract="ORD-01", extra="Reached from: src/orders/service.py\n"))
        self.assertIn("WARNING P11 T01", out)
        self.assertIn("ORD-02", out)
        self.strict()
        self.assertIn("ERROR P11 T01", self.run_plan(card("T01", contract="ORD-01", extra="Reached from: src/orders/service.py\n")))

    def test_a_contract_covering_the_trd_ids_passes(self) -> None:
        self.assertNotIn("P11", self.run_plan(card("T01")))

    def test_an_open_trd_decision_warns_and_fails_when_strict(self) -> None:
        write(self.p.root, "docs/trd/orders.md", TRD + "\nE-3: should retries be capped? decision open\n")
        out = self.run_plan(card("T01"))
        self.assertIn("WARNING P12", out)
        self.assertNotIn("ERROR P12", out)
        self.assertIn("E-3", out)
        self.strict()
        self.assertIn("ERROR P12", self.run_plan(card("T01")))

    def test_a_decision_line_that_cites_a_prd_row_is_not_open(self) -> None:
        write(self.p.root, "docs/trd/orders.md", TRD + "\nDecision: retries are capped, see ORD-02\n")
        self.assertNotIn("P12", self.run_plan(card("T01")))

    def test_a_created_symbol_needs_reached_from(self) -> None:
        body = card("T01", extra="Creates / consumes: creates `OrderConfig.retry_after`\n")
        self.assertIn("WARNING P13 T01", self.run_plan(body))
        self.strict()
        self.assertIn("ERROR P13 T01", self.run_plan(body))

    def test_reached_from_must_name_a_file_some_card_owns_or_a_consumed_symbol(self) -> None:
        extra = "Creates / consumes: creates `OrderConfig.retry_after`\nReached from: src/orders/nowhere.py::run\n"
        self.assertIn("WARNING P14 T01", self.run_plan(card("T01", extra=extra)))
        ok = "Creates / consumes: creates `OrderConfig.retry_after`\nReached from: src/orders/service.py::create_order\n"
        self.assertNotIn("P14", self.run_plan(card("T01", extra=ok)))

    def test_reached_from_may_be_a_symbol_another_card_consumes(self) -> None:
        a = card("T01", extra="Creates / consumes: creates `OrderConfig.retry_after`\nReached from: OrderConfig.retry_after\n")
        b = card("T02", contract="ORD-01", owns="src/orders/wire.py, src/orders/tests/test_wire.py", depends="T01",
                 extra="Creates / consumes: consumes `OrderConfig.retry_after` (T01)\n")
        self.assertNotIn("P14", self.run_plan(a + b))

    def test_more_than_eight_files_or_no_test_path_fails_when_strict(self) -> None:
        many = ", ".join(f"src/orders/f{i}.py" for i in range(9)) + ", src/orders/tests/test_f.py"
        self.assertIn("WARNING P15 T01", self.run_plan(card("T01", contract="ORD-01", owns=many)))
        no_test = card("T01", contract="ORD-01, ORD-02", owns="src/orders/service.py")
        self.assertIn("WARNING P16 T01", self.run_plan(no_test))
        self.strict()
        self.assertIn("ERROR P16 T01", self.run_plan(no_test))
        self.assertIn("ERROR P15 T01", self.run_plan(card("T01", contract="ORD-01", owns=many)))

    def test_a_complete_card_is_clean_even_when_strict(self) -> None:
        self.strict()
        extra = "Creates / consumes: creates `OrderConfig.retry_after`\nReached from: src/orders/service.py::create_order\n"
        out = self.run_plan(card("T01", extra=extra))
        for code in ("P11", "P12", "P13", "P14", "P15", "P16"):
            self.assertNotIn(code, out)


class SharedFileWaveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def run_plan(self, body: str) -> str:
        write(self.p.root, PLAN_PATH, HEAD + body)
        return self.p.py(GATE, "--step", "plan", "--plan", PLAN_PATH).stdout

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
