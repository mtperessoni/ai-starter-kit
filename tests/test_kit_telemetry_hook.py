import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "kit" / "scripts" / "telemetry_hook.py"
FIXTURE = ROOT / "tests" / "fixtures" / "hook_events.jsonl"


def payloads():
    return [json.loads(line) for line in FIXTURE.read_text(encoding="utf8").splitlines() if line.strip()]


class HookCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.proj = Path(self._tmp.name)
        (self.proj / "ai-kit.json").write_text("{}", encoding="utf8")

    def run_hook(self, payload, env_extra=None, raw=None, cwd=None):
        if payload is not None:
            payload = dict(payload, cwd=str(cwd or self.proj))
        env = {k: v for k, v in os.environ.items() if k != "AI_KIT_CONTEXT"}
        env.update(env_extra or {})
        return subprocess.run(
            [sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(payload),
            capture_output=True, text=True, env=env, cwd=str(self.proj), timeout=30)

    def events(self, ctx):
        path = self.proj / ".ai-kit" / "runs" / ctx / "events.jsonl"
        return [json.loads(x) for x in path.read_text(encoding="utf8").splitlines()]

    def bash(self, command, ctx="t"):
        p = {"session_id": "s1", "hook_event_name": "PreToolUse", "tool_name": "Bash",
             "tool_input": {"command": command}, "tool_use_id": "tu"}
        self.run_hook(p, {"AI_KIT_CONTEXT": ctx})
        return self.events(ctx)[-1]


class FixtureTest(HookCase):
    def setUp(self):
        super().setUp()
        self.fx = payloads()
        for p in self.fx:
            r = self.run_hook(p, {"AI_KIT_CONTEXT": "fx"})
            self.assertEqual((r.returncode, r.stdout), (0, ""))
        self.ev = self.events("fx")

    def test_one_event_per_payload_with_increasing_seq(self):
        self.assertEqual(len(self.ev), len(self.fx))
        self.assertEqual([e["seq"] for e in self.ev], list(range(1, len(self.fx) + 1)))
        self.assertEqual([e["ev"] for e in self.ev], [p["hook_event_name"] for p in self.fx])

    def test_failure_has_ms_err_intr(self):
        e = self.ev[5]
        self.assertEqual((e["ms"], e["err"], e["intr"]), (131, True, False))
        self.assertNotIn("err", self.ev[3])

    def test_subagent_tool_calls_carry_agent_and_type(self):
        self.assertEqual((self.ev[8]["agent"], self.ev[8]["atype"]), ("ac6e651743a9ecab9", "general-purpose"))
        self.assertEqual(self.ev[2]["agent"], "main")

    def test_agent_result_has_sub(self):
        sub = self.ev[11]["sub"]
        self.assertEqual((sub["tokens"], sub["ms"], sub["tools"], sub["status"], sub["id"]),
                         (19750, 2465, 1, "completed", "ac6e651743a9ecab9"))

    def test_transcript_paths(self):
        self.assertEqual(self.ev[10]["tp"], self.fx[10]["agent_transcript_path"])
        self.assertEqual(self.ev[0]["tp"], self.fx[0]["transcript_path"])

    def test_classes_and_secrets_not_stored(self):
        self.assertEqual(self.ev[2]["cls"], "shell")
        self.assertEqual(self.ev[6]["cls"], "agent")
        self.assertEqual(self.ev[2]["cmd"], "echo hi")
        self.assertNotIn("stdout", json.dumps(self.ev))

    def test_meta_on_session_events(self):
        meta = json.loads((self.proj / ".ai-kit" / "runs" / "fx" / "meta.json").read_text(encoding="utf8"))
        self.assertEqual(meta["context"], "fx")
        self.assertEqual(meta["sessions"], [self.fx[0]["session_id"][:8]])
        self.assertLessEqual(meta["first_ts"], meta["last_ts"])


class ClassifyTest(HookCase):
    def test_classes(self):
        cases = {
            "echo hi": "shell",
            "scripts/gates.sh full": "test.full",
            "bash scripts/gates.sh related": "test.related",
            "scripts/gates.sh one tests/x_test.py": "test.related",
            "scripts/gates.sh offline": "test.full",
            "scripts/gates.sh integration": "test.full",
            "scripts/gates.sh build": "docker.build",
            "pytest tests/x_test.py": "test.single",
            "python -m pytest": "test.full",
            "docker run --rm x": "docker.run",
            "docker build .": "docker.build",
            "git status": "git",
            "pip install x": "install",
            "tail -f log": "background.unbounded",
            "echo git": "shell",
        }
        for cmd, cls in cases.items():
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd)["cls"], cls)

    def test_other_tools_use_lowercase_name_and_wait_human(self):
        for tool, cls in (("Read", "read"), ("AskUserQuestion", "wait.human")):
            self.run_hook({"session_id": "s", "hook_event_name": "PreToolUse", "tool_name": tool,
                           "tool_input": {"file_path": "a.py"}}, {"AI_KIT_CONTEXT": "t"})
            self.assertEqual(self.events("t")[-1]["cls"], cls)

    def test_edit_records_files(self):
        self.run_hook({"session_id": "s", "hook_event_name": "PostToolUse", "tool_name": "Edit",
                       "tool_input": {"file_path": "a.py", "old_string": "x"}}, {"AI_KIT_CONTEXT": "t"})
        self.assertEqual(self.events("t")[-1]["files"], ["a.py"])


class RedactTest(HookCase):
    def test_redaction(self):
        e = self.bash("API_TOKEN=abc curl -H 'Authorization: Bearer xyz123' x; echo ghp_abcDEF123 sk-live-9 AKIAABCDEFGHIJKL")
        for secret in ("abc ", "xyz123", "ghp_abcDEF123", "sk-live-9", "AKIAABCDEFGHIJKL"):
            self.assertNotIn(secret, e["cmd"])
        self.assertIn("API_TOKEN=***", e["cmd"])

    def test_cmd_capped_at_160(self):
        self.assertEqual(len(self.bash("echo " + "a" * 500)["cmd"]), 160)


class ContextTest(HookCase):
    def test_env(self):
        self.bash("echo", ctx="from-env")
        self.assertTrue((self.proj / ".ai-kit" / "runs" / "from-env" / "events.jsonl").exists())

    def test_current_file(self):
        runs = self.proj / ".ai-kit" / "runs"
        runs.mkdir(parents=True)
        (runs / "current").write_text("my-change\nignored\n", encoding="utf8")
        self.run_hook({"hook_event_name": "Stop", "session_id": "s"})
        self.assertEqual(len(self.events("my-change")), 1)

    def test_env_beats_current_file(self):
        runs = self.proj / ".ai-kit" / "runs"
        runs.mkdir(parents=True)
        (runs / "current").write_text("my-change\n", encoding="utf8")
        self.bash("echo", ctx="env-wins")
        self.assertEqual(len(self.events("env-wins")), 1)

    def test_branch_and_default(self):
        self.run_hook({"hook_event_name": "Stop", "session_id": "s"})
        self.assertEqual(len(self.events("default")), 1)
        git = lambda *a: subprocess.run(["git", *a], cwd=self.proj, capture_output=True, check=True)
        git("init", "-q")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "i")
        git("checkout", "-q", "-b", "feat/x-y")
        (self.proj / ".ai-kit" / "runs" / ".branch").unlink(missing_ok=True)
        self.run_hook({"hook_event_name": "Stop", "session_id": "s"})
        self.assertEqual(len(self.events("feat-x-y")), 1)

    def test_root_found_from_subfolder(self):
        sub = self.proj / "a" / "b"
        sub.mkdir(parents=True)
        self.run_hook({"hook_event_name": "Stop", "session_id": "s"}, {"AI_KIT_CONTEXT": "t"}, cwd=sub)
        self.assertEqual(len(self.events("t")), 1)


class RobustTest(HookCase):
    def test_garbage_input(self):
        for raw in ("not json", "", "[1,2]", "null"):
            r = self.run_hook(None, raw=raw)
            self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_cap_truncates_oldest_half(self):
        (self.proj / "ai-kit.json").write_text('{"telemetry": {"max_events_mb": 0.002}}', encoding="utf8")
        for _ in range(30):
            self.bash("echo " + "a" * 100, ctx="cap")
        ev = self.events("cap")
        self.assertTrue(any(e["ev"] == "truncated" for e in ev))
        self.assertLess(len(ev), 30)
        seqs = [e["seq"] for e in ev if "seq" in e]
        self.assertEqual(seqs, sorted(seqs))

    def test_under_300ms(self):
        p = {"session_id": "s", "hook_event_name": "PreToolUse", "tool_name": "Bash",
             "tool_input": {"command": "echo"}, "cwd": str(self.proj)}
        env = dict(os.environ, AI_KIT_CONTEXT="speed")
        run = lambda: subprocess.run([sys.executable, str(HOOK)], input=json.dumps(p), text=True,
                                     capture_output=True, env=env)
        run()
        t = time.perf_counter()
        run()
        self.assertLess(time.perf_counter() - t, 0.3)


class FoundInTheRealEvaluation(HookCase):
    """Defects the 2026-10-05 telemetry evaluation exposed in a real session with subagents."""

    def test_concurrent_async_hooks_never_interleave_or_repeat_a_seq(self):
        env = {k: v for k, v in os.environ.items() if k != "AI_KIT_CONTEXT"}
        env["AI_KIT_CONTEXT"] = "c"
        procs = []
        for i in range(24):
            p = {"session_id": "s1", "hook_event_name": "PostToolUse", "tool_name": "Bash", "cwd": str(self.proj),
                 "tool_input": {"command": f"echo {i}", "description": "x" * 400}, "tool_use_id": f"t{i}",
                 "tool_response": {"stdout": "y" * 2000, "stderr": ""}, "duration_ms": 5}
            procs.append(subprocess.Popen([sys.executable, str(HOOK)], stdin=subprocess.PIPE, env=env,
                                          cwd=str(self.proj), text=True))
            procs[-1].stdin.write(json.dumps(p))
            procs[-1].stdin.close()
        for proc in procs:
            proc.wait(timeout=30)
        events = self.events("c")
        self.assertEqual(len(events), 24)
        self.assertEqual(sorted(e["seq"] for e in events), list(range(1, 25)))

    def test_the_hash_ignores_the_description_so_repeats_match(self):
        a = self.bash_with("python -c 'import sys; sys.exit(1)'", "first try")
        b = self.bash_with("python -c 'import sys; sys.exit(1)'", "again")
        self.assertEqual(a["h"], b["h"])

    def test_wrapper_prefixes_do_not_hide_the_class(self):
        self.assertEqual(self.bash("rtk docker build --help")["cls"], "docker.build")
        self.assertEqual(self.bash("rtk proxy git status")["cls"], "git")
        self.assertEqual(self.bash("timeout 30 pytest -q")["cls"], "test.full")
        self.assertEqual(self.bash("env CI=1 rtk proxy bash scripts/gates.sh full")["cls"], "test.full")

    def bash_with(self, command, description):
        p = {"session_id": "s1", "hook_event_name": "PreToolUse", "tool_name": "Bash",
             "tool_input": {"command": command, "description": description}, "tool_use_id": "tu"}
        self.run_hook(p, {"AI_KIT_CONTEXT": "h"})
        return self.events("h")[-1]


if __name__ == "__main__":
    unittest.main()
