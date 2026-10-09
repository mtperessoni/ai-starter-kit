import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "kit" / "scripts"))

import watch  # noqa: E402

T0 = 1_000_000.0


class Clock:
    def __init__(self, hook=None):
        self.t = T0
        self.hook = hook
        self.sleeps = 0

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.sleeps += 1
        self.t += seconds
        if self.hook:
            self.hook(self)


class WatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.folder = self.root / ".ai-kit" / "runs" / "ctx"
        self.folder.mkdir(parents=True)
        (self.root / ".ai-kit" / "runs" / "current").write_text("ctx\n", encoding="utf-8")
        self.events = self.folder / "events.jsonl"
        self.events.write_text("", encoding="utf-8")

    def add(self, ev, agent, ts, atype=None):
        row = {"ts": ts, "ev": ev, "agent": agent, "sid": "s"}
        if atype:
            row["atype"] = atype
        with self.events.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def run_watch(self, argv=("s1",), hook=None):
        clock = Clock(hook)
        out = io.StringIO()
        with redirect_stdout(out):
            code = watch.main(list(argv), root=self.root, now=clock.now, sleep=clock.sleep)
        return code, out.getvalue().strip().splitlines(), clock

    def test_done_once_every_tracked_agent_stopped(self):
        self.add("SubagentStart", "a1", T0 + 1, "prd-flow-executor")
        self.add("SubagentStop", "a1", T0 + 30)
        code, lines, _ = self.run_watch()
        self.assertEqual(lines, ["done: no agent running"])
        self.assertEqual(code, 0)

    def test_an_agent_that_stops_while_watching_ends_the_watch(self):
        self.add("SubagentStart", "a1", T0 + 1, "prd-flow-executor")

        def stop(clock):
            if clock.sleeps == 3:
                self.add("SubagentStop", "a1", clock.t)

        code, lines, clock = self.run_watch(hook=stop)
        self.assertEqual(lines, ["done: no agent running"])
        self.assertEqual(clock.sleeps, 3)

    def test_an_agent_started_long_before_the_watch_is_tracked_and_since_excludes_older_ones(self):
        self.add("SubagentStart", "old", T0 - 5000, "prd-flow-executor")
        self.add("SubagentStart", "early", T0 - 600, "prd-flow-reviewer")
        self.add("SubagentStop", "early", T0 + 10)
        code, lines, _ = self.run_watch(["s1", "--since", str(T0 - 1000)])
        self.assertEqual(lines, ["done: no agent running"])
        self.assertEqual(code, 0)

    def test_a_start_older_than_the_default_window_is_not_tracked(self):
        self.add("SubagentStart", "old", T0 - 5000, "prd-flow-executor")
        code, lines, _ = self.run_watch()
        self.assertEqual(code, 1)
        self.assertTrue(lines[0].startswith("unknown:"))

    def test_a_start_beyond_the_old_4mb_tail_is_still_seen(self):
        self.add("SubagentStart", "a1", T0 - 60, "prd-flow-executor")
        pad = json.dumps({"ts": T0, "ev": "PreToolUse", "agent": "main", "x": "y" * 1000}) + "\n"
        with self.events.open("a", encoding="utf-8") as f:
            f.write(pad * 4500)
        self.add("SubagentStop", "a1", T0 + 5)
        code, lines, _ = self.run_watch()
        self.assertEqual(lines, ["done: no agent running"])

    def test_stuck_after_10_minutes_without_a_tool_event(self):
        self.add("SubagentStart", "a1", T0 + 1, "prd-flow-executor")
        self.add("PostToolUse", "a1", T0 + 20)
        code, lines, _ = self.run_watch()
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"^stuck: a1 prd-flow-executor idle 1[01] min \(a silent long command is possible\)$")
        self.assertEqual(code, 1)

    def test_a_busy_agent_is_not_stuck_and_the_deadline_names_the_running_ids(self):
        self.add("SubagentStart", "a1", T0 + 1, "prd-flow-executor")
        self.add("SubagentStart", "a2", T0 + 1, "prd-flow-reviewer")

        def busy(clock):
            self.add("PreToolUse", "a1", clock.t)
            self.add("PreToolUse", "a2", clock.t)

        code, lines, clock = self.run_watch(["s1", "--minutes", "12"], hook=busy)
        self.assertEqual(lines, ["deadline: a1 a2"])
        self.assertEqual(code, 1)
        self.assertLessEqual(clock.t - T0, 13 * 60)

    def test_no_start_seen_is_unknown_after_3_minutes_with_exit_1(self):
        code, lines, clock = self.run_watch()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("unknown:"))
        self.assertGreaterEqual(clock.t - T0, 180)
        self.assertLess(clock.t - T0, 240)
        self.assertEqual(code, 1)

    def test_a_missing_events_file_is_unknown_at_once(self):
        self.events.unlink()
        code, lines, clock = self.run_watch()
        self.assertEqual(lines, ["unknown: no events file"])
        self.assertEqual(code, 1)
        self.assertEqual(clock.sleeps, 0)

    def test_the_main_thread_is_never_tracked(self):
        self.add("SubagentStart", "main", T0 + 1)
        code, lines, _ = self.run_watch()
        self.assertEqual(code, 1)
        self.assertTrue(lines[0].startswith("unknown:"))

    def test_bad_arguments_exit_2(self):
        for argv in ([], ["s1", "--minutes", "x"], ["s1", "--minutes"]):
            with self.subTest(argv=argv):
                err = io.StringIO()
                from contextlib import redirect_stderr
                with redirect_stderr(err):
                    self.assertEqual(watch.main(list(argv), root=self.root, now=Clock().now, sleep=Clock().sleep), 2)


if __name__ == "__main__":
    unittest.main()
