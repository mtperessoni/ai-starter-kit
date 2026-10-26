"""Faster gates.sh: one config read per target, the probe only on long targets, the ratchet at the end of lint-files (not in related)."""

import json
import os
import stat
import unittest
from pathlib import Path

from tests.test_kit_baseline import GatesBase
from tests.test_kit_scripts import PY, write

STUB_RATCHET = """\
import os, sys
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ratchet.ran"), "a").write("x\\n")
sys.exit(int(os.environ.get("RATCHET_EXIT", "0")))
"""


class FasterGatesTest(GatesBase):
    def setUp(self) -> None:
        super().setUp()
        self.ctx = "faster"
        self.env = {**self.env, "AI_KIT_CONTEXT": self.ctx}
        write(self.p.root, "scripts/ratchet.py", STUB_RATCHET)
        self.marker = self.p.root / "scripts" / "ratchet.ran"

    def resources(self) -> list[dict]:
        path = self.p.root / ".ai-kit" / "runs" / self.ctx / "resources.jsonl"
        if not path.is_file():
            return []
        return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

    def config_reads(self, *args: str) -> int:
        wrapper = Path(self.tmp.name) / "py_spy.sh"
        calls = Path(self.tmp.name) / "py_calls.txt"
        calls.write_text("", encoding="utf-8")
        wrapper.write_text(f'#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "{calls.as_posix()}"\nexec "{Path(PY).as_posix()}" "$@"\n', encoding="utf-8")
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
        r = self.gates(*args, env={**self.env, "GATES_PYTHON": str(wrapper)})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return sum("config_get.py" in line for line in calls.read_text(encoding="utf-8").splitlines())

    def test_one_reads_the_config_in_one_python_call(self) -> None:
        self.assertEqual(self.config_reads("one", "tests/test_a.py"), 1)

    def test_offline_and_lint_files_read_the_config_in_one_python_call(self) -> None:
        self.assertEqual(self.config_reads("offline", "tests/test_a.py"), 1)
        self.configure(commands={"lint_file": f'"{PY}" -c "pass"'})
        self.assertEqual(self.config_reads("lint-files", "a.py"), 1)

    def test_compare_reads_config_and_deselect_in_one_python_call(self) -> None:
        self.assertEqual(self.config_reads("compare", "demo"), 1)

    def test_one_runs_without_the_probe(self) -> None:
        r = self.gates("one", "tests/test_a.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.runs()[-1]["argv"], ["tests/test_a.py"])
        self.assertEqual(self.resources(), [])

    def test_the_whole_offline_target_still_goes_through_the_probe_and_takes_files(self) -> None:
        r = self.gates("offline", "tests/test_a.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.runs()[-1]["argv"], ["tests/test_a.py"])
        self.assertEqual([x["label"] for x in self.resources()], ["offline"])

    def test_compare_goes_through_the_probe(self) -> None:
        self.gates("compare", "demo")
        self.assertEqual([x["label"] for x in self.resources()], ["offline"])

    def test_related_runs_no_ratchet_and_no_probe(self) -> None:
        write(self.p.root, "src/features/orders/order_service.py", '"""ORD-01."""\nx = 2\n')
        self.gates("related", "src/features/orders/order_service.py")
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.resources(), [])

    def spy_calls(self, *args: str) -> list[str]:
        wrapper = Path(self.tmp.name) / "py_spy2.sh"
        calls = Path(self.tmp.name) / "py_calls2.txt"
        calls.write_text("", encoding="utf-8")
        wrapper.write_text(f'#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "{calls.as_posix()}"\nexec "{Path(PY).as_posix()}" "$@"\n', encoding="utf-8")
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
        self.gates(*args, env={**self.env, "GATES_PYTHON": str(wrapper)})
        return calls.read_text(encoding="utf-8").splitlines()

    def test_related_makes_no_help_probe_and_one_selector_call(self) -> None:
        write(self.p.root, "src/features/orders/order_service.py", '"""ORD-01."""\nx = 2\n')
        calls = self.spy_calls("related", "src/features/orders/order_service.py")
        self.assertFalse([c for c in calls if "--help" in c], calls)
        self.assertEqual(len([c for c in calls if "related_tests.py" in c]), 1, calls)

    def test_related_leaves_tests_always_out_unless_asked(self) -> None:
        write(self.p.root, "tests/test_architecture.py", "x = 1\n")
        self.configure(tests={"always": ["tests/test_architecture.py"], "runner": f'"{PY}" "{self.runner}" {{files}}'})
        write(self.p.root, "src/features/orders/order_service.py", '"""ORD-01."""\nx = 2\n')
        self.gates("related", "src/features/orders/order_service.py")
        plain = [r["argv"] for r in self.runs()]
        self.assertFalse(any("tests/test_architecture.py" in a for a in plain), plain)
        self.gates("related", "--with-always", "src/features/orders/order_service.py")
        self.assertTrue(any("tests/test_architecture.py" in r["argv"] for r in self.runs()))

    def test_python_in_the_test_command_is_the_resolved_interpreter(self) -> None:
        self.configure(commands={"test": f'{{python}} "{self.runner}"'})
        r = self.gates("one", "tests/test_a.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.runs()[-1]["argv"], ["tests/test_a.py"])
        r = self.gates("offline", "tests/test_a.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_lint_files_ends_with_the_ratchet(self) -> None:
        self.configure(commands={"lint_file": f'"{PY}" -c "pass"'})
        r = self.gates("lint-files", "a.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("lint-files ok", r.stdout)
        self.assertTrue(self.marker.exists())

    def test_lint_files_fails_when_the_ratchet_fails(self) -> None:
        self.configure(commands={"lint_file": f'"{PY}" -c "pass"'})
        r = self.gates("lint-files", "a.py", env={**self.env, "RATCHET_EXIT": "1"})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("lint-files ok", r.stdout)

    def test_a_lint_failure_still_exits_with_its_code_and_runs_the_ratchet(self) -> None:
        self.configure(commands={"lint_file": f'"{PY}" -c "raise SystemExit(3)"'})
        r = self.gates("lint-files", "a.py")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("lint-files FAILED (exit 3)", r.stdout)
        self.assertTrue(self.marker.exists())

    def test_the_ratchet_target_and_the_close_gate_keep_the_ratchet(self) -> None:
        self.gates("ratchet")
        self.assertTrue(self.marker.exists())
        self.assertIn('("ratchet", ["ratchet"])', (self.p.root / "scripts" / "close_gate.py").read_text(encoding="utf-8"))
        self.assertIn('("ratchet", ["ratchet"])', (self.p.root / "scripts" / "verify.py").read_text(encoding="utf-8"))

    def test_project_targets_still_delegate(self) -> None:
        write(self.p.root, "scripts/gates.project.sh", 'echo "project $*"\n')
        self.configure(commands={"project_targets": ["one"]})
        r = self.gates("one", "x")
        self.assertIn("project one x", r.stdout, r.stdout + r.stderr)
        self.assertEqual(self.runs(), [])


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    unittest.main()
