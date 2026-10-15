"""post_tool_hook.py: lint after an edit, the failing test streak, the main-thread checkpoint (audit 2026-10-15 H02, H06, H08)."""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "kit" / "scripts" / "post_tool_hook.py"
FAIL_LINT = f'"{sys.executable}" -c "import sys; print(\'E101 bad thing in\', sys.argv[1]); sys.exit(1)" {{files}}'
PASS_LINT = f'"{sys.executable}" -c "import sys; sys.exit(0)" {{files}}'


class HookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        (self.root / "README.md").write_text("doc\n", encoding="utf-8")
        self.config(FAIL_LINT)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def config(self, lint: str, **post_tool) -> None:
        cfg = {"code_extensions": [".py"], "source_dirs": ["src"], "generated_patterns": ["**/gen_*.py"],
               "commands": {"lint_file": lint}, "tests": {"failure_regex": "^FAILED (\\S+)"},
               "post_tool": {"lint_debounce_s": 0, **post_tool}}
        (self.root / "ai-kit.json").write_text(json.dumps(cfg), encoding="utf-8")

    def wait_for_lint(self) -> None:
        hooks = self.root / ".ai-kit" / "runs" / "_hooks"
        deadline = time.time() + 30
        while time.time() < deadline:
            if not list(hooks.glob("lint-*.req")):
                return
            time.sleep(0.2)
        self.fail("the lint worker did not finish")

    def edit_then_next_call(self, path: str) -> tuple[str, str]:
        first = self.edit(path)
        self.wait_for_lint()
        return first, self.bash("git status", "PostToolUse")

    def run_hook(self, payload: dict) -> str:
        base = {"session_id": "s1234567xx", "cwd": str(self.root)}
        r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({**base, **payload}), capture_output=True,
                           text=True, timeout=60, env={**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)})
        self.assertEqual(r.returncode, 0, r.stderr)
        if not r.stdout.strip():
            return ""
        return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]

    def edit(self, path: str, event: str = "PostToolUse") -> str:
        return self.run_hook({"hook_event_name": event, "tool_name": "Edit", "agent_id": "ag1",
                              "tool_input": {"file_path": str(self.root / path)}})

    def bash(self, command: str, event: str, agent: str | None = "ag1", stdout: str = "") -> str:
        p = {"hook_event_name": event, "tool_name": "Bash", "tool_input": {"command": command},
             "tool_response": {"stdout": stdout, "stderr": ""}}
        if agent:
            p["agent_id"] = agent
        return self.run_hook(p)

    def test_lint_finding_arrives_on_the_next_call_of_the_same_agent(self):
        first, second = self.edit_then_next_call("src/a.py")
        self.assertEqual(first, "")
        self.assertIn("E101 bad thing", second)
        self.assertIn("src/a.py", second)
        self.assertEqual(self.bash("git status", "PostToolUse"), "")

    def test_another_agent_does_not_receive_the_finding(self):
        self.edit("src/a.py")
        self.wait_for_lint()
        self.assertEqual(self.bash("git status", "PostToolUse", agent="ag2"), "")

    def test_a_file_changed_after_the_lint_started_drops_the_stale_result(self):
        self.config(FAIL_LINT, lint_debounce_s=1)
        self.edit("src/a.py")
        time.sleep(0.1)
        (self.root / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
        self.edit("src/a.py")
        self.wait_for_lint()
        out = self.bash("git status", "PostToolUse")
        self.assertEqual(out.count("E101"), 1)

    def test_clean_lint_is_silent(self):
        self.config(PASS_LINT)
        self.assertEqual(self.edit_then_next_call("src/a.py"), ("", ""))

    def test_non_code_generated_and_outside_files_are_not_linted(self):
        (self.root / "src" / "gen_x.py").write_text("x\n", encoding="utf-8")
        self.assertEqual(self.edit_then_next_call("README.md"), ("", ""))
        self.assertEqual(self.edit_then_next_call("src/gen_x.py"), ("", ""))
        self.assertEqual(self.run_hook({"hook_event_name": "PostToolUse", "tool_name": "Write",
                                        "tool_input": {"file_path": str(Path(tempfile.gettempdir()) / "o.py")}}), "")

    def test_lint_can_be_switched_off(self):
        self.config(FAIL_LINT, lint_after_edit=False)
        self.assertEqual(self.edit_then_next_call("src/a.py"), ("", ""))

    def test_failing_test_streak_warns_at_three_and_stops_at_five(self):
        cmd = "bash scripts/gates.sh one tests/test_a.py"
        self.assertEqual(self.bash(cmd, "PostToolUseFailure"), "")
        self.assertEqual(self.bash(cmd, "PostToolUseFailure"), "")
        self.assertIn("3 test runs in a row failed", self.bash(cmd, "PostToolUseFailure"))
        self.assertEqual(self.bash(cmd, "PostToolUseFailure"), "")
        self.assertIn("hand back", self.bash(cmd, "PostToolUseFailure"))

    def test_a_passing_run_resets_the_streak_and_agents_count_apart(self):
        cmd = "python -m pytest tests/test_a.py -q"
        self.bash(cmd, "PostToolUseFailure")
        self.bash(cmd, "PostToolUseFailure")
        self.bash(cmd, "PostToolUse")
        self.assertEqual(self.bash(cmd, "PostToolUseFailure"), "")
        self.bash(cmd, "PostToolUseFailure", agent="ag2")
        self.assertEqual(self.bash(cmd, "PostToolUseFailure", agent="ag2"), "")

    def test_failure_found_in_output_counts_when_the_exit_code_is_hidden(self):
        cmd = "bash scripts/gates.sh one t.py > log 2>&1; tail -5 log"
        for _ in range(2):
            self.bash(cmd, "PostToolUse", stdout="FAILED tests/t.py::x\n1 failed")
        self.assertIn("3 test runs in a row failed", self.bash(cmd, "PostToolUse", stdout="FAILED tests/t.py::x"))

    def test_other_commands_do_not_touch_the_streak(self):
        cmd = "vitest run src/a.test.ts"
        self.bash(cmd, "PostToolUseFailure")
        self.bash(cmd, "PostToolUseFailure")
        self.bash("git status", "PostToolUseFailure")
        self.assertIn("3 test runs", self.bash(cmd, "PostToolUseFailure"))

    def transcript(self, ctx: int) -> Path:
        t = self.root / "t.jsonl"
        usage = {"input_tokens": 10, "cache_read_input_tokens": ctx - 10, "cache_creation_input_tokens": 0}
        t.write_text(json.dumps({"type": "assistant", "message": {"id": "m1", "usage": usage}}) + "\n", encoding="utf-8")
        return t

    def test_main_thread_checkpoint_once_past_the_budget(self):
        t = self.transcript(200000)
        payload = {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": "ls"},
                   "transcript_path": str(t)}
        self.assertIn("fresh session", self.run_hook(payload))
        self.assertEqual(self.run_hook(payload), "")
        self.assertEqual(self.run_hook({**payload, "session_id": "other999zz", "agent_id": "ag1"}), "")

    def test_under_the_budget_is_silent(self):
        payload = {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_input": {"command": "ls"},
                   "transcript_path": str(self.transcript(90000))}
        self.assertEqual(self.run_hook(payload), "")

    def test_no_config_or_bad_input_is_silent(self):
        (self.root / "ai-kit.json").unlink()
        self.assertEqual(self.edit("src/a.py"), "")
        r = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True, timeout=30)
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
