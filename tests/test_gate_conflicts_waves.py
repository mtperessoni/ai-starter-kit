"""gate.py Q5 (conflict resolution), the Q4 cell message and --step plan waves (P7, P8, P9)."""

import unittest

from tests.test_kit_scripts import Project, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"
RULES = "state/orders/approved-rules.md"
PACK = "state/orders/pack.md"
ROW1 = "| ORD-01 | *(approved 2026-10-07, pending code)* An order needs two items. | src/features/orders/order_service.py::create_order | code |"
DIMS = "\n".join(f"| D{n:02d} thing | doc | x |" for n in range(1, 16))
INTERVIEW = f'# Interview\n\n## Dimensions\n| Dimension | State | Answer |\n|---|---|---|\n{DIMS}\n\nConfirmed: Ana · 2026-10-07 · "go"\n'


def approved(rows: str = ROW1, conflicts: str = "", extra: str = "") -> str:
    head = "# Approved\n\n## shop/05-orders.md\n| ID | Rule | Source | Change via |\n|---|---|---|---|\n" + rows + "\n"
    table = "\n## Conflicts\n| ID | Resolution | Note |\n|---|---|---|\n" + conflicts + "\n" if conflicts is not None else ""
    return head + table + extra


class ConflictTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        write(self.p.root, "state/orders/interview.md", INTERVIEW)

    def tearDown(self) -> None:
        self.p.close()

    def gate(self, rules: str, pack: str | None = None):
        write(self.p.root, RULES, rules)
        if pack is not None:
            write(self.p.root, PACK, pack)
        return self.p.py(GATE, "--rules", RULES)

    def test_a_missing_pack_is_not_an_error(self) -> None:
        r = self.gate(approved(conflicts=""))
        self.assertNotIn("Q5", r.stdout)

    def test_a_pack_conflict_without_a_row_is_q5(self) -> None:
        r = self.gate(approved(conflicts=""), "# Pack\nConflicts: ORD-02\n")
        self.assertIn("ERROR Q5 ORD-02", r.stdout)
        self.assertIn("; fix: ", r.stdout.split("ERROR Q5")[1].splitlines()[0])

    def test_conflicts_none_needs_nothing(self) -> None:
        r = self.gate(approved(conflicts=""), "# Pack\nConflicts: none\n")
        self.assertNotIn("Q5", r.stdout)

    def test_rewritten_needs_its_table_row(self) -> None:
        r = self.gate(approved(conflicts="| ORD-02 | rewritten | now two items |"), "# Pack\nConflicts: ORD-02\n")
        self.assertIn("ERROR Q5 ORD-02", r.stdout)
        ok = self.gate(approved(conflicts="| ORD-01 | rewritten | now two items |"), "# Pack\nConflicts: ORD-01\n")
        self.assertNotIn("Q5", ok.stdout)

    def test_superseded_must_be_listed_and_exist_in_the_prd(self) -> None:
        listed = "\n## Supersedes\nORD-02: An unpaid order is cancelled.\n"
        r = self.gate(approved(conflicts="| ORD-02 | superseded | gone |", extra=listed), "# Pack\nConflicts: ORD-02\n")
        self.assertNotIn("Q5", r.stdout)
        missing = self.gate(approved(conflicts="| ORD-02 | superseded | gone |"), "# Pack\nConflicts: ORD-02\n")
        self.assertIn("ERROR Q5 ORD-02", missing.stdout)
        ghost = self.gate(approved(conflicts="| ORD-99 | superseded | gone |", extra="\n## Supersedes\nORD-99: x\n"), "# Pack\nConflicts: ORD-99\n")
        self.assertIn("ERROR Q5 ORD-99", ghost.stdout)

    def test_compatible_needs_a_note(self) -> None:
        r = self.gate(approved(conflicts="| ORD-02 | compatible | |"), "# Pack\nConflicts: ORD-02\n")
        self.assertIn("ERROR Q5 ORD-02", r.stdout)
        ok = self.gate(approved(conflicts="| ORD-02 | compatible | different state |"), "# Pack\nConflicts: ORD-02\n")
        self.assertNotIn("Q5", ok.stdout)

    def test_an_unknown_resolution_is_q5_and_the_step_runs_it_too(self) -> None:
        write(self.p.root, RULES, approved(conflicts="| ORD-02 | maybe | x |"))
        write(self.p.root, PACK, "# Pack\nConflicts: ORD-02\n")
        r = self.p.py(GATE, "--step", "prd", "--rules", RULES)
        self.assertIn("ERROR Q5 ORD-02", r.stdout)

    def test_a_conflicts_table_is_not_read_as_rule_rows(self) -> None:
        r = self.gate(approved(conflicts="| ORD-01 | rewritten | x |"), "# Pack\nConflicts: ORD-01\n")
        self.assertNotIn("Q2", r.stdout)

    def test_q4_prints_the_differing_cells(self) -> None:
        write(self.p.root, RULES, approved(conflicts=""))
        r = self.p.py(GATE, "--rules", RULES, "--applied")
        line = next(x for x in r.stdout.splitlines() if x.startswith("ERROR Q4"))
        self.assertIn("An order needs two items", line)
        self.assertIn("An order is created only from a cart", line)
        self.assertIn("; fix: ", line)


def plan(*tasks: str) -> str:
    return "# Plan\n\n## Plan execution rules\n- x\n\n" + "\n".join(tasks)


def task(tid: str, owns: str, depends: str = "none", extra: str = "", title: str = "do it") -> str:
    return f"### {tid} · {title}\nContract: ORD-01\nOwns: {owns}\nReviewer: x\nModel: sonnet\nDepends on: {depends}\n{extra}"


class WaveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | hand |"), encoding="utf-8")
        write(self.p.root, "changes/001-orders/brief.md", "# brief\n")

    def tearDown(self) -> None:
        self.p.close()

    def gate(self, text: str):
        write(self.p.root, "changes/001-orders/plan.md", text)
        return self.p.py(GATE, "--step", "plan", "--plan", "changes/001-orders/plan.md")

    def test_waves_and_the_critical_path_are_printed_and_not_counted(self) -> None:
        r = self.gate(plan(task("T01", "src/a/a.py"), task("T02", "src/b/b.py"), task("T03", "src/c/c.py", "T01")))
        lines = r.stdout.splitlines()
        self.assertIn("WAVE 1: T01, T02", lines, r.stdout)
        self.assertIn("WAVE 2: T03", lines, r.stdout)
        self.assertIn("CRITICAL PATH: T01 > T03", lines, r.stdout)
        self.assertIn("gate:0 error(s), 0 warning(s)", r.stdout)

    def test_at_most_four_per_wave(self) -> None:
        tasks = [task(f"T0{n}", f"src/f{n}.py") for n in range(1, 7)]
        r = self.gate(plan(*tasks))
        self.assertIn("WAVE 1: T01, T02, T03, T04", r.stdout.splitlines(), r.stdout)
        self.assertIn("WAVE 2: T05, T06", r.stdout.splitlines(), r.stdout)

    def test_critical_path_tasks_come_first_in_a_wave(self) -> None:
        r = self.gate(plan(task("T01", "src/a.py"), task("T02", "src/b.py"), task("T03", "src/c.py", "T02")))
        self.assertIn("WAVE 1: T02, T01", r.stdout.splitlines(), r.stdout)

    def test_p7_two_tasks_of_one_wave_sharing_an_owned_file(self) -> None:
        r = self.gate(plan(task("T01", "src/a.py, src/shared.py"), task("T02", "src/shared.py")))
        self.assertIn("ERROR P7", r.stdout)
        self.assertEqual(r.returncode, 1)
        self.assertIn("; fix: ", next(x for x in r.stdout.splitlines() if "ERROR P7" in x))

    def test_p7_an_owned_glob_overlaps_a_file_under_its_directory(self) -> None:
        r = self.gate(plan(task("T01", "src/**"), task("T02", "src/a.py")))
        self.assertIn("ERROR P7", r.stdout)

    def test_p9_trailing_punctuation_does_not_hide_ownership(self) -> None:
        r = self.gate(plan(task("T01", "src/a.py, docs/trd/orders.md", extra="Creates / consumes: updates docs/trd/orders.md.\n")))
        self.assertNotIn("P9", r.stdout)

    def test_serial_tasks_may_share_a_file(self) -> None:
        r = self.gate(plan(task("T01", "src/a.py"), task("T02", "src/a.py", "T01")))
        self.assertNotIn("P7", r.stdout)

    def test_p8_two_serial_tasks_in_one_area_warn(self) -> None:
        r = self.gate(plan(task("T01", "src/features/orders/a.py"), task("T02", "src/features/orders/b.py", "T01")))
        self.assertIn("WARNING P8", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_p9_a_task_touching_docs_without_owning_it(self) -> None:
        r = self.gate(plan(task("T01", "src/a.py", extra="Creates / consumes: docs/trd/orders.md\n")))
        self.assertIn("ERROR P9", r.stdout)
        ok = self.gate(plan(task("T01", "src/a.py, docs/trd/orders.md", extra="Creates / consumes: docs/trd/orders.md\n")))
        self.assertNotIn("P9", ok.stdout)

    def test_a_dependency_on_an_unknown_task_is_an_error(self) -> None:
        r = self.gate(plan(task("T01", "src/a.py", "T09")))
        self.assertIn("ERROR P1", r.stdout)


if __name__ == "__main__":
    unittest.main()
