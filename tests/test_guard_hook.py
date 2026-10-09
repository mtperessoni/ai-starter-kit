import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "kit" / "scripts" / "guard_hook.py"
AGENTS = sorted((ROOT / "kit" / ".claude" / "agents").glob("prd-flow-*.md"))


def run(command, tool="Bash", raw=None, agent="a1b2c3"):
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {"command": command}}
    if agent:
        payload["agent_id"] = agent
    return subprocess.run([sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(payload),
                          capture_output=True, text=True, timeout=30)


DENIED = {
    "heredoc": ["cat <<'EOF'\nx\nEOF", "python - <<'E' 2>/dev/null || /c/Python314/python - <<'E2'\nprint(1)\nE2",
                "cat >> tests/a.py <<'EOF'\nx\nEOF", "cat <<< hello"],
    "here-string": ["$x = @'\nabc\n'@", '$x = @"\nabc\n"@'],
    "stdin interpreter": ["python -", "python3 - arg", "py - ", "/c/Python314/python -", "echo 1 | python", "echo 1 | python3 | cat"],
    "redirect write": ["cat > a.py", "cat >> a.py", "echo x | tee a.py", "tee -a log.txt"],
    "kill by name": ["taskkill /IM python.exe /F", "taskkill.exe /PID 4 /T", "Stop-Process -Name python -Force", "pkill -f python", "killall node"],
    "git destructive": ["git checkout main", "git checkout -- a.ts", "git switch other", "git stash", "git -C wt stash pop", "git reset --hard HEAD~1",
                        "git restore a.ts", "git commit --amend --no-edit", "git add a && git stash"],
    "in-place edit": ["sed -i 's/a/b/' f.py", "sed -ni 's/a/b/p' f.py"],
}
DENIED_MORE = ["bash -c 'git stash'", 'sh -c "cat > a.py"', "echo it's; git stash", "git commit -F -", "git commit --file=-", "python3 -u -",
               'python -c "exec(sys.stdin.read())"', "Get-Process python | Stop-Process -Id 4", "Get-Process python | Stop-Process",
               "Set-Content a.py 'x'", "Add-Content a.py x", "Out-File a.py", "echo x > file.py", "echo x >> notes.md", "x = @'\nabc\n'@",
               "pwsh -Command 'taskkill /IM python.exe'", "cat <<EOF\nx\nEOF", "cat <<-EOF\nx\nEOF"]
ALLOWED_MORE = ['echo "user@"', 'grep -rn "<<" src', 'python -c "print(1<<3)"', 'git commit -m "fix <<x"', "python tee.py", "ls tee-dir",
                "echo x > /dev/null", "cmd 2>&1", "echo x > out.log", "echo x > scratch/a.txt", "echo x > r.out", "a=1; echo $a",
                "python -m pytest -q", "git commit -F msg.txt", "echo it's fine", "git log --format=%H -3"]
ALLOWED = ["git log --oneline -5", "git diff --stat", "git status", "git commit -F .claude/msg.txt", "git add a.py", "git show HEAD",
           "python -m unittest tests.test_a", "python3 -m pytest -q", "python -c \"print(1)\"", "python scripts/verify.py s1",
           "scripts/gates.sh verify s1", "scripts/gates.sh reap --dry-run", "scripts/gates.sh move a.py 1-5 b.py", "scripts/gates.sh python",
           "cat a.py", "cat a.py | head -5", "cat a.txt 2>&1", "sed -n '1,5p' f.py", "grep -rn foo src", "ls -la", "taskkill_notes.md",
           "git commit -m \"do not git reset here\"", "echo hi | python -m json.tool", "py -3 script.py", "node script.js"]


class DenyTest(unittest.TestCase):
    def test_every_denied_pattern_exits_2_with_a_message(self):
        for kind, commands in DENIED.items():
            for cmd in commands:
                with self.subTest(kind=kind, cmd=cmd):
                    r = run(cmd, tool="PowerShell" if kind == "here-string" else "Bash")
                    self.assertEqual(r.returncode, 2, r.stderr)
                    self.assertTrue(r.stderr.strip())

    def test_wrapped_unquoted_and_uncovered_shapes_are_denied(self):
        for cmd in DENIED_MORE:
            with self.subTest(cmd=cmd):
                r = run(cmd, tool="PowerShell" if cmd.startswith(("Get-", "Set-", "Add-", "Out-", "x =", "pwsh")) else "Bash")
                self.assertEqual(r.returncode, 2, cmd)

    def test_each_message_names_the_allowed_way(self):
        allowed_way = {"heredoc": "Write", "here-string": "Write", "stdin interpreter": "python -m", "redirect write": "Write",
                       "kill by name": "gates.sh reap", "git destructive": "git", "in-place edit": "Edit"}
        for kind, needle in allowed_way.items():
            with self.subTest(kind=kind):
                self.assertIn(needle, run(DENIED[kind][0]).stderr)
        self.assertIn("gates.sh move", run("cat > a.py").stderr)
        self.assertIn("-F", run("git commit --amend").stderr)


class WrapperBodyTest(unittest.TestCase):
    def test_heredoc_and_stdin_interpreter_inside_a_wrapper_are_denied(self):
        for cmd in ["bash -c 'cat <<EOF\nx\nEOF'", "bash -c 'python - <<E\nprint(1)\nE'", "sh -c \"python -\"", 'cmd /c "echo > a.py"',
                    "cmd /c \"echo x > b.md\""]:
            with self.subTest(cmd=cmd):
                self.assertEqual(run(cmd).returncode, 2, cmd)

    def test_quoted_wrapper_bodies_that_only_mention_the_shapes_pass(self):
        for cmd in ["bash -c 'python -c \"print(1<<3)\"'", "bash -c 'echo hi > out.log'", 'cmd /c "echo hi"']:
            with self.subTest(cmd=cmd):
                self.assertEqual(run(cmd).returncode, 0, cmd)


class AllowTest(unittest.TestCase):
    def test_allowed_commands_pass_silently(self):
        for cmd in ALLOWED:
            with self.subTest(cmd=cmd):
                r = run(cmd)
                self.assertEqual((r.returncode, r.stderr), (0, ""), cmd)

    def test_false_positives_pass(self):
        for cmd in ALLOWED_MORE:
            with self.subTest(cmd=cmd):
                r = run(cmd, tool="PowerShell" if cmd.startswith("echo \"user") else "Bash")
                self.assertEqual((r.returncode, r.stderr), (0, ""), cmd)

    def test_other_tools_are_ignored(self):
        self.assertEqual(run("git stash", tool="Read").returncode, 0)

    def test_the_main_thread_without_an_agent_id_is_never_blocked(self):
        for cmd in ["git stash", "cat <<'EOF'\nx\nEOF", "taskkill /IM python.exe /F"]:
            with self.subTest(cmd=cmd):
                r = run(cmd, agent=None)
                self.assertEqual((r.returncode, r.stderr), (0, ""))

    def test_bad_input_fails_open(self):
        for raw in ["", "not json", "[]", json.dumps({"tool_name": "Bash"}), json.dumps({"tool_name": "Bash", "tool_input": "x"})]:
            with self.subTest(raw=raw):
                self.assertEqual(run("", raw=raw).returncode, 0)


class FrontmatterTest(unittest.TestCase):
    """The guard runs for every subagent from settings.json, so the agent files carry no hooks block (L12)."""

    def guard_command(self):
        hooks = json.loads((ROOT / "kit" / ".claude" / "settings.json").read_text(encoding="utf-8"))["hooks"]
        entries = [e for e in hooks["PreToolUse"] if e.get("matcher") == "Bash|PowerShell"]
        self.assertEqual(len(entries), 1)
        return entries[0]["hooks"][0]["command"]

    def test_five_agents_carry_no_hooks_block(self):
        self.assertEqual(len(AGENTS), 5)
        for path in AGENTS:
            front = path.read_text(encoding="utf-8").split("---", 2)[1]
            with self.subTest(agent=path.name):
                self.assertIsNone(re.search(r"^hooks:", front, re.M))
                self.assertNotIn("guard_hook.py", front)
                self.assertNotIn("—", path.read_text(encoding="utf-8"))

    def test_settings_carries_the_guard_and_passes_exit_2(self):
        command = self.guard_command()
        self.assertIn("scripts/guard_hook.py", command)
        self.assertRegex(command, r"\[ \$\? -eq 2 \] && exit 2")
        self.assertRegex(command, r'\[ -f "\$f" \] \|\| exit 0')

    def test_the_launcher_blocks_allows_and_fails_open(self):
        import shutil
        import tempfile

        bash = shutil.which("bash")
        if not bash:
            self.skipTest("no bash")
        script = self.guard_command().replace("__AIKIT_PYTHON__", Path(sys.executable).as_posix())
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp)
            (proj / "ai-kit.json").write_text("{}", encoding="utf-8")

            def go(command):
                payload = json.dumps({"tool_name": "Bash", "agent_id": "a1", "tool_input": {"command": command}})
                return subprocess.run([bash, "-c", script], input=payload, capture_output=True, text=True, timeout=60,
                                      env={**__import__("os").environ, "CLAUDE_PROJECT_DIR": str(proj)})

            self.assertEqual(go("git stash").returncode, 0)
            (proj / "scripts").mkdir()
            shutil.copy(HOOK, proj / "scripts" / "guard_hook.py")
            self.assertEqual(go("git stash").returncode, 2)
            self.assertEqual(go("git log").returncode, 0)


class SettingsTest(unittest.TestCase):
    def setUp(self):
        text = (ROOT / "kit" / ".claude" / "settings.json").read_text(encoding="utf-8")
        self.text = text
        self.hooks = json.loads(text)["hooks"]

    def test_an_unfilled_placeholder_still_finds_an_interpreter_and_blocks(self):
        import shutil
        import tempfile

        bash = shutil.which("bash")
        if not bash or not (shutil.which("python3") or shutil.which("python")):
            self.skipTest("no bash or python")
        script = next(e for e in self.hooks["PreToolUse"] if e.get("matcher") == "Bash|PowerShell")["hooks"][0]["command"]
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp)
            (proj / "ai-kit.json").write_text("{}", encoding="utf-8")
            (proj / "scripts").mkdir()
            shutil.copy(HOOK, proj / "scripts" / "guard_hook.py")
            fake_bin = proj / "bin"
            fake_bin.mkdir()
            shim = fake_bin / "python3"
            shim.write_text(f'#!/bin/sh\nexec "{Path(sys.executable).as_posix()}" "$@"\n', encoding="utf-8")
            shim.chmod(0o755)
            os_env = __import__("os").environ
            payload = json.dumps({"tool_name": "Bash", "agent_id": "a1", "tool_input": {"command": "git stash"}})
            run = subprocess.run([bash, "-c", script], input=payload, capture_output=True, text=True, timeout=60,
                                 env={**os_env, "CLAUDE_PROJECT_DIR": str(proj), "PATH": fake_bin.as_posix() + ":" + os_env["PATH"]})
            self.assertEqual(run.returncode, 2)

    def test_a_synchronous_guard_runs_for_bash_and_powershell_on_every_agent(self):
        entries = [e for e in self.hooks["PreToolUse"] if e.get("matcher") == "Bash|PowerShell"]
        self.assertEqual(len(entries), 1)
        hook = entries[0]["hooks"][0]
        self.assertIn("guard_hook.py", hook["command"])
        self.assertNotIn("async", hook)
        self.assertRegex(hook["command"], r"\[ \$\? -eq 2 \] && exit 2")

    def test_session_end_runs_the_cleanup(self):
        commands = [h["command"] for e in self.hooks["SessionEnd"] for h in e["hooks"]]
        self.assertTrue(any("gates.sh cleanup --session-end" in c for c in commands))

    def test_hooks_pick_python_then_python3_without_a_probe_when_the_placeholder_is_unfilled(self):
        self.assertNotIn("-c pass", self.text)
        self.assertNotIn("py=python ;;", self.text)
        for event, entries in self.hooks.items():
            for entry in entries:
                for hook in entry["hooks"]:
                    if "telemetry_hook.py" in hook["command"] or "guard_hook.py" in hook["command"]:
                        with self.subTest(event=event):
                            command = hook["command"]
                            self.assertIn("__AIKIT_PYTHON__", command)
                            self.assertIn('for p in python python3; do command -v "$p" >/dev/null 2>&1 && { py=$p; break; }; done', command)
                            self.assertIn('[ -n "$py" ] || exit 0', command)

    def test_telemetry_events_are_unchanged(self):
        self.assertEqual(sorted(self.hooks), sorted(["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PostToolUseFailure",
                                                     "SubagentStart", "SubagentStop", "Notification", "PreCompact", "PostCompact", "Stop",
                                                     "SessionEnd"]))


if __name__ == "__main__":
    unittest.main()
