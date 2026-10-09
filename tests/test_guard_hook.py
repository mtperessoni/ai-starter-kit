import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "kit" / "scripts" / "guard_hook.py"
AGENTS = sorted((ROOT / "kit" / ".claude" / "agents").glob("prd-flow-*.md"))


def run(command, tool="Bash", raw=None):
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {"command": command}}
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

    def test_bad_input_fails_open(self):
        for raw in ["", "not json", "[]", json.dumps({"tool_name": "Bash"}), json.dumps({"tool_name": "Bash", "tool_input": "x"})]:
            with self.subTest(raw=raw):
                self.assertEqual(run("", raw=raw).returncode, 0)


class FrontmatterTest(unittest.TestCase):
    def test_five_agents_declare_the_hook(self):
        self.assertEqual(len(AGENTS), 5)
        for path in AGENTS:
            text = path.read_text(encoding="utf-8")
            front = text.split("---", 2)[1]
            with self.subTest(agent=path.name):
                self.assertIn("hooks:", front)
                self.assertIn("PreToolUse:", front)
                self.assertIn('matcher: "Bash|PowerShell"', front)
                self.assertIn("scripts/guard_hook.py", front)
                self.assertNotIn("—", front)

    def test_the_launcher_fails_open_without_python_and_passes_exit_2(self):
        front = AGENTS[0].read_text(encoding="utf-8").split("---", 2)[1]
        self.assertIn("ai-kit.json", front)
        self.assertRegex(front, r"\[ \$\? -eq 2 \] && exit 2")
        self.assertRegex(front, r'\[ -n "\$py" \] \|\| exit 0')
        self.assertIsNone(re.search(r"^\s*async:\s*true", front, re.M))
        self.assertIn(r"s/\\\\/\\/g", front)

    def test_the_five_hook_blocks_are_identical(self):
        blocks = {p.read_text(encoding="utf-8").split("hooks:", 1)[1].split("\n---", 1)[0] for p in AGENTS}
        self.assertEqual(len(blocks), 1)

    def test_the_launcher_blocks_allows_and_fails_open(self):
        import shutil
        import tempfile
        import textwrap

        bash = shutil.which("bash")
        if not bash:
            self.skipTest("no bash")
        front = AGENTS[0].read_text(encoding="utf-8").split("---", 2)[1]
        script = textwrap.dedent(front.split("command: |\n", 1)[1])
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp)
            (proj / "ai-kit.json").write_text("{}", encoding="utf-8")

            def go(command):
                payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
                return subprocess.run([bash, "-c", script], input=payload, capture_output=True, text=True, timeout=60,
                                      env={**__import__("os").environ, "CLAUDE_PROJECT_DIR": str(proj)})

            self.assertEqual(go("git stash").returncode, 0)
            (proj / "scripts").mkdir()
            shutil.copy(HOOK, proj / "scripts" / "guard_hook.py")
            self.assertEqual(go("git stash").returncode, 2)
            self.assertEqual(go("git log").returncode, 0)


if __name__ == "__main__":
    unittest.main()
