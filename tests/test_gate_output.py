"""gate.py output: --step trd scoped to the change, capped stdout, full report in an artifact."""

import os
import re
import unittest

from tests.test_kit_scripts import Project, run, write
from tests.gate_report import full

GATE = ".claude/skills/prd-flow/scripts/gate.py"
ARTIFACT = ".claude/prd-flow/state/_gate/last-step-trd.txt"
BAD = "# TRD\n\n| File | Role |\n|---|---|\n| `src/nowhere/missing.py` | gone |\n"


def bad_rows(n: int) -> str:
    return "# TRD\n\n| File | Role |\n|---|---|\n" + "".join(f"| `src/nowhere/m{i}.py` | gone |\n" for i in range(n))


class OutputTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | hand |"), encoding="utf-8")
        write(self.p.root, "docs/trd/old.md", BAD)
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "debt", check=True)

    def tearDown(self) -> None:
        self.p.close()

    def test_untouched_trd_debt_is_one_warning_line_and_not_an_error(self) -> None:
        r = self.p.py(GATE, "--step", "trd")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("ERROR G23", r.stdout)
        self.assertIn("WARNING G23 earlier drift, outside this change: 1 finding(s) in 1 file(s), see " + ARTIFACT, full(self.p, r))

    def test_a_changed_trd_file_keeps_its_errors(self) -> None:
        write(self.p.root, "docs/trd/new.md", BAD)
        r = self.p.py(GATE, "--step", "trd")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G23 docs/trd/new.md", r.stdout)
        self.assertNotIn("docs/trd/old.md", r.stdout)

    def test_plain_trd_reports_everything(self) -> None:
        r = self.p.py(GATE, "--trd")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G23 docs/trd/old.md", r.stdout)
        self.assertNotIn("earlier drift", r.stdout)

    def test_the_cap_and_the_artifact_keep_the_full_list(self) -> None:
        write(self.p.root, "docs/trd/many.md", bad_rows(20))
        r = self.p.py(GATE, "--step", "trd")
        lines = r.stdout.splitlines()
        self.assertEqual(sum(1 for x in lines if x.startswith("ERROR G23")), 15, r.stdout)
        self.assertIn("... 5 more errors, see " + ARTIFACT, lines)
        self.assertRegex(lines[-1], r"^warnings: \d+ \(see " + re.escape(ARTIFACT) + r"\)$")
        full = (self.p.root / ARTIFACT).read_text(encoding="utf-8")
        self.assertEqual(sum(1 for x in full.splitlines() if x.startswith("ERROR G23")), 20)
        self.assertIn("gate:20 error(s)", full)

    def test_an_unwritable_artifact_folder_does_not_fail_the_run(self) -> None:
        write(self.p.root, ".claude/prd-flow", "a file where the folder should be")
        r = self.p.py(GATE, "--step", "trd")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertRegex(r.stdout, r"warnings: \d+ \(see " + re.escape(ARTIFACT) + r"\)")
        self.assertFalse(os.path.isdir(self.p.root / ".claude/prd-flow"))


if __name__ == "__main__":
    unittest.main()
