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
        # Busy CPUs widen the window in which Windows reports a lock being deleted as PermissionError.
        burners = [subprocess.Popen([sys.executable, "-c", "import time\nt=time.time()\nwhile time.time()-t<4: pass"])
                   for _ in range(max(2, (os.cpu_count() or 2)))]
        self.addCleanup(lambda: [b.kill() for b in burners])
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


class RunSpeedTelemetryTest(HookCase):
    """W5.3: repo routing, agent fields, Bash timeout and bg, waits, durations and chains."""

    def other_repo(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name)
        (repo / "ai-kit.json").write_text("{}", encoding="utf8")
        return repo

    def send(self, ev, tool=None, ti=None, ctx="t", read=True, **kw):
        p = {"session_id": "s1", "hook_event_name": ev, **kw}
        if tool:
            p.update(tool_name=tool, tool_input=ti or {}, tool_use_id=kw.get("tool_use_id", "tu"))
        self.run_hook(p, {"AI_KIT_CONTEXT": ctx})
        return self.events(ctx) if read else None

    def test_bash_cd_target_routes_the_event_to_that_repo(self):
        other = self.other_repo()
        self.send("PreToolUse", "Bash", {"command": f'cd "{other.as_posix()}" && git status'}, read=False)
        path = other / ".ai-kit" / "runs" / "t" / "events.jsonl"
        e = json.loads(path.read_text(encoding="utf8").splitlines()[-1])
        self.assertEqual(Path(e["repo"]).resolve(), other.resolve())
        self.assertFalse((self.proj / ".ai-kit" / "runs" / "t" / "events.jsonl").exists())

    def test_git_dash_c_and_file_paths_route_too(self):
        other = self.other_repo()
        self.send("PreToolUse", "Bash", {"command": f"git -C {other.as_posix()} log"}, read=False)
        self.send("PostToolUse", "Edit", {"file_path": str(other / "src" / "a.py")}, tool_use_id="t2", read=False)
        lines = (other / ".ai-kit" / "runs" / "t" / "events.jsonl").read_text(encoding="utf8").splitlines()
        self.assertEqual(len(lines), 2)

    @unittest.skipUnless(os.name == "nt", "MSYS drive paths exist on Windows only")
    def test_git_bash_drive_paths_route(self):
        other = self.other_repo().resolve()
        msys = "/" + other.drive[0].lower() + other.as_posix()[2:]
        self.send("PreToolUse", "Bash", {"command": f"cd {msys} && git status"}, read=False)
        e = json.loads((other / ".ai-kit" / "runs" / "t" / "events.jsonl").read_text(encoding="utf8").splitlines()[-1])
        self.assertEqual(Path(e["repo"]).resolve(), other)

    def test_an_absolute_path_in_a_command_without_cd_routes(self):
        other = self.other_repo().resolve()
        self.send("PreToolUse", "Bash", {"command": f"{other.as_posix()}/.venv/bin/python -m pytest {other.as_posix()}/tests/a.py"}, read=False)
        lines = (other / ".ai-kit" / "runs" / "t" / "events.jsonl").read_text(encoding="utf8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertFalse((self.proj / ".ai-kit" / "runs" / "t" / "events.jsonl").exists())

    @unittest.skipUnless(os.name == "nt", "drive paths exist on Windows only")
    def test_backslash_and_git_bash_drive_paths_in_a_command_route(self):
        other = self.other_repo().resolve()
        msys = "/" + other.drive[0].lower() + other.as_posix()[2:]
        self.send("PreToolUse", "Bash", {"command": f"type {other}{os.sep}README.md"}, read=False)
        self.send("PreToolUse", "Bash", {"command": f"cat {msys}/README.md"}, tool_use_id="t2", read=False)
        lines = (other / ".ai-kit" / "runs" / "t" / "events.jsonl").read_text(encoding="utf8").splitlines()
        self.assertEqual(len(lines), 2)

    def test_dash_c_of_other_tools_does_not_route(self):
        other = self.other_repo()
        for cmd in ("grep -C 3 foo src", "grep -rn -C 3 x"):
            self.send("PreToolUse", "Bash", {"command": cmd}, read=False)
        self.assertFalse((other / ".ai-kit").exists())
        self.assertEqual(len(self.events("t")), 2)

    def test_no_target_falls_back_to_the_session_root(self):
        self.send("PreToolUse", "Bash", {"command": "echo hi"})
        e = self.events("t")[-1]
        self.assertEqual(Path(e["repo"]).resolve(), self.proj.resolve())

    def test_agent_event_fields(self):
        prompt = "Task K3, item W5.3.\nmode: close\nslug: run-speed\ntask: K3"
        self.send("PreToolUse", "Agent", {"prompt": prompt, "model": "sonnet", "run_in_background": True,
                                          "subagent_type": "prd-flow-executor"})
        e = self.events("t")[-1]
        self.assertEqual((e["mode"], e["task"], e["slug"], e["model"], e["bg"]), ("close", "K3", "run-speed", "sonnet", True))

    def test_bash_bg_timeout_and_auto_bg(self):
        e = self.send("PostToolUse", "Bash", {"command": "make", "timeout": 600000}, duration_ms=300000)[-1]
        self.assertEqual((e["bg"], e["timeout"], e.get("auto_bg", False)), (False, 600000, False))
        e = self.send("PostToolUse", "Bash", {"command": "make"}, duration_ms=130000, tool_use_id="b")[-1]
        self.assertNotIn("timeout", e)
        self.assertTrue(e["auto_bg"])
        e = self.send("PostToolUse", "Bash", {"command": "make"}, duration_ms=5000, tool_use_id="c")[-1]
        self.assertFalse(e.get("auto_bg", False))
        e = self.send("PreToolUse", "Bash", {"command": "make", "run_in_background": True}, tool_use_id="d")[-1]
        self.assertTrue(e["bg"])

    def test_askuserquestion_wait_ms_comes_from_the_pre_event(self):
        pre = self.send("PreToolUse", "AskUserQuestion", {"questions": []}, tool_use_id="q1")[-1]
        time.sleep(0.3)
        post = self.send("PostToolUse", "AskUserQuestion", {"questions": []}, tool_use_id="q1", duration_ms=1)[-1]
        self.assertGreaterEqual(post["wait_ms"], 250)
        self.assertNotIn("wait_ms", pre)

    def test_wait_test_class_for_polling_and_baseline(self):
        for cmd in ("until grep -q done out.txt; do sleep 5; done", "for i in 1 2 3; do ls; sleep 2; done",
                    "scripts/gates.sh baseline my-slug"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd)["cls"], "wait.test")
        self.assertEqual(self.bash("sleep infinity")["cls"], "background.unbounded")

    def test_a_single_sleep_or_seq_is_not_polling_and_bg_baseline_is_no_wait(self):
        for cmd in ("sleep 2 && curl x", "seq 1 5", "scripts/gates.sh baseline my-slug --bg"):
            with self.subTest(cmd=cmd):
                self.assertNotEqual(self.bash(cmd)["cls"], "wait.test")

    def test_subagent_stop_carries_dur_ms_and_bg(self):
        self.send("SubagentStart", agent_id="ag1", agent_type="x")
        time.sleep(0.3)
        e = self.send("SubagentStop", agent_id="ag1", agent_type="x", background_tasks=[{"id": "b"}])[-1]
        self.assertGreaterEqual(e["dur_ms"], 250)
        self.assertEqual(e["bg"], 1)

    def test_edit_plus_test_is_a_chain(self):
        self.assertEqual(self.bash("sed -i 's/a/b/' src/x.py && pytest tests/test_x.py")["cls"], "chain")
        self.assertEqual(self.bash("cat > t.py <<EOF\nx\nEOF\npython -m unittest tests.t")["cls"], "chain")
        self.assertEqual(self.bash("pytest tests/test_x.py > out.txt")["cls"], "test.single")


if __name__ == "__main__":
    unittest.main()


class LauncherTest(unittest.TestCase):
    def launcher(self):
        settings = json.loads((ROOT / "kit" / ".claude" / "settings.json").read_text(encoding="utf8"))
        commands = {h["command"] for entries in settings["hooks"].values() for e in entries for h in e["hooks"]}
        self.assertEqual(len(commands), 1)
        self.assertNotIn("agent_guard_hook", next(iter(commands)))
        return next(iter(commands))

    def run_launcher(self, proj, extra_path=None):
        import shutil
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("bash not available")
        env = dict(os.environ, CLAUDE_PROJECT_DIR=proj.as_posix())
        return subprocess.run([bash, "-c", self.launcher()], capture_output=True, text=True, env=env, timeout=30)

    def test_commands_python_from_ai_kit_json_runs_the_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp)
            (proj / "scripts").mkdir()
            (proj / "scripts" / "telemetry_hook.py").write_text("", encoding="utf8")
            fake = proj / "fakepy"
            fake.write_text("#!/bin/sh\necho ran > " + (proj / "marker").as_posix() + "\n", encoding="utf8")
            fake.chmod(0o755)
            (proj / "ai-kit.json").write_text(json.dumps({"commands": {"python": fake.as_posix()}}), encoding="utf8")
            r = self.run_launcher(proj)
            self.assertEqual(r.returncode, 0)
            self.assertTrue((proj / "marker").is_file())

    def test_a_missing_hook_script_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self.run_launcher(Path(tmp))
            self.assertEqual((r.returncode, r.stdout), (0, ""))
