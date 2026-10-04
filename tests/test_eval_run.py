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
        self.assertEqual(CFG["arms"]["LT"]["ref"], "feat/living-truth")
        self.assertFalse(CFG["arms"]["LT"]["spec_kit"])
        caps = {k: (v["reps"], v["budget_usd"]) for k, v in CFG["scenarios"].items()}
        self.assertEqual(caps, {"S1": (2, 8), "S2": (2, 15), "S3": (1, 8), "S4": (1, 8)})

    def test_protocol_files_exist_and_are_plain(self):
        for arm in CFG["arms"].values():
            text = (EVAL / arm["protocol"]).read_text(encoding="utf-8")
            self.assertTrue(text.strip())
            self.assertNotIn("—", text)
        self.assertIn("{protocol}", (EVAL / "prompt.md").read_text(encoding="utf-8"))


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


if __name__ == "__main__":
    unittest.main()
