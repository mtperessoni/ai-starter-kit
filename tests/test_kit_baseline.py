"""TS43, TS48, TS52: gates.sh baseline (worktree, cache, lock, watchdog), the Python resolver, red, the close reuse, output cap."""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tests.test_kit_scripts import BASH, KIT, PY, Project, run, write

RUNNER = """\
import json, os, sys, time
with open(os.environ["RUN_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"cwd": os.getcwd(), "argv": sys.argv[1:]}) + "\\n")
time.sleep(float(os.environ.get("RUN_SLEEP", "0")))
flag = os.environ.get("RUN_FLAKY_FLAG")
if flag and os.path.exists(flag):
    os.remove(flag)
    print("FAILED new::flaky")
if os.environ.get("RUN_FAIL"):
    print("FAILED " + os.environ["RUN_FAIL"])
print("1 failed" if os.environ.get("RUN_FAIL") else "1 passed")
sys.exit(1 if os.environ.get("RUN_FAIL") else 0)
"""


@unittest.skipUnless(BASH, "bash not available")
class GatesBase(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        self.tmp = tempfile.TemporaryDirectory()
        self.runner = Path(self.tmp.name) / "runner.py"
        self.runner.write_text(RUNNER, encoding="utf-8")
        self.log = Path(self.tmp.name) / "runs.jsonl"
        self.env = {**os.environ, "RUN_LOG": str(self.log), "PYTHONIOENCODING": "utf-8"}
        self.configure(commands={"test": f'"{PY}" "{self.runner}"', "offline_args": "", "no_coverage_args": ""})

    def tearDown(self) -> None:
        self.p.close()
        self.tmp.cleanup()

    def configure(self, **sections: dict) -> None:
        path = self.p.root / "ai-kit.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        for name, values in sections.items():
            config[name].update(values)
        path.write_text(json.dumps(config), encoding="utf-8")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "config " + str(time.time()), "--allow-empty", check=True)

    def gates(self, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([BASH, "scripts/gates.sh", *args], cwd=self.p.root, capture_output=True, text=True,
                              encoding="utf-8", env=env or self.env, check=False)

    def runs(self) -> list[dict]:
        if not self.log.is_file():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines() if line.strip()]

    def state(self, slug: str, name: str) -> Path:
        return self.p.root / ".claude/prd-flow/state" / slug / name


class BaselineTest(GatesBase):
    def test_baseline_runs_in_a_worktree_and_removes_it(self) -> None:
        r = self.gates("baseline", "s1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        runs = self.runs()
        self.assertEqual(len(runs), 1)
        self.assertNotEqual(Path(runs[0]["cwd"]).resolve(), self.p.root.resolve())
        self.assertFalse(Path(runs[0]["cwd"]).exists())
        listing = run(self.p.root, "git", "worktree", "list", "--porcelain").stdout
        self.assertEqual(listing.count("worktree "), 1, listing)
        self.assertTrue(self.state("s1", "baseline-failures.txt").is_file())

    def test_baseline_records_the_failures_the_close_step_reads(self) -> None:
        r = self.gates("baseline", "s1", env={**self.env, "RUN_FAIL": "old::broken"})
        self.assertIn("baseline failures: 1", r.stdout, r.stdout + r.stderr)
        self.assertEqual(self.state("s1", "baseline-failures.txt").read_text(encoding="utf-8").strip(), "old::broken")

    def test_a_second_slug_at_the_same_commit_hits_the_cache(self) -> None:
        self.gates("baseline", "s1", env={**self.env, "RUN_FAIL": "old::broken"})
        r = self.gates("baseline", "s2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("cached", r.stdout)
        self.assertEqual(len(self.runs()), 1)
        self.assertEqual(self.state("s2", "baseline-failures.txt").read_text(encoding="utf-8").strip(), "old::broken")

    def test_a_new_commit_runs_again(self) -> None:
        self.gates("baseline", "s1")
        write(self.p.root, "yarn.lock", "changed\n")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "lock", check=True)
        self.gates("baseline", "s2")
        self.assertEqual(len(self.runs()), 2)

    def test_the_deselect_list_reaches_the_runner(self) -> None:
        self.configure(tests={"baseline_deselect": ["tests/test_a.py::test_hang"]})
        self.gates("baseline", "s1")
        argv = self.runs()[0]["argv"]
        self.assertEqual(argv, ["--deselect", "tests/test_a.py::test_hang"])

    def test_a_concurrent_run_waits_for_the_lock_and_reuses_the_result(self) -> None:
        slow = subprocess.Popen([BASH, "scripts/gates.sh", "baseline", "a"], cwd=self.p.root, env={**self.env, "RUN_SLEEP": "3"},
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.time() + 20
            while not self.log.is_file() and time.time() < deadline:
                time.sleep(0.2)
            r = self.gates("baseline", "b")
            slow.communicate(timeout=60)
        finally:
            if slow.poll() is None:
                slow.kill()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.runs()), 1)
        self.assertTrue(self.state("b", "baseline-failures.txt").is_file())

    def test_a_stale_lock_is_taken_over(self) -> None:
        self.gates("baseline", "s1")
        for lock in (self.p.root / ".claude/prd-flow/state/_baseline").glob("*.lock"):
            lock.unlink()
        base = self.p.root / ".claude/prd-flow/state/_baseline"
        for cached in base.glob("*"):
            if cached.is_dir():
                import shutil

                shutil.rmtree(cached)
        head = run(self.p.root, "git", "rev-parse", "HEAD").stdout.strip()
        lock = base / f"{head[:12]}.lock"
        lock.write_text("999999 1\n", encoding="utf-8")
        os_time = time.time() - 7200
        os.utime(lock, (os_time, os_time))
        r = self.gates("baseline", "s2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(self.runs()), 2)

    def test_the_watchdog_kills_a_run_with_no_progress(self) -> None:
        self.configure(tests={"baseline_idle_seconds": 2})
        started = time.time()
        r = self.gates("baseline", "s1", env={**self.env, "RUN_SLEEP": "60"})
        self.assertLess(time.time() - started, 45)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("no progress", r.stdout + r.stderr)
        self.assertTrue(self.state("s1", "baseline-failures.txt").is_file())
        listing = run(self.p.root, "git", "worktree", "list", "--porcelain").stdout
        self.assertEqual(listing.count("worktree "), 1, listing)

    def test_bg_returns_at_once_and_the_result_arrives(self) -> None:
        r = self.gates("baseline", "s1", "--bg", env={**self.env, "RUN_SLEEP": "1"})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("background", r.stdout)
        deadline = time.time() + 60
        while not self.state("s1", "baseline-failures.txt").is_file() and time.time() < deadline:
            time.sleep(0.3)
        self.assertTrue(self.state("s1", "baseline-failures.txt").is_file())
        bg_log = self.state("s1", "baseline.bg.log")
        while time.time() < deadline:
            try:
                os.rename(bg_log, bg_log)
                break
            except OSError:
                time.sleep(0.3)

    def test_a_real_node_modules_link_is_never_followed(self) -> None:
        keep = Path(self.tmp.name) / "real_modules"
        keep.mkdir()
        (keep / "x.txt").write_text("x", encoding="utf-8")
        sys.path.insert(0, str(self.p.root / "scripts"))
        try:
            import baseline

            tree = Path(self.tmp.name) / "wt"
            tree.mkdir()
            link = tree / "node_modules"
            try:
                os.symlink(keep, link, target_is_directory=True)
            except OSError:
                self.skipTest("symlinks not permitted")
            baseline.drop_links(tree)
            self.assertFalse(link.exists() or link.is_symlink())
            self.assertTrue((keep / "x.txt").is_file())
        finally:
            sys.path.remove(str(self.p.root / "scripts"))
            sys.modules.pop("baseline", None)


class PythonResolverTest(GatesBase):
    def stub(self, name: str, body: str) -> Path:
        directory = Path(self.tmp.name) / "stubs"
        directory.mkdir(exist_ok=True)
        path = directory / name
        path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8", newline="\n")
        path.chmod(0o755)
        return path

    def test_the_windows_store_path_is_rejected(self) -> None:
        directory = Path(self.tmp.name) / "WindowsApps"
        directory.mkdir()
        fake = directory / "python3"
        fake.write_text("#!/usr/bin/env bash\necho 3\n", encoding="utf-8", newline="\n")
        fake.chmod(0o755)
        r = self.gates("ratchet", env={**self.env, "GATES_PYTHON": str(fake)})
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("Windows Store", r.stderr)

    def test_the_not_found_stub_text_is_rejected_in_both_languages(self) -> None:
        for text in ("Python was not found; run without arguments", "Python não foi encontrado; execute sem argumentos"):
            fake = self.stub("python3", f"echo '{text}'\nexit 49\n")
            r = self.gates("ratchet", env={**self.env, "GATES_PYTHON": str(fake)})
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("not a usable Python 3", r.stderr)

    def test_probing_skips_a_stub_and_finds_the_real_python(self) -> None:
        self.stub("python3", "echo 'Python was not found'\nexit 49\n")
        self.stub("python", "echo 'Python was not found'\nexit 49\n")
        env = {**self.env, "PATH": str(Path(self.tmp.name) / "stubs") + os.pathsep + str(Path(PY).parent) + os.pathsep + self.env["PATH"]}
        env.pop("GATES_PYTHON", None)
        r = self.gates("ratchet", env=env)
        self.assertIn("ratchet", r.stdout + r.stderr)
        self.assertNotIn("not a usable", r.stderr)

    def test_gates_sh_never_calls_bare_python(self) -> None:
        text = (KIT / "scripts/gates.sh").read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), 1):
            code = line.split("#", 1)[0]
            self.assertNotRegex(code, r"(^|[\s(`$])python(3)?\s+(-|scripts/|\.claude)", f"line {number}: {line}")
        self.assertNotIn("python -", text)
        self.assertNotIn("<<'PY'", text)


class RedAndRelatedTest(GatesBase):
    def test_red_prints_the_exit_code_of_a_failing_test(self) -> None:
        r = self.gates("red", "tests/x.py::t", env={**self.env, "RUN_FAIL": "x::t"})
        self.assertIn("Red: ", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.runs()[0]["argv"][-1], "tests/x.py::t")

    def test_red_on_a_passing_test_says_red_zero_and_fails(self) -> None:
        r = self.gates("red", "tests/x.py::t")
        self.assertIn("Red: 0", r.stdout)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_related_arguments_are_never_interpreted_by_a_shell(self) -> None:
        marker = self.p.root / "PWNED"
        self.gates("related", f"src/x.py;touch {marker.name}", "src/a (1).py", "src/b[2].py")
        self.assertFalse(marker.exists())


class CloseReuseTest(GatesBase):
    def prepare(self, env: dict) -> None:
        self.configure(commands={"lint": f'"{PY}" -c "pass"'}, tests={"rerun_ids": True})
        from tests.test_kit_scripts import KIT as kit

        import shutil

        shutil.copytree(kit / "docs" / "templates", self.p.root / "docs" / "templates", dirs_exist_ok=True)
        self.gates("html")
        run(self.p.root, "git", "add", "-A", check=True)
        run(self.p.root, "git", "commit", "-q", "-m", "html", check=True)
        self.gates("baseline", "demo", env=env)

    def close(self, env: dict) -> subprocess.CompletedProcess:
        return subprocess.run([PY, "scripts/close_gate.py", "demo"], cwd=self.p.root, capture_output=True, text=True, encoding="utf-8",
                              env={**env, "GATES_BASH": BASH}, check=False)

    def test_close_reuses_a_fresh_full_run_without_running_again(self) -> None:
        self.prepare(self.env)
        self.gates("compare", "demo")
        before = len(self.runs())
        r = self.close(self.env)
        self.assertEqual(len(self.runs()), before, r.stdout)
        self.assertIn("compare ok", r.stdout)
        self.assertIn("reused", r.stdout)

    def test_close_reports_a_running_baseline_and_never_waits_for_it(self) -> None:
        self.prepare(self.env)
        folder = self.p.root / ".claude" / "prd-flow" / "state" / "demo"
        (folder / "baseline-failures.txt").unlink()
        (folder / "baseline.status").write_text("running" + chr(10), encoding="utf-8")
        r = self.close(self.env)
        self.assertIn("still running", r.stdout)
        self.assertIn("completion", r.stdout)
        self.assertNotIn("wait until", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_close_without_a_compare_result_never_runs_the_suite(self) -> None:
        self.prepare(self.env)
        before = len(self.runs())
        r = self.close(self.env)
        self.assertEqual(len(self.runs()), before, r.stdout)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("no compare result", r.stdout)

    def test_close_reruns_only_the_new_failing_ids_of_the_last_full_run(self) -> None:
        self.prepare(self.env)
        flag = Path(self.tmp.name) / "flaky.flag"
        flag.write_text("1", encoding="utf-8")
        env = {**self.env, "RUN_FLAKY_FLAG": str(flag)}
        self.gates("compare", "demo", env=env)
        before = len(self.runs())
        r = self.close(env)
        runs = self.runs()
        self.assertEqual(len(runs), before + 1, r.stdout)
        self.assertEqual(runs[-1]["argv"][-1], "new::flaky")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_an_edit_after_the_full_run_makes_it_stale(self) -> None:
        self.prepare(self.env)
        self.gates("compare", "demo")
        write(self.p.root, "src/features/orders/order_service.py", '"""ORD-01."""\nx = 2\n')
        before = len(self.runs())
        r = self.close(self.env)
        self.assertEqual(len(self.runs()), before, r.stdout)
        self.assertIn("no compare result", r.stdout)


class CleanOutputsTest(unittest.TestCase):
    def test_a_runaway_output_over_the_hard_cap_is_deleted_in_any_project_folder(self) -> None:
        sys.path.insert(0, str(KIT / "scripts"))
        try:
            import clean_task_outputs as cto

            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                big = root / "other-project" / "s" / "tasks" / "a.output"
                small = root / "other-project" / "s" / "tasks" / "b.output"
                big.parent.mkdir(parents=True)
                big.write_bytes(b"x" * 3 * 1024 * 1024)
                small.write_bytes(b"x")
                removed, errors = cto.clean(root, ["mine"], 2, 4000, hard_max_mb=2)
                self.assertEqual([r.path for r in removed], [big])
                self.assertIn("hard cap", removed[0].reason)
                self.assertFalse(big.exists())
                self.assertTrue(small.exists())
                self.assertEqual(errors, [])
        finally:
            sys.path.remove(str(KIT / "scripts"))
            sys.modules.pop("clean_task_outputs", None)


if __name__ == "__main__":
    unittest.main()
