"""Wave 1 review fixes (R2 to R7, R21, R22): rerun exit code, compare stamp, deselect, baseline status and links, config_get, docs routing."""

import json
import os
import shutil
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

    def test_the_stamp_is_published_only_after_the_run(self) -> None:
        self.gates("compare", "demo")
        self.assertTrue(self.state("demo", "final.stamp").is_file())
        self.assertFalse(self.state("demo", "final.stamp.pending").exists())
        self.assertTrue(self.state("demo", "exit").is_file())


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

    def test_a_new_failure_without_runnable_ids_fails_from_the_compare_result_without_a_run(self) -> None:
        self.prepare(False)
        env = {**self.env, "RUN_FAIL": "Some title"}
        self.gates("compare", "demo", env=env)
        before = len(self.runs())
        r = self.close(env)
        self.assertEqual(len(self.runs()), before, r.stdout)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("NEW Some", r.stdout)
        self.assertNotIn("all passed", r.stdout)


NO_SUMMARY_RUNNER = """\
import json, os, sys
with open(os.environ["RUN_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"cwd": os.getcwd(), "argv": sys.argv[1:]}) + "\\n")
print(os.environ.get("RUN_TEXT", "collecting ..."))
sys.exit(int(os.environ.get("RUN_EXIT", "0")))
"""


class OnePassGatesTest(RunSpeedBase):
    def seed(self, slug: str = "demo") -> None:
        folder = self.p.root / ".claude/prd-flow/state" / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "baseline-failures.txt").write_text("", encoding="utf-8")

    def test_compare_fails_when_the_run_ends_without_its_summary_line(self) -> None:
        self.runner.write_text(NO_SUMMARY_RUNNER, encoding="utf-8")
        self.seed()
        r = self.gates("compare", "demo")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("suite ended without its summary line", r.stdout)
        self.assertFalse((self.p.root / ".claude/prd-flow/state/_compare").exists())

    def test_baseline_fails_when_the_run_ends_without_its_summary_line(self) -> None:
        self.runner.write_text(NO_SUMMARY_RUNNER, encoding="utf-8")
        r = self.gates("baseline", "s1")
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("suite ended without its summary line", r.stdout + r.stderr)
        self.assertFalse(self.state("s1", "baseline-failures.txt").exists())
        r = self.gates("baseline", "s2")
        self.assertNotEqual(r.returncode, 0, "a failed baseline must not be cached")

    def test_a_nonzero_runner_exit_without_any_failure_line_is_not_a_pass(self) -> None:
        self.runner.write_text(NO_SUMMARY_RUNNER, encoding="utf-8")
        self.seed()
        r = self.gates("compare", "demo", env={**self.env, "RUN_TEXT": "1 passed", "RUN_EXIT": "5"})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("exited 5 without a failure line", r.stdout)

    def test_a_timeout_or_killed_outcome_counts_as_a_new_failure(self) -> None:
        write(self.p.root, "baseline.txt", "")
        for text in ("+++++ Timeout +++++\n1 passed\n", "Fatal Python error: x\n1 passed\n", "ERROR collecting tests/a.py\n1 error\n"):
            write(self.p.root, "final.log", text)
            r = self.p.py("scripts/new_failures.py", "baseline.txt", "final.log")
            self.assertEqual(r.returncode, 1, text + r.stdout)
            self.assertIn("NEW", r.stdout)

    def test_gates_exports_utf8_and_drops_no_exit_code(self) -> None:
        text = (KIT / "scripts/gates.sh").read_text(encoding="utf-8")
        self.assertIn("export PYTHONUTF8=1", text)
        block = text.split("compare)", 1)[1].split("\n    ;;", 1)[0]
        self.assertNotIn("|| true", block)

    def test_fast_flags_reach_baseline_and_compare_only_when_declared(self) -> None:
        self.seed()
        self.configure(tests={"fast_flags": "--no-cov -n 2"})
        self.gates("baseline", "s1")
        self.gates("compare", "demo")
        self.assertEqual([run["argv"] for run in self.runs()], [["--no-cov", "-n", "2"]] * 2)

    def test_a_docs_only_commit_reuses_the_compare_result_and_a_source_change_does_not(self) -> None:
        self.seed()
        self.gates("compare", "demo")
        write(self.p.root, "docs/prd/x.md", "docs only\n")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "docs(prd): promote demo", check=True)
        r = self.gates("compare", "demo")
        self.assertIn("reused", r.stdout)
        self.assertEqual(len(self.runs()), 1)
        write(self.p.root, "src/features/orders/order_service.py", "x = 9\n")
        self.gates("compare", "demo")
        self.assertEqual(len(self.runs()), 2)

    def test_the_compare_result_is_shared_across_slugs(self) -> None:
        self.seed("a")
        self.seed("b")
        self.gates("compare", "a")
        r = self.gates("compare", "b")
        self.assertIn("reused", r.stdout)
        self.assertEqual(len(self.runs()), 1)


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


TOUCH_RUNNER = """\
import os, sys
open("touched_by_run.txt", "w").write("x")
print("1 passed")
sys.exit(int(os.environ.get("RUN_EXIT", "0")))
"""


@unittest.skipUnless(BASH, "bash not available")
class CompareCloseReview2Test(RunSpeedBase):
    def prepare(self, **tests: object) -> None:
        self.configure(commands={"lint": f'"{PY}" -c "pass"'}, tests=tests)
        shutil.copytree(KIT / "docs" / "templates", self.p.root / "docs" / "templates", dirs_exist_ok=True)
        self.gates("html")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "html", check=True)
        self.gates("baseline", "demo")

    def close(self, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([PY, "scripts/close_gate.py", "demo", *args], cwd=self.p.root, capture_output=True, text=True,
                              encoding="utf-8", env={**(env or self.env), "GATES_BASH": BASH}, check=False)

    def test_fix_files_replaces_every_files_placeholder(self) -> None:
        self.configure(commands={"fix_file": "echo {files} >> out.txt && echo {files} >> out.txt"})
        r = self.gates("fix-files", "a.py", "b.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((self.p.root / "out.txt").read_text(encoding="utf-8").split("\n")[:2], ["a.py b.py", "a.py b.py"])

    def test_the_runner_exit_code_is_stored_and_close_applies_it(self) -> None:
        self.prepare()
        env = {**self.env, "RUN_EXIT": "5"}
        self.gates("compare", "demo", env=env)
        self.assertEqual(self.state("demo", "exit").read_text(encoding="utf-8").strip(), "5")
        r = self.close(env=env)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("compare ok", r.stdout)
        self.assertIn("exited 5", r.stdout)

    def test_a_close_never_reads_a_result_without_its_exit_code(self) -> None:
        self.prepare()
        self.gates("compare", "demo")
        self.state("demo", "exit").unlink()
        for cached in (self.p.root / ".claude/prd-flow/state/_compare").glob("*/exit"):
            cached.unlink()
        r = self.close()
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("compare ok", r.stdout)

    def test_the_content_hash_covers_the_test_relevant_root_files_and_hash_paths(self) -> None:
        self.prepare(hash_paths=["docs"])
        close_gate = script_module("close_gate")
        before = close_gate.content_hash(self.p.root)
        for name in ("package.json", "pyproject.toml", "conftest.py", "vitest.config.ts", "tsconfig.json", ".nvmrc", ".env.test"):
            write(self.p.root, name, "{}\n")
            after = close_gate.content_hash(self.p.root)
            self.assertNotEqual(before, after, name)
            before = after
        write(self.p.root, "docs/arch/rule.md", "x\n")
        self.assertNotEqual(before, close_gate.content_hash(self.p.root))

    def test_the_stamp_is_taken_before_the_run(self) -> None:
        self.runner.write_text(TOUCH_RUNNER, encoding="utf-8")
        self.gates("compare", "demo")
        stamp = self.state("demo", "final.stamp").read_text(encoding="utf-8").strip()
        self.assertNotEqual(stamp, script_module("close_gate").tree_stamp(self.p.root))

    def test_the_summary_is_searched_in_the_last_lines_only(self) -> None:
        new_failures = script_module("new_failures")
        log = self.p.root / "nested.log"
        log.write_text("5 passed\n" + "noise\n" * 40, encoding="utf-8")
        self.assertFalse(new_failures.has_summary(log, {}))
        log.write_text("noise\n" * 40 + "5 passed\n", encoding="utf-8")
        self.assertTrue(new_failures.has_summary(log, {}))

    def test_a_failed_baseline_deletes_the_earlier_failures_file(self) -> None:
        self.gates("baseline", "s1")
        self.assertTrue(self.state("s1", "baseline-failures.txt").is_file())
        self.runner.write_text(NO_SUMMARY_RUNNER, encoding="utf-8")
        self.configure(tests={"fast_flags": "--other"})
        self.gates("baseline", "s1")
        self.assertFalse(self.state("s1", "baseline-failures.txt").exists())

    def test_close_requires_an_ok_baseline_status(self) -> None:
        self.prepare()
        self.gates("compare", "demo")
        self.state("demo", "baseline.status").write_text("failed no summary\n", encoding="utf-8")
        r = self.close()
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("baseline", r.stdout)

    def test_close_never_runs_the_ids_and_prints_them_when_rerun_ids_is_true(self) -> None:
        self.prepare(rerun_ids=True)
        env = {**self.env, "RUN_FAIL": "Some title"}
        self.gates("compare", "demo", env=env)
        before = len(self.runs())
        r = self.close(env=env)
        self.assertEqual(len(self.runs()), before, r.stdout)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("gates.sh rerun demo", r.stdout)

    def test_every_subprocess_call_in_close_goes_through_the_timeout_wrapper(self) -> None:
        text = (KIT / "scripts/close_gate.py").read_text(encoding="utf-8")
        self.assertEqual(text.count("subprocess.run("), 1)
        self.assertIn("timeout=", text)

    def test_compare_reads_the_config_keys_in_one_process(self) -> None:
        text = (KIT / "scripts/gates.sh").read_text(encoding="utf-8")
        block = text.split("compare)", 1)[1].split("\n    ;;", 1)[0]
        self.assertIn("--many", text)
        self.assertNotIn("$(cmd ", block)
        self.assertNotIn("fast_flags)", block)
        offline_fn = text.split("offline() {", 1)[1].split("\n}", 1)[0]
        self.assertNotIn("$(cmd ", offline_fn)

    def test_a_json_escaped_windows_python_path_resolves(self) -> None:
        self.configure(commands={"python": PY})
        r = self.gates("python")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.strip(), PY)

    def test_close_with_case_c4_skips_compare_and_baseline(self) -> None:
        self.configure(commands={"lint": f'"{PY}" -c "pass"'})
        shutil.copytree(KIT / "docs" / "templates", self.p.root / "docs" / "templates", dirs_exist_ok=True)
        self.gates("html")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "html", check=True)
        r = self.gates("close", "demo", "--case", "C4")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("C4", r.stdout)
        self.assertIn("skipped", r.stdout)
        self.assertEqual(self.runs(), [])
        self.assertEqual(self.gates("close", "demo", "--case", "C9").returncode, 2)


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
