"""Tests of the pure parts of eval/run.py and of eval/arms.json."""

import json
import sys
import unittest
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "eval"
sys.path.insert(0, str(EVAL))
import run  # noqa: E402

CFG = json.loads((EVAL / "arms.json").read_text(encoding="utf-8"))


class ConfigTest(unittest.TestCase):
    def test_arms_json_matches_readme_table(self):
        self.assertEqual(CFG["timeout_min"], 60)
        self.assertEqual(CFG["parallel"], 4)
        self.assertEqual(CFG["arms"]["SK"]["ref"], "eval/speckit-baseline")
        self.assertTrue(CFG["arms"]["SK"]["spec_kit"])
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
    def test_twelve_pairs_interleaved(self):
        pairs = run.plan_pairs(CFG)
        self.assertEqual(len(pairs), 12)
        names = [p["name"] for p in pairs]
        self.assertEqual(names[:4], ["SK-S1-r1", "LT-S1-r1", "SK-S1-r2", "LT-S1-r2"])
        self.assertEqual(len(set(names)), 12)
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
        sk = run.build_args(CFG["arms"]["SK"], "out")
        self.assertIn("--spec-kit", sk)
        self.assertEqual(sk[2:6], ["--ref", "eval/speckit-baseline", "--out", "out"])
        self.assertNotIn("--spec-kit", run.build_args(CFG["arms"]["LT"], "out"))


if __name__ == "__main__":
    unittest.main()
