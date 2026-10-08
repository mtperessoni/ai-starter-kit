"""Tests of eval/rounds.py: the eight metrics recomputed offline from result folders."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "eval"
sys.path.insert(0, str(EVAL))
import rounds  # noqa: E402


def folder(root, name, runs):
    d = Path(root) / name
    d.mkdir()
    for stem, metrics in runs.items():
        (d / f"{stem}.metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    return d


M = {"tokens_total": 1000, "wall_min": 10.0, "min_per_task": 5.0, "plan_coverage": 0.5,
     "status": "ok", "subagents": 2, "accept": 1.0}


class RoundsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.a = folder(self.tmp.name, "r1", {"GATE-S1-r1": M, "FLOW-S1-r1": M,
                                              "FLOW-S2-r1": {**M, "tokens_total": 3000},
                                              "FLOW-S3-r1": {**M, "status": "rate_limited"}})
        self.b = folder(self.tmp.name, "r2", {"FLOW-S1-r1": {**M, "tokens_total": 500}})

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse_spec_keeps_drive_colon(self):
        self.assertEqual(rounds.parse_spec("C:/x/y:FLOW"), ("C:/x/y", "FLOW"))
        self.assertEqual(rounds.parse_spec("C:/x/y"), ("C:/x/y", None))
        self.assertEqual(rounds.parse_spec("res:GATE"), ("res", "GATE"))

    def test_columns_one_per_folder_arm(self):
        cols = rounds.columns([f"{self.a}:GATE", f"{self.a}:FLOW", f"{self.b}:FLOW"])
        self.assertEqual([c[0] for c in cols], ["r1:GATE", "r1:FLOW", "r2:FLOW"])

    def test_all_arms_when_no_arm_given(self):
        self.assertEqual([c[0] for c in rounds.columns([str(self.a)])], ["r1:FLOW", "r1:GATE"])

    def test_tables_per_metric_with_total_rows(self):
        text = rounds.render([f"{self.a}:FLOW", f"{self.b}:FLOW"])
        for mid in ("M1", "M2", "M3", "M4", "M5", "M6"):
            self.assertIn(f"## {mid} ", text)
        self.assertIn("| r1:FLOW | r2:FLOW |", text)
        self.assertIn("| tokens_total S1 | 1000 | 500 |", text)
        self.assertIn("| tokens_total S2 | 3000 | n/a |", text)
        self.assertIn("| tokens_total total | 4000 | 500 |", text)
        self.assertNotIn("S3", text)

    def test_tasks_derived_from_old_metrics(self):
        runs = rounds.load_column(self.a, "FLOW")
        self.assertEqual(runs["S1"][0]["tasks_planned"], 2)
        self.assertEqual(runs["S1"][0]["tasks_done"], 1)
        self.assertEqual(runs["S1"][0]["tokens_per_task"], 1000.0)

    def test_transcript_fills_new_fields(self):
        t = Path(self.a) / "FLOW-S1-r1.jsonl"
        lines = [
            {"type": "assistant", "timestamp": "2026-10-07T10:00:00Z", "message": {"id": "m", "content": [
                {"type": "tool_use", "id": "A", "name": "Agent", "input": {}}]}},
            {"type": "assistant", "timestamp": "2026-10-07T10:00:00Z", "parent_tool_use_id": "A",
             "message": {"id": "s", "content": []}},
            {"type": "user", "timestamp": "2026-10-07T10:03:00Z", "parent_tool_use_id": "A",
             "message": {"content": []}},
        ]
        t.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
        run = rounds.load_column(self.a, "FLOW")["S1"][0]
        self.assertAlmostEqual(run["agent_min"], 3.0)
        self.assertEqual(run["cold_starts"], 1)

    def test_out_file(self):
        out = Path(self.tmp.name) / "o.md"
        rounds.main([f"{self.a}:FLOW", "--out", str(out)])
        self.assertIn("## M1 ", out.read_text(encoding="utf-8"))


class RepsAndAdoptionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = {"status": "ok", "tasks_planned": 4, "tasks_done": 4, "hidden_passed": 4,
                "hidden_total": 4, "completed": True, "protocol_adherence": 1.0,
                "prd_fidelity": 1.0, "docs_dispatched": True, "rework_commits": 1, "wall_min": 10.0}
        self.base = folder(self.tmp.name, "b", {
            "GATE-S5-r1": {**base, "cost_usd": 4.0, "tokens_main": 1_000_000},
            "GATE-S5-r2": {**base, "cost_usd": 6.0, "tokens_main": 1_000_000}})
        self.good = folder(self.tmp.name, "g", {
            "FLOW-S5-r1": {**base, "cost_usd": 4.5, "tokens_main": 1_050_000},
            "FLOW-S5-r2": {**base, "cost_usd": 5.5, "tokens_main": 1_050_000}})
        self.bad = folder(self.tmp.name, "x", {
            "FLOW-S5-r1": {**base, "cost_usd": 9.0, "tokens_main": 4_000_000, "tasks_done": 1,
                           "docs_dispatched": False}})

    def tearDown(self):
        self.tmp.cleanup()

    def test_reps_are_averaged_with_spread(self):
        text = rounds.render([f"{self.base}:GATE"])
        self.assertIn("| cost_usd S5 | 5 (spread 2) |", text)

    def test_new_groups_and_fields_listed(self):
        text = rounds.render([f"{self.base}:GATE"])
        for h in ("## M7 Output quality", "## M8 Protocol compliance"):
            self.assertIn(h, text)
        for f in ("cost_main_usd", "cache_hit_rate", "output_share", "min_to_docs", "gate_fail_ratio",
                  "rereads", "first_pass_rate", "traceability", "docs_dispatched", "docs_first"):
            self.assertIn(f"| {f} S5 |", text)

    def test_first_pass_rate_derived(self):
        run = rounds.load_column(self.base, "GATE")["S5"][0]
        self.assertAlmostEqual(run["first_pass_rate"], 0.75)

    def test_no_adoption_section_without_baseline(self):
        self.assertNotIn("Adoption (M07)", rounds.render([f"{self.base}:GATE"]))

    def test_adoption_pass(self):
        text = rounds.render([f"{self.base}:GATE", f"{self.good}:FLOW"], f"{self.base}:GATE")
        self.assertIn("## Adoption (M07)", text)
        self.assertIn("Verdict g:FLOW: PASS", text)
        self.assertIn("PASS S5 cost_usd within +10%", text)

    def test_adoption_fail_on_cost_tokens_and_gates(self):
        text = rounds.render([f"{self.base}:GATE", f"{self.bad}:FLOW"], f"{self.base}:GATE")
        self.assertIn("Verdict x:FLOW: FAIL", text)
        self.assertIn("FAIL S5 cost_usd within +10%", text)
        self.assertIn("FAIL tokens_main per run at most 3.5M", text)
        self.assertIn("FAIL M2 not worse (hard gate)", text)
        self.assertIn("FAIL M8 not worse (hard gate)", text)

    def test_missing_data_never_crashes(self):
        d = folder(self.tmp.name, "e", {"FLOW-S1-r1": {"status": "ok"}})
        text = rounds.render([f"{self.base}:GATE", f"{d}:FLOW"], f"{self.base}:GATE")
        self.assertIn("Verdict e:FLOW", text)


if __name__ == "__main__":
    unittest.main()
