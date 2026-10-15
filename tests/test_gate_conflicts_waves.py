"""gate.py --step plan: the wave table and the critical path, and P17 as the only plan check left."""

import unittest

from tests.gate_report import full
from tests.test_kit_scripts import Project, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"


def plan(*tasks: str) -> str:
    return "# Plan\n\n" + "\n".join(tasks)


def task(tid: str, owns: str, depends: str = "none", extra: str = "", title: str = "do it") -> str:
    return f"### {tid} · {title}\nContract: ORD-01\nOwns: {owns}\nRead: {owns}\nReviewer: x\nModel: sonnet\nDepends on: {depends}\n{extra}"


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
        r = self.gate(plan(task("T01", "src/a/a.py, src/a/test_a.py"), task("T02", "src/b/b.py, src/b/test_b.py"), task("T03", "src/c/c.py, src/c/test_c.py", "T01")))
        lines = r.stdout.splitlines()
        self.assertIn("WAVE 1: T01, T02", lines, r.stdout)
        self.assertIn("WAVE 2: T03", lines, r.stdout)
        self.assertIn("CRITICAL PATH: T01 > T03", lines, r.stdout)
        self.assertIn("gate:0 error(s), 0 warning(s)", full(self.p, r))

    def test_at_most_four_per_wave(self) -> None:
        tasks = [task(f"T0{n}", f"src/f{n}.py") for n in range(1, 7)]
        r = self.gate(plan(*tasks))
        self.assertIn("WAVE 1: T01, T02, T03, T04", r.stdout.splitlines(), r.stdout)
        self.assertIn("WAVE 2: T05, T06", r.stdout.splitlines(), r.stdout)

    def test_critical_path_tasks_come_first_in_a_wave(self) -> None:
        r = self.gate(plan(task("T01", "src/a.py"), task("T02", "src/b.py"), task("T03", "src/c.py", "T02")))
        self.assertIn("WAVE 1: T02, T01", r.stdout.splitlines(), r.stdout)

    def test_serial_tasks_may_share_a_file(self) -> None:
        r = self.gate(plan(task("T01", "src/a.py"), task("T02", "src/a.py", "T01")))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_two_tasks_of_one_wave_on_the_shared_file_warn_p17(self) -> None:
        r = self.gate(plan(task("T01", "src/a.py", extra="Creates / consumes: creates ai-kit.json\n"), task("T02", "src/b.py", extra="Creates / consumes: creates ai-kit.json\n")))
        self.assertIn("WARNING P17", full(self.p, r))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_the_owns_and_depends_on_checks_are_gone(self) -> None:
        r = self.gate(plan(task("T01", "src/a.py, src/shared.py", "T09"), task("T02", "src/shared.py", extra="Creates / consumes: docs/trd/orders.md\n")))
        self.assertEqual(r.returncode, 0, r.stdout)
        for code in ("P1", "P7", "P8", "P9"):
            self.assertNotIn(code, full(self.p, r))


if __name__ == "__main__":
    unittest.main()
