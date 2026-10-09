"""Wave 1 review fixes (R2 to R7, R21, R22): rerun exit code, compare stamp, deselect, baseline status and links, config_get, docs routing."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.test_kit_baseline import GatesBase
from tests.test_kit_scripts import BASH, KIT, PY, run, write

RUNNER = """\
import json, os, sys
with open(os.environ["RUN_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"cwd": os.getcwd(), "argv": sys.argv[1:], "modules": os.path.exists("node_modules/x.txt")}) + "\\n")
if os.environ.get("RUN_FAIL"):
    print("FAILED " + os.environ["RUN_FAIL"])
print("1 passed")
sys.exit(int(os.environ.get("RUN_EXIT", "1" if os.environ.get("RUN_FAIL") else "0")))
"""


def script_module(name: str):
    sys.path.insert(0, str(KIT / "scripts"))
    try:
        return __import__(name)
    finally:
        sys.path.remove(str(KIT / "scripts"))
        sys.modules.pop(name, None)


class RunSpeedBase(GatesBase):
    def setUp(self) -> None:
        super().setUp()
        self.runner.write_text(RUNNER, encoding="utf-8")


class RerunTest(RunSpeedBase):
    def seed(self, slug: str = "demo") -> None:
        folder = self.p.root / ".claude/prd-flow/state" / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "baseline-failures.txt").write_text("", encoding="utf-8")

    def test_rerun_fails_when_the_runner_exits_nonzero_without_a_failure_line(self) -> None:
        self.seed()
        r = self.gates("rerun", "demo", "a::b", env={**self.env, "RUN_EXIT": "5"})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("exit 5", r.stdout + r.stderr)

    def test_rerun_passes_when_the_runner_exits_zero(self) -> None:
        self.seed()
        r = self.gates("rerun", "demo", "a::b")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_rerun_applies_the_deselect_list(self) -> None:
        self.configure(tests={"baseline_deselect": ["tests/test_a.py::test_hang"]})
        self.seed()
        self.gates("rerun", "demo", "a::b")
        self.assertEqual(self.runs()[-1]["argv"], ["--deselect", "tests/test_a.py::test_hang", "a::b"])

    def test_compare_applies_the_deselect_list(self) -> None:
        self.configure(tests={"baseline_deselect": ["tests/test_a.py::test_hang"]})
        self.gates("compare", "demo")
        self.assertEqual(self.runs()[-1]["argv"], ["--deselect", "tests/test_a.py::test_hang"])


class CompareStampTest(RunSpeedBase):
    def stamp(self) -> str:
        return (self.p.root / ".claude/prd-flow/state/demo/final.stamp").read_text(encoding="utf-8").strip()

    def current(self) -> str:
        return script_module("close_gate").tree_stamp(self.p.root)

    def test_the_stamp_matches_the_tree_right_after_compare(self) -> None:
        self.gates("compare", "demo")
        self.assertEqual(self.stamp(), self.current())

    def test_an_untracked_file_changes_the_stamp(self) -> None:
        self.gates("compare", "demo")
        write(self.p.root, "src/features/orders/tests/test_new.py", "x = 1\n")
        self.assertNotEqual(self.stamp(), self.current())

    def test_reediting_an_already_modified_file_changes_the_stamp(self) -> None:
        path = write(self.p.root, "src/features/orders/order_service.py", "x = 2\n")
        self.gates("compare", "demo")
        path.write_text("x = 3\n", encoding="utf-8")
        self.assertNotEqual(self.stamp(), self.current())

    def test_the_stamp_is_written_after_the_run(self) -> None:
        self.gates("compare", "demo")
        stamp = self.p.root / ".claude/prd-flow/state/demo/final.stamp"
        final = self.p.root / ".claude/prd-flow/state/demo/final.log"
        self.assertGreaterEqual(stamp.stat().st_mtime_ns, final.stat().st_mtime_ns)


class CloseRerunIdsTest(RunSpeedBase):
    def prepare(self, rerun_ids: bool) -> None:
        self.configure(commands={"lint": f'"{PY}" -c "pass"'}, tests={"rerun_ids": rerun_ids})
        import shutil

        shutil.copytree(KIT / "docs" / "templates", self.p.root / "docs" / "templates", dirs_exist_ok=True)
        self.gates("html")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "html", check=True)
        self.gates("baseline", "demo")

    def close(self, env: dict) -> subprocess.CompletedProcess:
        return subprocess.run([PY, "scripts/close_gate.py", "demo"], cwd=self.p.root, capture_output=True, text=True, encoding="utf-8",
                              env={**env, "GATES_BASH": BASH}, check=False)

    def test_a_new_failure_without_runnable_ids_runs_the_full_suite_and_fails(self) -> None:
        self.prepare(False)
        env = {**self.env, "RUN_FAIL": "Some title"}
        self.gates("compare", "demo", env=env)
        before = len(self.runs())
        r = self.close(env)
        runs = self.runs()
        self.assertEqual(runs[-1]["argv"], [], r.stdout)
        self.assertGreater(len(runs), before)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("all passed", r.stdout)


class BaselineStatusTest(RunSpeedBase):
    def test_a_setup_failure_ends_the_status_as_failed(self) -> None:
        self.configure(commands={"setup": f'"{PY}" -c "import sys; sys.exit(7)"'})
        r = self.gates("baseline", "s1")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        status = self.state("s1", "baseline.status").read_text(encoding="utf-8")
        self.assertTrue(status.startswith("failed"), status)

    def test_a_crash_ends_the_status_as_failed(self) -> None:
        baseline = script_module("baseline")
        with mock.patch.object(baseline, "run_suite", side_effect=RuntimeError("boom")), \
                mock.patch.object(baseline, "repo_root", return_value=self.p.root):
            with self.assertRaises(RuntimeError):
                baseline.main(["s9", "--commit", "HEAD"])
        status = (self.p.root / ".claude/prd-flow/state/s9/baseline.status").read_text(encoding="utf-8")
        self.assertTrue(status.startswith("failed"), status)

    def test_baseline_runs_the_suite_with_the_gates_bash(self) -> None:
        text = (KIT / "scripts/gates.sh").read_text(encoding="utf-8")
        block = text.split("baseline)", 1)[1].split(";;", 1)[0]
        self.assertIn("GATES_BASH", block)


class BaselineLinkTest(RunSpeedBase):
    def make_modules(self) -> Path:
        write(self.p.root, ".gitignore", "node_modules/\n")
        modules = self.p.root / "node_modules"
        modules.mkdir()
        (modules / "x.txt").write_text("x", encoding="utf-8")
        return modules

    def test_the_dependency_folder_is_linked_and_setup_is_skipped(self) -> None:
        modules = self.make_modules()
        marker = Path(self.tmp.name) / "setup.marker"
        self.configure(commands={"setup": f'"{PY}" -c "open(r\'{marker}\', \'w\').write(\'x\')"'})
        r = self.gates("baseline", "s1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.runs()[0]["modules"])
        self.assertFalse(marker.exists())
        self.assertTrue((modules / "x.txt").is_file())

    def test_a_changed_lockfile_runs_setup_instead_of_linking(self) -> None:
        modules = self.make_modules()
        write(self.p.root, "yarn.lock", "old\n")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "lock", "--allow-empty", check=True)
        write(self.p.root, "yarn.lock", "new\n")
        marker = Path(self.tmp.name) / "setup.marker"
        self.configure(commands={"setup": f'"{PY}" -c "open(r\'{marker}\', \'w\').write(\'x\')"'})
        self.gates("baseline", "s1", "--commit", "HEAD~1")
        self.assertFalse(self.runs()[0]["modules"])
        self.assertTrue(marker.exists())
        self.assertTrue((modules / "x.txt").is_file())

    @unittest.skipUnless(os.name == "nt", "junctions are Windows only")
    def test_drop_links_removes_a_junction_and_keeps_its_target(self) -> None:
        baseline = script_module("baseline")
        keep = Path(self.tmp.name) / "real"
        keep.mkdir()
        (keep / "x.txt").write_text("x", encoding="utf-8")
        tree = Path(self.tmp.name) / "wt"
        tree.mkdir()
        made = subprocess.run(["cmd", "/c", "mklink", "/J", str(tree / "node_modules"), str(keep)], capture_output=True, check=False)
        self.assertEqual(made.returncode, 0, made.stdout)
        self.assertTrue(baseline.is_link(tree / "node_modules"))
        baseline.drop_links(tree)
        self.assertFalse((tree / "node_modules").exists())
        self.assertTrue((keep / "x.txt").is_file())

    def test_drop_links_never_deletes_a_real_folder(self) -> None:
        baseline = script_module("baseline")
        tree = Path(self.tmp.name) / "wt2"
        (tree / ".venv").mkdir(parents=True)
        (tree / ".venv" / "y.txt").write_text("y", encoding="utf-8")
        baseline.drop_links(tree)
        self.assertTrue((tree / ".venv" / "y.txt").is_file())


class ConfigGetTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write(self.root, "ai-kit.json", json.dumps({"commands": {"test": "pytest", "unset": ["A", "B"]},
                                                    "tests": {"baseline_deselect": ["a b", "c"], "baseline_deselect_flag": "--skip"}}))
        run(self.root, "git", "init", "-q", check=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def get(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([PY, str(KIT / "scripts" / "config_get.py"), *args], cwd=self.root, capture_output=True, text=True,
                              encoding="utf-8", check=False)

    def test_a_value_is_printed(self) -> None:
        self.assertEqual(self.get("commands.test").stdout.strip(), "pytest")

    def test_a_list_is_joined_with_spaces(self) -> None:
        self.assertEqual(self.get("commands.unset").stdout.strip(), "A B")

    def test_a_missing_key_prints_the_default(self) -> None:
        r = self.get("commands.nope", "fallback")
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "fallback"))

    def test_a_missing_key_without_default_fails(self) -> None:
        r = self.get("commands.nope")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no commands.nope", r.stderr)

    def test_has_checks_list_membership(self) -> None:
        self.assertEqual(self.get("--has", "commands.unset", "A").returncode, 0)
        self.assertEqual(self.get("--has", "commands.unset", "Z").returncode, 1)
        self.assertEqual(self.get("--has", "commands.test", "pytest").returncode, 1)

    def test_no_arguments_prints_usage(self) -> None:
        self.assertEqual(self.get().returncode, 2)

    def test_deselect_prints_the_quoted_flags(self) -> None:
        self.assertEqual(self.get("--deselect").stdout.strip(), "--skip 'a b' --skip c")


@unittest.skipUnless(BASH, "bash not available")
class DocsRoutingTest(RunSpeedBase):
    def fake_gate(self, supports_docs: bool) -> None:
        text = 'import sys\nif "--help" in sys.argv:\n    print("usage: gate.py' + (" --docs" if supports_docs else "") + '")\n    sys.exit(0)\nprint("ARGS " + " ".join(sys.argv[1:]))\n'
        write(self.p.root, ".claude/skills/prd-flow/scripts/gate.py", text)

    def test_a_slug_runs_the_docs_flag_when_the_gate_supports_it(self) -> None:
        self.fake_gate(True)
        self.assertIn("ARGS --docs demo", self.gates("docs", "demo").stdout)

    def test_a_slug_falls_back_to_the_plain_gate_when_unsupported(self) -> None:
        self.fake_gate(False)
        self.assertIn("ARGS demo", self.gates("docs", "demo").stdout)
        self.assertNotIn("--docs", self.gates("docs", "demo").stdout)

    def test_a_flag_argument_is_passed_through(self) -> None:
        self.fake_gate(True)
        self.assertIn("ARGS --final", self.gates("docs", "--final").stdout)


class CleanOutputsTruncateTest(unittest.TestCase):
    def test_an_output_that_cannot_be_deleted_is_truncated_with_its_own_verb(self) -> None:
        cto = script_module("clean_task_outputs")
        with tempfile.TemporaryDirectory() as tmp:
            big = Path(tmp) / "p" / "s" / "tasks" / "a.output"
            big.parent.mkdir(parents=True)
            big.write_bytes(b"x" * 3 * 1024 * 1024)
            real = Path.unlink

            def locked(self: Path, *args, **kwargs) -> None:
                if self == big:
                    raise PermissionError("in use")
                real(self, *args, **kwargs)

            with mock.patch.object(Path, "unlink", locked):
                removed, errors = cto.clean(Path(tmp), ["mine"], 2, 4000, hard_max_mb=2)
            self.assertEqual(errors, [])
            self.assertEqual(removed[0].verb, "truncated")
            self.assertEqual(big.stat().st_size, 0)

    def test_the_summary_uses_the_truncated_verb(self) -> None:
        cto = script_module("clean_task_outputs")
        with tempfile.TemporaryDirectory() as tmp:
            big = Path(tmp) / "p" / "a.output"
            big.parent.mkdir(parents=True)
            big.write_bytes(b"x" * 3 * 1024 * 1024)
            real = Path.unlink

            def locked(self: Path, *args, **kwargs) -> None:
                if self == big:
                    raise PermissionError("in use")
                real(self, *args, **kwargs)

            with mock.patch.object(Path, "unlink", locked), mock.patch("builtins.print") as shown:
                cto.main(["--root", tmp, "--slug", "mine", "--hard-max-mb", "2"])
            printed = " ".join(str(c.args[0]) for c in shown.call_args_list if c.args)
            self.assertIn("truncated", printed)


if __name__ == "__main__":
    unittest.main()
