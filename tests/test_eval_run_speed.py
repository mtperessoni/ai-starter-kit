"""W6.1: run-speed metrics from a transcript (baseline_runs, poll_calls, bg_alive_at_return, question_rounds,
rejected_answers, bash_code_edits, git_unsafe_calls), their scorecard wiring and the W6.2 scenario files."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import protocol  # noqa: E402
import run  # noqa: E402
import six  # noqa: E402
import transcript  # noqa: E402

_n = [0]
KEYS = ("baseline_runs", "poll_calls", "bg_alive_at_return", "question_rounds", "rejected_answers",
        "bash_code_edits", "git_unsafe_calls", "verify_runs", "agent_test_runs")


def asst(blocks, parent=None):
    _n[0] += 1
    return {"type": "assistant", "parent_tool_use_id": parent, "cwd": "/p",
            "message": {"id": f"m{_n[0]}", "model": "x", "content": blocks,
                        "usage": {"input_tokens": 1, "output_tokens": 1, "cache_read_input_tokens": 0,
                                  "cache_creation_input_tokens": 5}}}


def use(tid, name, **inp):
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


def res(tid, text="ok", parent=None, error=False):
    b = {"type": "tool_result", "tool_use_id": tid, "content": text}
    if error:
        b["is_error"] = True
    return {"type": "user", "parent_tool_use_id": parent, "message": {"content": [b]}}


def bash(cmd, parent=None, tid=None, **extra):
    _n[0] += 1
    return asst([use(tid or f"b{_n[0]}", "Bash", command=cmd, **extra)], parent)


def metrics(*events):
    return protocol.analyze(list(events))


class BaselineRunsTest(unittest.TestCase):
    def count(self, cmd, parent=None):
        return metrics(bash(cmd, parent))["baseline_runs"]

    def test_baseline_counts_but_the_closing_compare_does_not(self):
        self.assertEqual(self.count("scripts/gates.sh baseline plan-1"), 1)
        self.assertEqual(self.count("scripts/gates.sh baseline plan-1 --bg"), 1)
        self.assertEqual(self.count("scripts/gates.sh compare plan-1"), 0)
        self.assertEqual(self.count("scripts/gates.sh close plan-1"), 0)

    def test_full_suite_by_any_agent(self):
        self.assertEqual(self.count("python -m pytest -q"), 1)
        self.assertEqual(self.count("python -m pytest tests/ -q", parent="a1"), 1)
        self.assertEqual(self.count("python -m unittest discover -s tests"), 1)
        self.assertEqual(self.count("yarn test"), 1)

    def test_narrow_runs_do_not_count(self):
        self.assertEqual(self.count("python -m pytest tests/test_a.py -q"), 0)
        self.assertEqual(self.count("python -m unittest tests.test_a"), 0)
        self.assertEqual(self.count("scripts/gates.sh related src/a.py"), 0)
        self.assertEqual(self.count("scripts/gates.sh one tests/test_a.py"), 0)

    def test_counts_add_over_calls(self):
        a = metrics(bash("scripts/gates.sh baseline x"), bash("pytest -q", "a1"), bash("ls"))
        self.assertEqual(a["baseline_runs"], 2)


class PollCallsTest(unittest.TestCase):
    def count(self, cmd):
        return metrics(bash(cmd))["poll_calls"]

    def test_loops_with_sleep(self):
        self.assertEqual(self.count("until [ -f out.txt ]; do sleep 5; done"), 1)
        self.assertEqual(self.count("while kill -0 $PID; do sleep 2; done"), 1)
        self.assertEqual(self.count("for i in $(seq 1 30); do sleep 10; ls; done"), 1)
        self.assertEqual(self.count("until grep -q done log\ndo\n  sleep 3\ndone"), 1)

    def test_seq_loop_without_sleep_counts(self):
        self.assertEqual(self.count("for i in $(seq 1 20); do tail -1 log; done"), 1)

    def test_plain_commands_do_not_count(self):
        self.assertEqual(self.count("sleep 5"), 0)
        self.assertEqual(self.count("for f in a b; do echo $f; done"), 0)
        self.assertEqual(self.count("python -m pytest -q"), 0)


class BackgroundAliveTest(unittest.TestCase):
    def test_launch_never_collected_is_alive(self):
        ev = [bash("pytest -q", parent="a1", tid="bg1", run_in_background=True),
              res("bg1", "Command running in background with ID: sh7", parent="a1")]
        self.assertEqual(metrics(*ev)["bg_alive_at_return"], 1)

    def test_collected_or_stopped_is_not_alive(self):
        ev = [bash("pytest -q", parent="a1", tid="bg1", run_in_background=True),
              res("bg1", "Command running in background with ID: sh7", parent="a1"),
              asst([use("o1", "BashOutput", bash_id="sh7")], "a1")]
        self.assertEqual(metrics(*ev)["bg_alive_at_return"], 0)
        ev[2] = asst([use("k1", "TaskStop", task_id="sh7")], "a1")
        self.assertEqual(metrics(*ev)["bg_alive_at_return"], 0)

    def test_foreground_and_main_thread_do_not_count(self):
        self.assertEqual(metrics(bash("pytest -q", parent="a1"))["bg_alive_at_return"], 0)
        ev = [bash("pytest -q", tid="bg1", run_in_background=True), res("bg1", "ID: sh1")]
        self.assertEqual(metrics(*ev)["bg_alive_at_return"], 0)

    def test_nohup_launch_is_alive(self):
        self.assertEqual(metrics(bash("nohup pytest -q > out.txt 2>&1 &", parent="a1"))["bg_alive_at_return"], 1)
        self.assertEqual(metrics(bash("pytest -q & wait", parent="a1"))["bg_alive_at_return"], 0)


class QuestionRoundsTest(unittest.TestCase):
    def ask(self, tid, answer, parent=None, error=False):
        return [asst([use(tid, "AskUserQuestion", questions=[{"question": "Which?"}])], parent),
                res(tid, answer, error=error)]

    def test_rounds_and_rejections(self):
        ev = (self.ask("q1", 'User has answered your questions: "Which?"="Option A". You can now continue.')
              + self.ask("q2", 'User has answered your questions: "Which?"="The scenario is wrong".')
              + self.ask("q3", "The user doesn't want to proceed with this tool use.", error=True))
        a = metrics(*ev)
        self.assertEqual((a["question_rounds"], a["rejected_answers"]), (3, 2))

    def test_question_text_alone_is_not_a_rejection(self):
        ev = self.ask("q1", 'User has answered your questions: "Is the scenario wrong?"="Yes, split it".')
        self.assertEqual(metrics(*ev)["rejected_answers"], 0)

    def test_no_questions(self):
        a = metrics(bash("ls"))
        self.assertEqual((a["question_rounds"], a["rejected_answers"]), (0, 0))


class BashCodeEditsTest(unittest.TestCase):
    def count(self, cmd, parent=None):
        return metrics(bash(cmd, parent))["bash_code_edits"]

    def test_in_place_edits_of_source(self):
        self.assertEqual(self.count("sed -i 's/a/b/' src/orders/x.py"), 1)
        self.assertEqual(self.count("perl -pi -e 's/a/b/' src/orders/x.py", "a1"), 1)
        self.assertEqual(self.count("sed -i.bak 's/a/b/' tests/test_x.py"), 1)

    def test_python_writes_into_source(self):
        self.assertEqual(self.count("python - <<'EOF'\nfrom pathlib import Path\nPath('src/a.py').write_text('x')\nEOF"), 1)
        self.assertEqual(self.count("python -c \"open('src/a.py','w').write('x')\""), 1)

    def test_heredoc_and_redirect_into_source(self):
        self.assertEqual(self.count("cat > src/a.py <<'EOF'\nx = 1\nEOF"), 1)
        self.assertEqual(self.count("echo 'x' >> src/orders/b.py"), 1)

    def test_docs_reads_and_plain_python_do_not_count(self):
        self.assertEqual(self.count("sed -i 's/a/b/' docs/prd/x.md"), 0)
        self.assertEqual(self.count("sed -n '1,20p' src/a.py"), 0)
        self.assertEqual(self.count("python -m pytest -q"), 0)
        self.assertEqual(self.count("cat src/a.py"), 0)
        self.assertEqual(self.count("python - <<'EOF'\nprint(open('src/a.py').read())\nEOF"), 0)


class GitUnsafeCallsTest(unittest.TestCase):
    def test_only_inside_subagents(self):
        for cmd in ("git stash", "git reset --hard HEAD", "git checkout -- a.py", "git switch main",
                    "git restore a.py", "git commit --amend --no-edit", "git -C /p stash pop"):
            self.assertEqual(metrics(bash(cmd, "a1"))["git_unsafe_calls"], 1, cmd)
            self.assertEqual(metrics(bash(cmd))["git_unsafe_calls"], 0, cmd)

    def test_safe_git_does_not_count(self):
        for cmd in ("git status", "git commit -m x", "git diff --stat", "git log --oneline", "git add a.py"):
            self.assertEqual(metrics(bash(cmd, "a1"))["git_unsafe_calls"], 0, cmd)


class VerifyAndAgentTestRunsTest(unittest.TestCase):
    def test_verify_runs_count_by_any_agent_and_are_not_baselines(self):
        m = metrics(bash("scripts/gates.sh verify plan-1"), bash("scripts/gates.sh verify plan-1 --wave 2"),
                    bash("scripts/gates.sh compare plan-1"))
        self.assertEqual((m["verify_runs"], m["baseline_runs"]), (2, 0))

    def test_agent_test_runs_count_gate_and_suite_runs_in_subagents(self):
        for cmd in ("scripts/gates.sh related src/a.py", "scripts/gates.sh baseline x", "scripts/gates.sh verify x",
                    "python -m pytest -q", "python -m pytest tests/ -q", "python -m pytest tests/a.py tests/b.py",
                    "python -m unittest discover -s tests", "yarn test", "scripts/gates.sh lint"):
            self.assertEqual(metrics(bash(cmd, "a1"))["agent_test_runs"], 1, cmd)
            self.assertEqual(metrics(bash(cmd))["agent_test_runs"], 0, cmd)

    def test_a_single_named_test_file_is_allowed(self):
        for cmd in ("scripts/gates.sh one tests/test_a.py", "python -m pytest tests/test_a.py -q",
                    "python -m pytest tests/test_a.py::T::test_x", "python -m unittest tests.test_a", "git status"):
            self.assertEqual(metrics(bash(cmd, "a1"))["agent_test_runs"], 0, cmd)


class WiringTest(unittest.TestCase):
    def test_all_keys_reach_the_scorecard(self):
        for k in KEYS:
            self.assertIn(k, six.FLOW_KEYS)
            self.assertEqual(six.DIRECTION[k], six.LOWER)
            self.assertIn(k, six.ADDITIVE)
            self.assertIn(k, transcript.SUM_KEYS)
        listed = {f for _, fields in six.METRICS.values() for f in fields}
        for k in KEYS + ("cold_starts",):
            self.assertIn(k, listed)

    def test_every_key_is_defined_in_metrics_md(self):
        text = (ROOT / "eval" / "METRICS.md").read_text(encoding="utf-8")
        for k in KEYS:
            self.assertIn(f"`{k}`", text)

    def test_phases_add(self):
        d = tempfile.TemporaryDirectory()
        p1, p2 = Path(d.name) / "r.jsonl", Path(d.name) / "r.p2.jsonl"
        w = lambda p, ev: p.write_text("\n".join(json.dumps(e) for e in ev), encoding="utf-8")
        w(p1, [bash("scripts/gates.sh baseline a")])
        w(p2, [bash("pytest -q", "a1"), bash("git stash", "a1")])
        s = transcript.summarize_phases([str(p1), str(p2)])
        self.assertEqual((s["baseline_runs"], s["git_unsafe_calls"]), (2, 1))


class SiblingBuildTest(unittest.TestCase):
    def test_build_args_pass_the_siblings_of_a_scenario(self):
        d = tempfile.TemporaryDirectory()
        (Path(d.name) / "siblings.json").write_text(json.dumps({"storefront": "fixture-storefront"}), encoding="utf-8")
        args = run.build_args({"ref": "HEAD", "spec_kit": False}, Path(d.name) / "out", siblings=Path(d.name) / "siblings.json")
        self.assertIn("--sibling", args)
        self.assertIn("storefront=" + str(ROOT / "eval" / "fixture-storefront"), args)
        self.assertNotIn("--sibling", run.build_args({"ref": "HEAD", "spec_kit": False}, Path(d.name) / "out"))

    def test_build_makes_a_sibling_repo_and_lists_it(self):
        d = tempfile.TemporaryDirectory()
        out = Path(d.name) / "p"
        done = subprocess.run([sys.executable, str(ROOT / "eval" / "build.py"), "--ref", "HEAD", "--out", str(out),
                               "--sibling", f"storefront={ROOT / 'eval' / 'fixture-storefront'}"],
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        sib = Path(d.name) / "p-storefront"
        self.assertTrue((sib / "src" / "storefront" / "features" / "customers" / "customer_payload.py").is_file())
        self.assertTrue((sib / ".git").is_dir())
        repos = json.loads((out / ".ai-kit" / "repos.json").read_text(encoding="utf-8"))
        self.assertEqual([(r["alias"], Path(r["path"]).resolve()) for r in repos["repos"]],
                         [("storefront", sib.resolve())])


class ScenarioFilesTest(unittest.TestCase):
    SCEN = ROOT / "eval" / "scenarios"

    def test_s9_s10_s11_have_the_standard_files(self):
        for s in ("S9", "S10", "S11"):
            for f in ("request.md", "decisions.md", "expected.json"):
                self.assertTrue((self.SCEN / s / f).is_file(), f"{s}/{f}")
            exp = json.loads((self.SCEN / s / "expected.json").read_text(encoding="utf-8"))
            self.assertEqual(exp["case"], "C5")
            self.assertTrue(exp["prd_facts"])
            self.assertTrue(list((self.SCEN / s / "hidden").glob("test_*.py")), s)

    def test_expected_metrics_are_known_fields(self):
        for s in ("S9", "S10", "S11"):
            exp = json.loads((self.SCEN / s / "expected.json").read_text(encoding="utf-8"))
            for k in exp.get("expect_metrics", {}):
                self.assertIn(k, KEYS + ("cold_starts", "dispatch_map"), f"{s}:{k}")

    def test_round_arms_file(self):
        cfg = json.loads((ROOT / "eval" / "arms-run-speed.json").read_text(encoding="utf-8"))
        self.assertEqual({k: v["reps"] for k, v in cfg["scenarios"].items()},
                         {"S5": 2, "S8": 1, "S9": 1, "S10": 1})
        self.assertEqual(set(cfg["arms"]), {"BASE", "CAND"})
        self.assertTrue((ROOT / "eval" / "predictions" / "run-speed.md").is_file())


if __name__ == "__main__":
    unittest.main()
