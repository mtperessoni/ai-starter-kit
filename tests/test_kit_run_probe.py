"""run_probe.py (RT02, RT07) and the gates.sh targets that go through it (RT08)."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from test_kit_scripts import BASH, PY, Project, run

KIT = Path(__file__).resolve().parents[1] / "kit"
PROBE = str(KIT / "scripts" / "run_probe.py")
sys.path.insert(0, str(KIT / "scripts"))

import run_probe  # noqa: E402

PYTEST_SUMMARY = "print('=== FAILURES ===');print('=========== 2 failed, 5 passed, 1 skipped in 0.12s ===========')"
UNITTEST_SUMMARY = "import sys;print('Ran 7 tests in 0.003s',file=sys.stderr);print('FAILED (failures=2, errors=1)',file=sys.stderr)"


def probe(root: Path, label: str, *cmd: str, env: dict | None = None):
    full = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    full.pop("AI_KIT_CONTEXT", None)
    full.pop("CLAUDE_AGENT_ID", None)
    full.update(env or {})
    import subprocess

    return subprocess.run(
        [PY, PROBE, "--label", label, "--root", str(root), "--", *cmd],
        capture_output=True, text=True, encoding="utf-8", env=full, check=False,
    )


def lines(root: Path, context: str) -> list[dict]:
    path = root / ".ai-kit" / "runs" / context / "resources.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]


class RunProbeTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_exit_code_passes_through(self) -> None:
        self.assertEqual(probe(self.root, "t", PY, "-c", "pass", env={"AI_KIT_CONTEXT": "c"}).returncode, 0)
        self.assertEqual(probe(self.root, "t", PY, "-c", "raise SystemExit(3)", env={"AI_KIT_CONTEXT": "c"}).returncode, 3)

    def test_output_passes_through_unchanged(self) -> None:
        r = probe(self.root, "t", PY, "-c", "import sys;print('out line');print('err line',file=sys.stderr)",
                  env={"AI_KIT_CONTEXT": "c"})
        self.assertEqual(r.stdout.strip(), "out line")
        self.assertEqual(r.stderr.strip(), "err line")

    def test_a_resources_line_records_label_time_exit_and_disk(self) -> None:
        probe(self.root, "related", PY, "-c", "raise SystemExit(3)", env={"AI_KIT_CONTEXT": "c"})
        (rec,) = lines(self.root, "c")
        self.assertEqual((rec["label"], rec["exit"]), ("related", 3))
        self.assertGreaterEqual(rec["sec"], 0)
        self.assertIsNotNone(rec["disk_free_gb_before"])
        self.assertIsNotNone(rec["disk_free_gb_after"])
        self.assertIn("raise SystemExit(3)", rec["cmd"])
        self.assertIsNone(rec["agent"])
        for key in ("ts", "mem_peak_mb", "tests_collected", "tests_failed"):
            self.assertIn(key, rec)

    def test_memory_peak_sees_a_200_mb_child(self) -> None:
        probe(self.root, "m", PY, "-c", "b=bytearray(200*1024*1024); import time; time.sleep(1)", env={"AI_KIT_CONTEXT": "c"})
        (rec,) = lines(self.root, "c")
        self.assertIsNotNone(rec["mem_peak_mb"])
        self.assertGreater(rec["mem_peak_mb"], 150)

    def test_pytest_and_unittest_summaries_are_parsed(self) -> None:
        probe(self.root, "p", PY, "-c", PYTEST_SUMMARY, env={"AI_KIT_CONTEXT": "c"})
        probe(self.root, "u", PY, "-c", UNITTEST_SUMMARY, env={"AI_KIT_CONTEXT": "c"})
        py, ut = lines(self.root, "c")
        self.assertEqual((py["tests_collected"], py["tests_failed"]), (8, 2))
        self.assertEqual((ut["tests_collected"], ut["tests_failed"]), (7, 3))

    def test_jest_summary_and_no_summary(self) -> None:
        self.assertEqual(run_probe.parse_summary("Tests:       1 failed, 4 passed, 5 total\n"), (5, 1))
        self.assertEqual(run_probe.parse_summary("nothing here"), (None, None))

    def test_the_agent_comes_from_the_environment_and_secrets_are_redacted(self) -> None:
        probe(self.root, "t", PY, "-c", "pass", "API_TOKEN=abc123", env={"AI_KIT_CONTEXT": "c", "CLAUDE_AGENT_ID": "a1"})
        (rec,) = lines(self.root, "c")
        self.assertEqual(rec["agent"], "a1")
        self.assertIn("API_TOKEN=***", rec["cmd"])
        self.assertNotIn("abc123", rec["cmd"])

    def test_a_command_that_cannot_start_returns_127(self) -> None:
        self.assertEqual(probe(self.root, "t", "no-such-binary-xyz", env={"AI_KIT_CONTEXT": "c"}).returncode, 127)

    def test_context_follows_env_then_current_file_then_branch_then_default(self) -> None:
        self.assertEqual(run_probe.context(self.root, {}), "default")
        run(self.root, "git", "init", "-q", "-b", "feat/x-y", check=True)
        run(self.root, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "i", check=True)
        self.assertEqual(run_probe.context(self.root, {}), "feat-x-y")
        current = self.root / ".ai-kit" / "runs" / "current"
        current.parent.mkdir(parents=True)
        current.write_text("my-slug\nignored\n", encoding="utf-8")
        self.assertEqual(run_probe.context(self.root, {}), "my-slug")
        self.assertEqual(run_probe.context(self.root, {"AI_KIT_CONTEXT": "from-env"}), "from-env")

    def test_context_from_env_names_the_run_folder(self) -> None:
        probe(self.root, "t", PY, "-c", "pass", env={"AI_KIT_CONTEXT": "env-ctx"})
        self.assertEqual(len(lines(self.root, "env-ctx")), 1)


@unittest.skipUnless(BASH, "bash not available")
class GatesProbeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()

    def tearDown(self) -> None:
        self.p.close()

    def gates(self, *args: str, env: dict | None = None):
        saved = {k: os.environ.get(k) for k in (env or {})}
        os.environ.update(env or {})
        try:
            return run(self.p.root, BASH, "scripts/gates.sh", *args)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_context_writes_the_current_file(self) -> None:
        r = self.gates("context", "003-orders")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = (self.p.root / ".ai-kit" / "runs" / "current").read_text(encoding="utf-8")
        self.assertEqual(text, "003-orders\n")

    def test_related_goes_through_the_probe(self) -> None:
        self.gates("context", "ctx1")
        r = self.gates("related", "src/features/orders/order_service.py")
        self.assertIn("FAILED fake::test_a", r.stdout, r.stdout + r.stderr)
        (rec,) = lines(self.p.root, "ctx1")
        self.assertEqual(rec["label"], "related")
        self.assertIn("exit", rec)

    def test_retro_calls_scripts_retro(self) -> None:
        (self.p.root / "scripts" / "retro.py").write_text("import sys;print('retro', *sys.argv[1:])\n", encoding="utf-8")
        r = self.gates("retro", "--context", "x")
        self.assertIn("retro --context x", r.stdout, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
