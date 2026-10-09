"""Tests of the pure parts of eval/run.py and of eval/arms.json."""

import json
import sys
import unittest
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "eval"
sys.path.insert(0, str(EVAL))
import run  # noqa: E402

CFG = json.loads((EVAL / "arms.json").read_text(encoding="utf-8"))


class RateLimitTest(unittest.TestCase):
    def write(self, lines):
        import tempfile
        f = Path(tempfile.mkdtemp()) / "t.jsonl"
        f.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
        return f

    def test_session_limit_result_is_rate_limited(self):
        f = self.write([{"type": "result", "is_error": True, "api_error_status": 429,
                         "result": "You've hit your session limit"}])
        self.assertEqual(run.classify(f, 1), "rate_limited")

    def test_clean_result_is_ok_and_other_errors_crash(self):
        self.assertEqual(run.classify(self.write([{"type": "result", "is_error": False}]), 0), "ok")
        self.assertEqual(run.classify(self.write([{"type": "result", "is_error": True,
                                                   "subtype": "error_max_budget_usd"}]), 1), "crash")

    def test_arms_filter(self):
        pairs = run.plan_pairs(CFG, arms=["LT"])
        self.assertTrue(pairs and all(p["arm"] == "LT" for p in pairs))


class ConfigTest(unittest.TestCase):
    def test_arms_json_matches_readme_table(self):
        self.assertEqual(CFG["timeout_min"], 60)
        self.assertEqual(CFG["parallel"], 4)
        for arm in ("SKU", "SKF"):
            self.assertEqual(CFG["arms"][arm]["ref"], "eval/speckit-baseline")
            self.assertTrue(CFG["arms"][arm]["spec_kit"])
        self.assertIn("must", (EVAL / CFG["arms"]["SKF"]["protocol"]).read_text(encoding="utf-8"))
        self.assertEqual(CFG["arms"]["LT"]["ref"], "HEAD")
        self.assertFalse(CFG["arms"]["LT"]["spec_kit"])
        caps = {k: (v["reps"], v["budget_usd"]) for k, v in CFG["scenarios"].items()}
        self.assertEqual(caps, {"S1": (2, 8), "S2": (2, 15), "S3": (1, 8), "S4": (1, 8)})

    def test_protocol_files_exist_and_are_plain(self):
        for arm in CFG["arms"].values():
            text = (EVAL / arm["protocol"]).read_text(encoding="utf-8")
            self.assertTrue(text.strip())
            self.assertNotIn(chr(0x2014), text)
        self.assertIn("{protocol}", (EVAL / "prompt.md").read_text(encoding="utf-8"))


class FlowConfigTest(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((EVAL / "arms-flow.json").read_text(encoding="utf-8"))

    def test_arms_scenarios_and_names(self):
        self.assertEqual((self.cfg["base"], self.cfg["candidate"]), ("GATE", "FLOW"))
        self.assertEqual(self.cfg["arms"]["GATE"]["ref"], "fix/existing-repo-adoption")
        self.assertEqual(self.cfg["arms"]["FLOW"]["ref"], "HEAD")
        self.assertIn("/prd-gate", (EVAL / self.cfg["arms"]["GATE"]["protocol"]).read_text(encoding="utf-8"))
        self.assertIn("/prd-flow", (EVAL / self.cfg["arms"]["FLOW"]["protocol"]).read_text(encoding="utf-8"))
        self.assertEqual(sorted(self.cfg["scenarios"]), ["S5", "S6", "S7"])
        self.assertEqual(len(run.plan_pairs(self.cfg)), 8)

    def test_new_scenarios_are_complete(self):
        for sc in self.cfg["scenarios"]:
            folder = EVAL / "scenarios" / sc
            exp = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
            self.assertTrue(exp.get("conflict_ids") or exp.get("gap_topic"), sc)
            self.assertTrue(exp["prd_facts"] and exp["dup_phrases"], sc)
            for name in ("request.md", "decisions.md"):
                self.assertNotIn(chr(0x2014), (folder / name).read_text(encoding="utf-8"))
            self.assertTrue(list((folder / "hidden").glob("test_*.py")), sc)

    def test_build_args_pass_an_existing_overlay_only(self):
        arm = {"ref": "HEAD", "spec_kit": False}
        self.assertIn("--overlay", run.build_args(arm, "o", overlay=EVAL / "scenarios" / "S6" / "files"))
        self.assertNotIn("--overlay", run.build_args(arm, "o", overlay=EVAL / "scenarios" / "S5" / "files"))


class PairsTest(unittest.TestCase):
    def test_pairs_interleaved_per_arm(self):
        pairs = run.plan_pairs(CFG)
        self.assertEqual(len(pairs), 18)
        names = [p["name"] for p in pairs]
        self.assertEqual(names[:3], ["SKU-S1-r1", "SKF-S1-r1", "LT-S1-r1"])
        self.assertEqual(len(set(names)), 18)
        self.assertEqual(next(p for p in pairs if p["name"] == "LT-S2-r2")["budget_usd"], 15)

    def test_only_filter_and_unknown(self):
        self.assertEqual([p["name"] for p in run.plan_pairs(CFG, only=["LT-S3-r1"])], ["LT-S3-r1"])
        with self.assertRaises(SystemExit):
            run.plan_pairs(CFG, only=["XX-S9-r1"])


class CommandTest(unittest.TestCase):
    def test_command(self):
        cmd = run.build_command(12, "claude")
        self.assertEqual(cmd[:6], ["claude", "-p", "--output-format", "stream-json", "--verbose",
                                   "--dangerously-skip-permissions"])
        self.assertEqual(cmd[-2:], ["--max-budget-usd", "12"])

    def test_render_prompt(self):
        out = run.render_prompt("P:{protocol} R:{request} D:{decisions}", " a ", "b\n", " proto \n")
        self.assertEqual(out, "P:proto R:a D:b")

    def test_render_prompt_real_template_has_no_slot_left(self):
        out = run.render_prompt((EVAL / "prompt.md").read_text(encoding="utf-8"), "r", "d", "p")
        for slot in ("{protocol}", "{request}", "{decisions}"):
            self.assertNotIn(slot, out)
        self.assertIn("How this team works", out)

    def test_build_args(self):
        sk = run.build_args(CFG["arms"]["SKF"], "out")
        self.assertIn("--spec-kit", sk)
        self.assertEqual(sk[2:6], ["--ref", "eval/speckit-baseline", "--out", "out"])
        self.assertNotIn("--spec-kit", run.build_args(CFG["arms"]["LT"], "out"))

    def test_build_args_pass_fixture_and_fill_from_the_config(self):
        cmd = run.build_args(CFG["arms"]["LT"], "out", fixture=EVAL / "fixture-large", fill=EVAL / "fixture-large" / "fill.json")
        self.assertEqual(cmd[cmd.index("--fixture") + 1], str(EVAL / "fixture-large"))
        self.assertEqual(cmd[cmd.index("--fill") + 1], str(EVAL / "fixture-large" / "fill.json"))
        self.assertNotIn("--fixture", run.build_args(CFG["arms"]["LT"], "out"))


class LargeConfigTest(unittest.TestCase):
    cfg = json.loads((EVAL / "arms-large.json").read_text(encoding="utf-8"))

    def test_small_config_defaults(self):
        self.assertEqual(run.suite_paths(CFG), (EVAL / "fixture", EVAL / "fixture" / "fill.json", EVAL / "scenarios"))

    def test_large_config_paths(self):
        self.assertEqual(run.suite_paths(self.cfg), (EVAL / "fixture-large", EVAL / "fixture-large" / "fill.json",
                                                     EVAL / "scenarios-large"))

    def test_large_round_decision(self):
        self.assertEqual(set(self.cfg["arms"]), {"LT", "SKU", "SKF"})
        self.assertEqual(self.cfg["timeout_min"], 75)
        self.assertEqual(self.cfg["parallel"], 3)
        self.assertEqual({k: v["budget_usd"] for k, v in self.cfg["scenarios"].items()},
                         {"L1": 10, "L2": 20, "L3": 20, "L4": 8, "L5": 8, "L6": 10, "L7": 10, "L8": 8})
        self.assertTrue(all(v["reps"] == 2 for v in self.cfg["scenarios"].values()))
        self.assertEqual(len(run.plan_pairs(self.cfg)), 48)
        for arm in self.cfg["arms"]:
            self.assertEqual(self.cfg["arms"][arm], CFG["arms"][arm])


class HermeticRunTest(unittest.TestCase):
    def test_env_points_to_a_fresh_folder_with_only_the_credentials(self):
        import shutil
        import tempfile
        src = Path(tempfile.mkdtemp())
        (src / ".credentials.json").write_text("{}", encoding="utf-8")
        (src / "CLAUDE.md").write_text("personal", encoding="utf-8")
        tmp, env = run.hermetic_env({"CLAUDE_CODE_SESSION_ID": "x", "CLAUDECODE": "1", "PATH": "p"}, src)
        self.addCleanup(shutil.rmtree, tmp, True)
        self.assertEqual(env["CLAUDE_CONFIG_DIR"], str(tmp))
        self.assertEqual(sorted(p.name for p in tmp.iterdir()), [".credentials.json"])
        self.assertEqual(env.get("PATH"), "p")
        self.assertNotIn("CLAUDECODE", env)
        self.assertNotIn("CLAUDE_CODE_SESSION_ID", env)

    def test_command_pins_model_effort_and_sources(self):
        cmd = run.build_command(5, "claude", "opus", "medium")
        self.assertEqual(cmd[cmd.index("--model") + 1], "opus")
        self.assertEqual(cmd[cmd.index("--effort") + 1], "medium")
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "project,local")
        self.assertNotIn("--model", run.build_command(5, "claude"))


class BigConfigTest(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((EVAL / "arms-big.json").read_text(encoding="utf-8"))

    def test_arms_scenarios_and_pins(self):
        self.assertEqual(self.cfg["arms"]["GATE"]["ref"], "fix/existing-repo-adoption")
        self.assertEqual(self.cfg["arms"]["FLOW"]["ref"], "HEAD")
        fast = self.cfg["arms"]["FLOW-FAST"]
        self.assertTrue(fast["two_phase"])
        self.assertEqual(fast["phase2_model"], "sonnet")
        self.assertEqual({k: v["reps"] for k, v in self.cfg["scenarios"].items()}, {"S5": 3, "S6": 1, "S7": 1, "S8": 1})
        self.assertTrue(self.cfg["model"] and self.cfg["effort"])
        self.assertEqual(len(run.plan_pairs(self.cfg)), 18)

    def test_phase_prompts_exist_and_resume(self):
        self.assertIn("/prd-flow resume {slug}", (EVAL / "prompt-phase2.md").read_text(encoding="utf-8"))
        self.assertIn("approved and committed", (EVAL / "prompt-phase1.md").read_text(encoding="utf-8"))
        self.assertEqual(run.render_phase2("resume {slug} {decisions}", "s", " d "), "resume s d")

    def test_state_slug_reads_the_state_folder(self):
        import tempfile
        root = Path(tempfile.mkdtemp())
        (root / ".claude/prd-flow/state/_close").mkdir(parents=True)
        (root / ".claude/prd-flow/state/min-order").mkdir()
        (root / ".claude/prd-flow/state/min-order/approved-rules.md").write_text("x", encoding="utf-8")
        self.assertEqual(run.state_slug(root), "min-order")

    def test_s8_is_complete(self):
        folder = EVAL / "scenarios" / "S8"
        exp = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
        self.assertEqual(exp["expected_waves"], 2)
        self.assertTrue(exp["gap_topic"] and exp["prd_facts"] and exp["dup_phrases"])
        for name in ("request.md", "decisions.md"):
            self.assertNotIn(chr(0x2014), (folder / name).read_text(encoding="utf-8"))
        self.assertTrue(list((folder / "hidden").glob("test_*.py")))


class ReviewFixesTest(unittest.TestCase):
    def _src(self):
        import tempfile
        src = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, src, True)
        return src

    def test_auth_variables_survive_the_env_filter(self):
        import shutil
        env = {"CLAUDE_CODE_OAUTH_TOKEN": "t", "CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "r",
               "CLAUDE_CODE_SESSION_ID": "x", "ANTHROPIC_API_KEY": "k"}
        tmp, out = run.hermetic_env(env, self._src())
        self.addCleanup(shutil.rmtree, tmp, True)
        for k in ("CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK", "AWS_REGION", "ANTHROPIC_API_KEY"):
            self.assertIn(k, out)
        self.assertNotIn("CLAUDE_CODE_SESSION_ID", out)

    def test_no_credentials_and_no_auth_variable_fails_early_and_cleans(self):
        import tempfile
        before = set(Path(tempfile.gettempdir()).glob("ai-kit-claude-*"))
        with self.assertRaises(RuntimeError) as ctx:
            run.hermetic_env({"PATH": "p"}, self._src())
        self.assertIn("credentials", str(ctx.exception))
        self.assertEqual(set(Path(tempfile.gettempdir()).glob("ai-kit-claude-*")), before)

    def test_state_slug_picks_the_newest_approved_state(self):
        import os
        root = self._src()
        base = root / ".claude/prd-flow/state"
        for name, t in (("old", 100), ("new", 200)):
            (base / name).mkdir(parents=True)
            f = base / name / "approved-rules.md"
            f.write_text("x", encoding="utf-8")
            os.utime(f, (t, t))
        (base / "unapproved").mkdir()
        self.assertEqual(run.state_slug(root), "new")

    def test_state_slug_falls_back_to_the_newest_change_folder(self):
        root = self._src()
        (root / ".claude/prd-flow/state/_close").mkdir(parents=True)
        for n in ("001-first", "002-min-order", "archive"):
            (root / "changes" / n).mkdir(parents=True)
        self.assertEqual(run.state_slug(root), "min-order")
        self.assertIsNone(run.state_slug(self._src()))

    def test_state_slug_fallback_ignores_folders_of_the_seed_commit(self):
        import subprocess
        root = self._src()
        git = lambda *a: subprocess.run(["git", "-C", str(root), *a], check=True, capture_output=True)
        git("init", "-q")
        (root / "changes/009-old").mkdir(parents=True)
        (root / "changes/009-old/brief.md").write_text("x", encoding="utf-8")
        git("add", "-A")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "seed")
        self.assertIsNone(run.state_slug(root))
        (root / "changes/010-new-one").mkdir()
        self.assertEqual(run.state_slug(root), "new-one")

    def test_phase_budgets_split_70_30(self):
        self.assertEqual(run.split_budget(10), (7.0, 3.0))


class AdoptionGateTest(unittest.TestCase):
    def test_run_without_hidden_result_fails_the_gate(self):
        import adoption
        ok = {"hidden_passed": 4, "hidden_total": 4}
        gate = adoption.hard_gates({"S5": [ok, {"status": "crash"}]})[0]
        self.assertFalse(gate[1])
        self.assertIn("1 had no hidden result", gate[2])


class NoSkillAndRunMetricsTest(unittest.TestCase):
    def test_build_args_append_no_skill_only_when_configured(self):
        self.assertIn("--no-skill", run.build_args({"ref": "HEAD", "spec_kit": False, "no_skill": True}, "o"))
        self.assertNotIn("--no-skill", run.build_args({"ref": "HEAD", "spec_kit": False}, "o"))

    def test_lite_config_plain_arm_is_no_skill(self):
        cfg = json.loads((EVAL / "arms-lite.json").read_text(encoding="utf-8"))
        self.assertTrue(cfg["arms"]["PLAIN"]["no_skill"])

    def test_task_output_left_bytes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "proj"
            project.mkdir()
            self.assertEqual(run.task_output_left_bytes(project, Path(tmp) / "claude"), 0)
            tasks = Path(tmp) / "claude" / run.project_slug(project) / "sess" / "tasks"
            tasks.mkdir(parents=True)
            (tasks / "a.output").write_bytes(b"x" * 10)
            (tasks / "b.output").write_bytes(b"y" * 5)
            (tasks / "c.txt").write_bytes(b"z" * 99)
            self.assertEqual(run.task_output_left_bytes(project, Path(tmp) / "claude"), 15)

    def test_run_metrics_from_transcript_files(self):
        import tempfile
        import interview_metrics as im
        events = [
            {"type": "assistant", "cwd": "/p", "message": {"id": "m1", "usage": {"output_tokens": 100}, "content": [
                {"type": "tool_use", "id": "a1", "name": "Agent", "input": {"description": "x"}},
                {"type": "tool_use", "id": "e1", "name": "Edit", "input": {"file_path": "/p/docs/prd/a.md"}}]}},
            {"type": "assistant", "cwd": "/p", "message": {"id": "m2", "usage": {"output_tokens": 300}, "content": [
                {"type": "tool_use", "id": "e2", "name": "Write", "input": {"file_path": "/p/src/a.py"}},
                {"type": "tool_use", "id": "e3", "name": "Write", "input": {"file_path": "/p/changes/001-x/plan.md"}}]}},
            {"type": "assistant", "cwd": "/p", "message": {"id": "m3", "usage": {"output_tokens": 50}, "content": [
                {"type": "text", "text": "no edits"}]}},
        ]
        got = im.run_metrics(events)
        self.assertEqual(got["agents_dispatched"], 1)
        self.assertEqual((got["docs_output_tokens"], got["code_output_tokens"]), (100, 300))
        self.assertAlmostEqual(got["docs_to_code_ratio"], 100 / 300)
        self.assertIsNone(im.run_metrics([])["docs_to_code_ratio"])
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "t.jsonl"
            f.write_text("\n".join(json.dumps(e) for e in events) + "\nnot json\n", encoding="utf-8")
            self.assertEqual(run.load_events([f])[0]["message"]["id"], "m1")
            self.assertEqual(len(run.load_events([f])), 3)


if __name__ == "__main__":
    unittest.main()
