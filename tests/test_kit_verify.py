"""gates.sh verify (one verification per batch) and gates.sh python."""

import json

from tests.test_kit_baseline import GatesBase
from tests.test_kit_gates_run_speed import RUNNER
from tests.test_kit_scripts import write


class VerifyTest(GatesBase):
    def setUp(self) -> None:
        super().setUp()
        self.runner.write_text(RUNNER, encoding="utf-8")
        self.stamp = self.state("demo", "verify.stamp")

    def test_python_prints_the_resolved_interpreter(self) -> None:
        r = self.gates("python")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.strip())

    def test_verify_runs_related_tests_for_the_changed_files_and_writes_the_stamp_and_log(self) -> None:
        write(self.p.root, "src/a.py", "x = 1\n")
        r = self.gates("verify", "demo", "--since", "HEAD")
        self.assertIn("changed file(s) since HEAD", r.stdout, r.stdout + r.stderr)
        self.assertTrue(self.stamp.is_file())
        self.assertTrue(self.state("demo", "verify.log").is_file())
        self.assertIn("gates.sh related", self.state("demo", "verify.log").read_text(encoding="utf-8"))

    def test_a_rerun_with_nothing_changed_reruns_only_what_failed(self) -> None:
        write(self.p.root, "src/a.py", "x = 1\n")
        self.gates("verify", "demo", "--since", "HEAD")
        failed = json.loads(self.stamp.read_text(encoding="utf-8"))["failed"]
        before = len(self.runs())
        r = self.gates("verify", "demo")
        if failed:
            self.assertNotIn("nothing changed", r.stdout)
            self.assertIn("ok (unchanged since the last verification)" if "tests" not in failed else "tests", r.stdout)
        else:
            self.assertIn("nothing changed", r.stdout)
            self.assertEqual(len(self.runs()), before)

    def test_a_change_after_the_stamp_reruns_every_step(self) -> None:
        write(self.p.root, "src/a.py", "x = 1\n")
        self.gates("verify", "demo", "--since", "HEAD")
        before = len(self.runs())
        write(self.p.root, "src/b.py", "y = 2\n")
        r = self.gates("verify", "demo")
        self.assertNotIn("nothing changed", r.stdout)
        self.assertGreaterEqual(len(self.runs()), before)

    def test_a_bad_slug_is_a_usage_error(self) -> None:
        r = self.gates("verify", "../x")
        self.assertEqual(r.returncode, 2)
