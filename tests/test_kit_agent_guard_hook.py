import json
import os
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

    def test_unidentified_subagent_never_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".git").write_text("gitdir: /x/.git/worktrees/w", encoding="utf8")
            self.assertEqual(run("git stash", agent_type=None, cwd=d).returncode, 0)
            self.assertEqual(run("git checkout main", agent_type=None, cwd=d).returncode, 0)

    def test_nested_shells_and_absolute_git_are_blocked(self):
        for cmd in ['bash -c "git stash"', "sh -c 'git reset --hard'", 'eval "git checkout main"',
                    "echo $(git stash)", "/usr/bin/git reset --hard", "x=1 /usr/bin/git restore a.ts"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(run(cmd).returncode, 2)
        self.assertEqual(run('echo "git stash"').returncode, 0)
        self.assertEqual(run("git commit -m 'git stash'").returncode, 0)

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


def find_bash():
    for c in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files (x86)\Git\bin\bash.exe", "/bin/bash", "/usr/bin/bash"):
        if Path(c).exists():
            return c
    return None


def registered(script, event="PreToolUse"):
    hooks = json.loads(SETTINGS.read_text(encoding="utf8"))["hooks"][event]
    return [h for e in hooks for h in e["hooks"] if script in h["command"]]


class SettingsTest(unittest.TestCase):
    def test_registered_next_to_telemetry(self):
        self.assertTrue(registered("telemetry_hook.py"))
        guard = registered("agent_guard_hook.py")
        self.assertEqual(len(guard), 1)
        self.assertFalse(guard[0].get("async"))
        hooks = json.loads(SETTINGS.read_text(encoding="utf8"))["hooks"]["PreToolUse"]
        entry = [e for e in hooks if any("agent_guard" in h["command"] for h in e["hooks"])][0]
        self.assertEqual(entry["matcher"], "Bash")

    def test_every_hook_uses_the_project_dir_not_a_relative_path(self):
        for event, entries in json.loads(SETTINGS.read_text(encoding="utf8"))["hooks"].items():
            for e in entries:
                for h in e["hooks"]:
                    with self.subTest(event=event):
                        self.assertIn("CLAUDE_PROJECT_DIR", h["command"])
                        self.assertNotIn("python scripts/", h["command"])


@unittest.skipUnless(find_bash(), "needs a POSIX shell, as Claude Code uses")
class RegisteredCommandTest(unittest.TestCase):
    """The hook command exactly as registered, run from a cwd that is not the repo root."""

    def run_cmd(self, project_dir, cwd, env_extra=None, stdin=None):
        cmd = registered("agent_guard_hook.py")[0]["command"]
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project_dir))
        env.update(env_extra or {})
        return subprocess.run([find_bash(), "-c", cmd], input=stdin or "", capture_output=True, text=True,
                              cwd=str(cwd), env=env, timeout=60)

    def payload(self, command="git stash"):
        return json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command},
                           "agent_type": "prd-flow-executor", "agent_id": "a"})

    def test_works_from_another_cwd(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cmd(ROOT / "kit", d, stdin=self.payload())
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("Blocked", r.stderr)
            self.assertEqual(self.run_cmd(ROOT / "kit", d, stdin=self.payload("git status")).returncode, 0)

    def test_missing_script_never_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cmd(d, d, stdin=self.payload())
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_missing_interpreter_never_blocks(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as empty:
            r = self.run_cmd(ROOT / "kit", d, {"PATH": empty}, stdin=self.payload())
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_telemetry_command_also_survives_a_missing_script(self):
        cmd = registered("telemetry_hook.py", "PostToolUse")[0]["command"]
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([find_bash(), "-c", cmd], input="{}", capture_output=True, text=True, cwd=d,
                               env=dict(os.environ, CLAUDE_PROJECT_DIR=d), timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
