import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "kit" / "scripts" / "agent_guard_hook.py"
SETTINGS = ROOT / "kit" / ".claude" / "settings.json"


def run(command, agent_type="prd-flow-executor", agent_id="a1", cwd=None, tool="Bash"):
    p = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {"command": command},
         "cwd": cwd or str(ROOT)}
    if agent_type:
        p["agent_type"] = agent_type
    if agent_id:
        p["agent_id"] = agent_id
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(p),
                          capture_output=True, text=True, timeout=30)


class BlockTest(unittest.TestCase):
    def test_blocked_commands(self):
        for cmd in ["git stash", "git stash pop", "git -C wt stash push -m x", "git reset --hard HEAD~1",
                    "git reset HEAD file", "git checkout main", "git checkout -- src/a.ts",
                    "git switch other", "git restore src/a.ts", "git commit --amend --no-edit",
                    "git add a && git stash", "scripts/gates.sh fix", "bash scripts/gates.sh fix"]:
            with self.subTest(cmd=cmd):
                r = run(cmd)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertTrue(r.stderr.strip())

    def test_allowed_commands(self):
        for cmd in ["git status", "git diff", "git commit -m 'x'", "git add src/a.ts",
                    "scripts/gates.sh fix src/a.ts", "scripts/gates.sh related src/a.ts",
                    "git commit -m 'never git stash or git reset'",
                    "git commit -F - <<'EOF'\nnote about git stash\nEOF"]:
            with self.subTest(cmd=cmd):
                r = run(cmd)
                self.assertEqual(r.returncode, 0, r.stderr)

    def test_main_thread_and_other_agents_untouched(self):
        self.assertEqual(run("git stash", agent_type=None, agent_id=None).returncode, 0)
        self.assertEqual(run("git stash", agent_type="Explore").returncode, 0)

    def test_unidentified_subagent_only_in_linked_worktree(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run("git stash", agent_type=None, cwd=d).returncode, 0)
            (Path(d) / ".git").write_text("gitdir: /x/.git/worktrees/w", encoding="utf8")
            self.assertEqual(run("git stash", agent_type=None, cwd=d).returncode, 2)

    def test_non_bash_tool_ignored(self):
        self.assertEqual(run("git stash", tool="Edit").returncode, 0)

    def test_bad_input_allows(self):
        r = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)


class WarnTest(unittest.TestCase):
    def warned(self, cmd):
        r = run(cmd)
        self.assertEqual(r.returncode, 0, r.stderr)
        if not r.stdout.strip():
            return False
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertIn("Edit", out["additionalContext"])
        return True

    def test_warn_patterns(self):
        for cmd in ["sed -i 's/a/b/' src/a.ts", "perl -pi -e 's/a/b/' x.py", "python - <<'PY'\nprint(1)\nPY",
                    "python3 <<EOF\nprint(1)\nEOF", "python -", "cat > src/a.ts <<'X'\ncode\nX"]:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.warned(cmd))

    def test_no_warn(self):
        for cmd in ["python scripts/ratchet.py", "sed -n 1,5p a.ts", "cat > notes.txt <<'X'\nhi\nX", "ls"]:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.warned(cmd))


class SettingsTest(unittest.TestCase):
    def test_registered_next_to_telemetry(self):
        hooks = json.loads(SETTINGS.read_text(encoding="utf8"))["hooks"]["PreToolUse"]
        cmds = [h["command"] for e in hooks for h in e["hooks"]]
        self.assertIn("python scripts/telemetry_hook.py", cmds)
        self.assertIn("python scripts/agent_guard_hook.py", cmds)
        guard = [e for e in hooks if any("agent_guard" in h["command"] for h in e["hooks"])][0]
        self.assertEqual(guard["matcher"], "Bash")
        self.assertFalse(any(h.get("async") for h in guard["hooks"]))


if __name__ == "__main__":
    unittest.main()
