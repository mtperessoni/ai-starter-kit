"""Metric fixes of AUDIT-v5 section 6, the phase-2 prompt, arms-short.json and eval/agents_report.py."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import agents_report  # noqa: E402
import grade  # noqa: E402
import protocol  # noqa: E402
import run  # noqa: E402
import transcript  # noqa: E402

CWD = "/p"
_n = [0]


def asst(blocks, parent=None, ts=None, model="claude-opus-4-8", usage=None, mid=None):
    _n[0] += 1
    e = {"type": "assistant", "parent_tool_use_id": parent, "cwd": CWD,
         "message": {"id": mid or f"m{_n[0]}", "model": model, "content": blocks,
                     "usage": usage or {"input_tokens": 10, "output_tokens": 5,
                                        "cache_read_input_tokens": 100, "cache_creation_input_tokens": 20}}}
    if ts is not None:
        e["timestamp"] = f"2026-10-08T10:{ts // 60:02d}:{ts % 60:02d}Z"
    return e


def use(tid, name, **inp):
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


def res(tid, text="ok", parent=None, ts=None):
    e = {"type": "user", "parent_tool_use_id": parent,
         "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "content": text}]}}
    if ts is not None:
        e["timestamp"] = f"2026-10-08T10:{ts // 60:02d}:{ts % 60:02d}Z"
    return e


def spawn(tid, kind, desc="", prompt="", ts=None):
    return asst([use(tid, "Agent", subagent_type=f"prd-flow-{kind}", description=desc, prompt=prompt)], ts=ts)


def after_surveyor(*more):
    return [spawn("s1", "surveyor"), res("s1", "done"), *more]


class ViolationCategoriesTest(unittest.TestCase):
    def count(self, events):
        return protocol.analyze(events)

    def test_incoming_request_read_does_not_count(self):
        a = self.count([asst([use("r", "Read", file_path="/p/docs/incoming/spec.md")]), spawn("s1", "surveyor")])
        self.assertEqual(a["main_violations"], 0)

    def test_other_docs_read_before_surveyor_still_counts(self):
        a = self.count([asst([use("r", "Read", file_path="/p/docs/prd/x.md")]), spawn("s1", "surveyor")])
        self.assertEqual(a["main_violations"], 1)

    def test_source_read_after_surveyor_counts(self):
        a = self.count(after_surveyor(asst([use("r", "Read", file_path="/p/src/shop/cart.py")])))
        self.assertEqual(a["main_source_reads"], 1)
        self.assertEqual(a["main_violations"], 1)

    def test_state_and_docs_reads_after_surveyor_are_free(self):
        a = self.count(after_surveyor(
            asst([use("r", "Read", file_path="/p/.claude/prd-flow/state/x/impact.md")]),
            asst([use("q", "Read", file_path="/p/docs/prd/INDEX.md")])))
        self.assertEqual(a["main_violations"], 0)

    def test_diff_read_after_surveyor_counts_but_stat_does_not(self):
        a = self.count(after_surveyor(
            asst([use("d", "Bash", command="git diff src/a.py")]),
            asst([use("e", "Bash", command="git diff --stat -- src/a.py && git add src/a.py")])))
        self.assertEqual(a["main_diff_reads"], 1)
        self.assertEqual(a["main_violations"], 1)

    def test_kit_script_read_counts(self):
        a = self.count(after_surveyor(
            asst([use("k", "Read", file_path="/p/.claude/skills/prd-flow/scripts/promote.py")]),
            asst([use("g", "Bash", command="python scripts/gate.py --rules")])))
        self.assertEqual(a["kit_script_reads"], 1)

    def test_agent_file_edit_counts(self):
        a = self.count(after_surveyor(
            asst([use("e", "Edit", file_path="/p/.claude/prd-flow/state/x/deliveries.md")]),
            asst([use("f", "Write", file_path="/p/.claude/prd-flow/state/x/state.md")])))
        self.assertEqual(a["agent_file_edits"], 1)
        self.assertEqual(a["main_violations"], 1)

    def test_retro_reread_counts(self):
        a = self.count(after_surveyor(
            asst([use("t", "Bash", command="cat .claude/prd-flow/state/x/retro.md")])))
        self.assertEqual(a["retro_rereads"], 1)

    def test_no_surveyor_no_executor_is_none(self):
        self.assertIsNone(self.count([asst([use("r", "Read", file_path="/p/src/a.py")])])["main_violations"])


class WaveTest(unittest.TestCase):
    def test_fix_dispatch_does_not_open_a_wave(self):
        ev = [spawn("e1", "executor", "T01 build", "T01", ts=0), res("e1", "ok", ts=60),
              spawn("r1", "reviewer", "review", ts=61), res("r1", "ok", ts=100),
              spawn("e2", "executor", "Fix review findings", "fix F-1", ts=101), res("e2", "ok", ts=130)]
        a = protocol.analyze(ev)
        self.assertEqual(a["waves"], 1)
        self.assertEqual(a["wave_widths"], [1])
        self.assertEqual(a["agents_by_role"]["executor"], 2)

    def test_parallel_factor_uses_executor_segments_only(self):
        ev = [asst([use("e1", "Agent", subagent_type="prd-flow-executor", description="T01", prompt="T01"),
                    use("e2", "Agent", subagent_type="prd-flow-executor", description="T02", prompt="T02")], ts=0),
              res("e1", "ok", ts=60), res("e2", "ok", ts=60),
              spawn("r1", "reviewer", "review", ts=61), res("r1", "ok", ts=200),
              spawn("e3", "executor", "T03", "T03", ts=300), res("e3", "ok", ts=360)]
        a = protocol.analyze(ev)
        self.assertAlmostEqual(a["parallel_factor"], 180 / 120)


class TraceabilityTest(unittest.TestCase):
    def test_dec_and_q_rows_are_not_rules(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        root = Path(d.name)
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@t", "PATH": __import__("os").environ["PATH"]}

        def git(*a):
            subprocess.run(["git", *a], cwd=root, check=True, capture_output=True, env=env)

        git("init", "-q")
        (root / "docs" / "prd").mkdir(parents=True)
        (root / "docs" / "prd" / "a.md").write_text("# a\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "seed")
        seed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
        (root / "docs" / "prd" / "a.md").write_text(
            "| PRC-02 | rule |\n| DEC-01 | why |\n| Q-03 | ask |\n| DEC-02 | x |\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-qm", "rules")
        self.assertEqual(grade.prd_diff_ids(str(root), seed), ["PRC-02"])


class CostAndWallTest(unittest.TestCase):
    def write(self, events):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = Path(d.name) / "t.jsonl"
        p.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
        return p

    def test_cost_by_role_and_model(self):
        big = {"input_tokens": 0, "output_tokens": 1_000_000, "cache_read_input_tokens": 0,
               "cache_creation_input_tokens": 0}
        ev = [{"type": "system", "subtype": "init", "model": "claude-opus-4-8"},
              asst([use("a1", "Agent", subagent_type="prd-flow-surveyor", description="survey")],
                   usage=big, mid="main1"),
              asst([{"type": "text", "text": "x"}], parent="a1", model="claude-sonnet-5-5", usage=big, mid="sub1"),
              {"type": "result", "subtype": "success", "duration_ms": 60000, "total_cost_usd": 40.0,
               "modelUsage": {"claude-opus-4-8": {"costUSD": 25.0}, "claude-sonnet-5-5": {"costUSD": 15.0}}}]
        s = transcript.summarize(self.write(ev))
        self.assertAlmostEqual(s["cost_by_role"]["main"], 25.0)
        self.assertAlmostEqual(s["cost_by_role"]["surveyor"], 15.0)
        self.assertAlmostEqual(s["cost_main_usd"], 25.0)
        self.assertAlmostEqual(s["cost_subagents_usd"], 15.0)

    def test_wall_is_the_sum_of_result_events(self):
        ev = [{"type": "result", "subtype": "success", "duration_ms": 81000},
              {"type": "result", "subtype": "success", "duration_ms": 3000},
              {"type": "result", "subtype": "success", "duration_ms": 438000, "total_cost_usd": 1.0}]
        s = transcript.summarize(self.write(ev))
        self.assertAlmostEqual(s["wall_min"], 522 / 60)


class HarnessTest(unittest.TestCase):
    def test_auto_memory_is_off_in_command_and_env(self):
        cmd = run.build_command(5, "claude")
        i = cmd.index("--settings")
        self.assertEqual(json.loads(cmd[i + 1]), {"autoMemoryEnabled": False})
        self.assertEqual(cmd[-2:], ["--max-budget-usd", "5"])
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        (Path(d.name) / ".credentials.json").write_text("{}", encoding="utf-8")
        tmp, env = run.hermetic_env({"PATH": "p"}, d.name)
        self.addCleanup(__import__("shutil").rmtree, tmp, True)
        self.assertEqual(env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"], "1")

    def test_phase2_prompt_keeps_reviewer_and_loads_skill_and_state(self):
        text = (ROOT / "eval" / "prompt-phase2.md").read_text(encoding="utf-8")
        self.assertIn("prd-flow-reviewer", text)
        self.assertIn("state.md", text)
        self.assertRegex(text.lower(), r"prd-flow skill")

    def test_arms_short(self):
        cfg = json.loads((ROOT / "eval" / "arms-short.json").read_text(encoding="utf-8"))
        big = json.loads((ROOT / "eval" / "arms-big.json").read_text(encoding="utf-8"))
        self.assertEqual(list(cfg["arms"]), ["FLOW-FAST"])
        self.assertEqual(cfg["arms"]["FLOW-FAST"], big["arms"]["FLOW-FAST"])
        self.assertEqual((cfg["model"], cfg["effort"]), (big["model"], big["effort"]))
        self.assertEqual({k: v["reps"] for k, v in cfg["scenarios"].items()}, {"S5": 3, "S7": 1, "S8": 1})


class AgentsReportTest(unittest.TestCase):
    def folder(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        long_prompt = "x" * 4500
        main = [
            {"type": "system", "subtype": "init", "model": "claude-opus-4-8"},
            asst([use("a1", "Agent", subagent_type="prd-flow-executor", description="T01", prompt=long_prompt)],
                 ts=0, mid="mm1"),
            asst([use("a2", "Read", file_path="/p/a.md")], ts=1, mid="mm2"),
            asst([use("a3", "Read", file_path="/p/a.md")], ts=2, mid="mm3"),
            asst([use("c1", "Read", file_path="/p/src/a.py")], parent="a1", ts=3, model="claude-sonnet-5-5", mid="sub1"),
            asst([use("c2", "Read", file_path="/p/src/a.py")], parent="a1", ts=5, model="claude-sonnet-5-5", mid="sub2"),
            res("a1", "r" * 2500, ts=7),
            {"type": "result", "subtype": "success", "duration_ms": 420000, "total_cost_usd": 1.0,
             "modelUsage": {"claude-opus-4-8": {"costUSD": 0.5}, "claude-sonnet-5-5": {"costUSD": 0.5}}},
        ]
        (Path(d.name) / "FLOW-FAST-S8-r1.jsonl").write_text(
            "\n".join(json.dumps(e) for e in main), encoding="utf-8")
        return d

    def test_rows_and_flags(self):
        d = self.folder()
        runs = agents_report.report_runs(d.name, arm="FLOW-FAST", scenario="S8")
        self.assertEqual(len(runs), 1)
        rows = {r["role"]: r for r in runs[0]["rows"]}
        self.assertEqual(set(rows), {"main", "executor"})
        ex = rows["executor"]
        self.assertEqual(ex["model"], "claude-sonnet-5-5")
        self.assertEqual(ex["prompt_chars"], 4500)
        self.assertEqual(ex["return_chars"], 2500)
        self.assertEqual((ex["reads"], ex["files"], ex["rereads"]), (2, 1, 1))
        self.assertEqual(rows["main"]["rereads"], 1)
        self.assertIn("prompt over 4000 chars", ex["flags"])
        self.assertIn("return over 2000 chars", ex["flags"])
        self.assertNotIn("reads over 25 files", ex["flags"])

    def test_markdown_and_filters(self):
        d = self.folder()
        md = agents_report.render(agents_report.report_runs(d.name))
        self.assertIn("FLOW-FAST-S8-r1", md)
        self.assertIn("| main |", md)
        self.assertEqual(agents_report.report_runs(d.name, arm="GATE"), [])


if __name__ == "__main__":
    unittest.main()
