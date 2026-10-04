"""Tests of eval/report.py: every branch of the decision rule on synthetic metrics."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "eval"
sys.path.insert(0, str(EVAL))
import report  # noqa: E402


def run(**kw):
    base = {"accept": 1.0, "suite_green": True, "gate_ok": True, "completed": True,
            "prd_fidelity": 0.9, "protocol_adherence": 1.0, "tokens_total": 1000.0,
            "cost_usd": 10.0, "wall_min": 20.0, "turns": 50, "tool_errors": 4,
            "plan_drift": 0.2, "traceability": 1.0, "single_source": 2}
    return {**base, **kw}


def data(lt=None, sk=None, scenarios=("S1", "S2")):
    return {"LT": {s: [lt or run()] for s in scenarios}, "SK": {s: [sk or run()] for s in scenarios}}


def gate(res, prefix):
    return next(g for g in res["gates"] if g["rule"].startswith(prefix))


class GateTest(unittest.TestCase):
    def test_all_hold(self):
        res = report.evaluate(data())
        self.assertTrue(res["gates_ok"])
        self.assertTrue(res["adopt"])

    def test_q1_accept_lower_fails(self):
        self.assertFalse(gate(report.evaluate(data(lt=run(accept=0.8))), "Q1")["ok"])
        self.assertTrue(gate(report.evaluate(data(sk=run(accept=0.8))), "Q1")["ok"])

    def test_q2_q3_q4_need_every_lt_run(self):
        for key, label in (("suite_green", "Q2"), ("gate_ok", "Q3"), ("completed", "Q4")):
            d = data()
            d["LT"]["S2"] = [run(), run(**{key: False})]
            self.assertFalse(gate(report.evaluate(d), label)["ok"], label)
            d["LT"]["S2"] = [run(), run(**{key: None})]
            self.assertFalse(gate(report.evaluate(d), label)["ok"], label)

    def test_f1_within_slack_passes_beyond_fails(self):
        self.assertTrue(gate(report.evaluate(data(lt=run(prd_fidelity=0.85))), "F1")["ok"])
        self.assertFalse(gate(report.evaluate(data(lt=run(prd_fidelity=0.8))), "F1")["ok"])
        self.assertFalse(gate(report.evaluate(data(lt=run(prd_fidelity=None))), "F1")["ok"])

    def test_r4_must_be_one(self):
        res = report.evaluate(data(lt=run(protocol_adherence=0.75)))
        self.assertFalse(gate(res, "R4")["ok"])
        self.assertFalse(res["adopt"])

    def test_no_lt_runs_fails_gates(self):
        res = report.evaluate({"SK": {"S1": [run()]}})
        self.assertFalse(res["gates_ok"])
        self.assertFalse(res["adopt"])


class ScorecardTest(unittest.TestCase):
    def cell(self, lt, sk, key="cost_usd"):
        res = report.evaluate(data(lt=run(**{key: lt}), sk=run(**{key: sk})))
        return res["scorecard"]["S1"][key]

    def test_win_loss_tie_by_band(self):
        self.assertEqual(self.cell(8.0, 10.0)["verdict"], "win")
        self.assertEqual(self.cell(12.0, 10.0)["verdict"], "loss")
        self.assertEqual(self.cell(10.9, 10.0)["verdict"], "tie")
        self.assertEqual(self.cell(9.1, 10.0)["verdict"], "tie")

    def test_direction_higher_is_better(self):
        self.assertEqual(self.cell(1.0, 0.5, "traceability")["verdict"], "win")
        self.assertEqual(self.cell(0.5, 1.0, "traceability")["verdict"], "loss")

    def test_band_widens_with_spread_inside_an_arm(self):
        d = data()
        d["SK"]["S1"] = [run(cost_usd=10.0), run(cost_usd=16.0)]  # median 13, spread 6
        d["LT"]["S1"] = [run(cost_usd=8.0)]  # 5 below the median: inside the spread
        cell = report.evaluate(d)["scorecard"]["S1"]["cost_usd"]
        self.assertEqual(cell["band"], 6.0)
        self.assertEqual(cell["verdict"], "tie")

    def test_median_of_reps(self):
        d = data()
        d["LT"]["S1"] = [run(cost_usd=5.0), run(cost_usd=6.0), run(cost_usd=100.0)]
        self.assertEqual(report.evaluate(d)["scorecard"]["S1"]["cost_usd"]["lt"], 6.0)

    def test_missing_value_is_undecided(self):
        self.assertIsNone(self.cell(None, 10.0)["verdict"])

    def test_zero_baseline_does_not_divide(self):
        self.assertEqual(self.cell(0, 0, "tool_errors")["verdict"], "tie")
        self.assertEqual(self.cell(3, 0, "tool_errors")["verdict"], "loss")


class AdoptionTest(unittest.TestCase):
    def test_slow_cost_on_s1_blocks(self):
        res = report.evaluate(data(lt=run(cost_usd=15.0)))
        self.assertTrue(res["gates_ok"])
        self.assertFalse(res["speed_ok"])
        self.assertFalse(res["adopt"])
        self.assertIn("cost_usd", {w["metric"] for w in res["work_list"]})

    def test_speed_loss_only_on_s3_does_not_block_s1_s2_rule(self):
        d = data(scenarios=("S1", "S2", "S3"))
        d["LT"]["S3"] = [run(wall_min=40.0)]
        res = report.evaluate(d)
        self.assertTrue(res["speed_ok"])
        self.assertEqual(res["tally"]["efficiency"]["loss"], 1)
        self.assertFalse(res["groups_ok"])
        self.assertFalse(res["adopt"])

    def test_wins_offset_losses_within_a_group(self):
        d = data(lt=run(turns=40, tool_errors=9), sk=run(turns=50, tool_errors=4))
        d["LT"]["S1"] = [run(turns=40, tool_errors=9)]
        res = report.evaluate(d)
        self.assertEqual(res["tally"]["errors"]["loss"], 2)
        self.assertFalse(res["groups_ok"])
        d2 = data(lt=run(tool_errors=9, plan_drift=0.0), sk=run(tool_errors=4))
        res2 = report.evaluate(d2)
        self.assertTrue(res2["tally"]["fidelity"]["win"] >= 1)
        self.assertTrue(res2["groups_ok"] is False)  # errors group still has losses over wins

    def test_equal_runs_adopt_with_ties(self):
        res = report.evaluate(data())
        self.assertTrue(res["groups_ok"])
        self.assertEqual(res["work_list"], [])

    def test_missing_s2_blocks_adoption(self):
        res = report.evaluate(data(scenarios=("S1",)))
        self.assertFalse(res["speed_ok"])
        self.assertFalse(res["adopt"])


class FileTest(unittest.TestCase):
    def test_load_and_write_tolerate_missing_runs(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for arm in ("LT", "SK"):
                for sc, n in (("S1", 2), ("S2", 1)):
                    for r in range(1, n + 1):
                        (d / f"{arm}-{sc}-r{r}.metrics.json").write_text(json.dumps(run()))
            (d / "LT-S3-r1.metrics.json").write_text("{not json")
            (d / "other.metrics.json").write_text("{}")
            out = report.write_report(d)
            text = out.read_text(encoding="utf-8")
            payload = json.loads((d / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["runs"]["LT.S1"], {"found": 2, "expected": 2, "missing": 0})
        self.assertEqual(payload["runs"]["LT.S2"]["missing"], 1)
        self.assertEqual(payload["runs"]["SK.S3"]["missing"], 1)
        self.assertIn("run(s) are missing", text)
        self.assertIn("## Hard gates", text)
        self.assertIn("## Scorecard S1", text)
        self.assertIn("LT is adopted", text)
        self.assertEqual(payload["medians"]["S1"]["LT"]["cost_usd"], 10.0)

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as d:
            text = report.write_report(d).read_text(encoding="utf-8")
        self.assertIn("LT is not adopted", text)


if __name__ == "__main__":
    unittest.main()
