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


class InfraFailureTest(unittest.TestCase):
    def test_rate_limited_and_skipped_runs_are_missing_not_losses(self):
        import tempfile
        d = Path(tempfile.mkdtemp())
        (d / "LT-S1-r1.metrics.json").write_text(json.dumps({"status": "ok", "accept": 1.0}), encoding="utf-8")
        (d / "LT-S1-r2.metrics.json").write_text(json.dumps({"status": "rate_limited", "accept": 0.0}),
                                                 encoding="utf-8")
        (d / "SKF-S1-r1.metrics.json").write_text(json.dumps({"status": "skipped_rate_limit"}), encoding="utf-8")
        runs = report.load(d)
        self.assertEqual(len(runs["LT"]["S1"]), 1)
        self.assertNotIn("SKF", runs)

    def test_base_arm_is_configurable(self):
        d = data()
        d["SKF"] = d.pop("SK")
        res = report.evaluate(d, base="SKF")
        self.assertTrue(res["gates_ok"])


class ExpectedRepsTest(unittest.TestCase):
    def test_reps_come_from_the_config(self):
        cfg = {"scenarios": {"L1": {"reps": 2}, "L4": {"reps": 3}}}
        counts = report.run_counts({"LT": {"L1": [{}]}}, "SKU", "LT", report.expected_reps(cfg))
        self.assertEqual(counts["LT.L1"], {"found": 1, "expected": 2, "missing": 1})
        self.assertEqual(counts["SKU.L4"]["expected"], 3)
        self.assertNotIn("LT.S1", counts)

    def test_default_is_the_small_suite_map(self):
        self.assertEqual(report.expected_reps(None), report.EXPECTED_REPS)

    def test_derived_from_files_when_no_config(self):
        d = Path(tempfile.mkdtemp())
        for name in ("LT-L1-r1", "LT-L1-r2", "SKU-L1-r1", "LT-L4-r1"):
            (d / f"{name}.metrics.json").write_text(json.dumps({"status": "ok"}), encoding="utf-8")
        self.assertEqual(report.derive_reps(d), {"L1": 2, "L4": 1})

    def test_write_report_uses_the_config_reps(self):
        d = Path(tempfile.mkdtemp())
        (d / "LT-L1-r1.metrics.json").write_text(json.dumps({"status": "ok", "accept": 1.0}), encoding="utf-8")
        cfg = d / "arms.json"
        cfg.write_text(json.dumps({"scenarios": {"L1": {"reps": 2}}}), encoding="utf-8")
        out = report.write_report(d, "SKU", "LT", config=cfg)
        payload = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(payload["runs"]["LT.L1"]["expected"], 2)
        self.assertNotIn("LT.S1", payload["runs"])


class CategoryTest(unittest.TestCase):
    def test_metrics_are_grouped_by_the_agreed_categories(self):
        self.assertEqual(list(report.GROUPS), ["tokens", "speed", "efficiency", "rework",
                                               "plan_fidelity", "source_fidelity", "errors",
                                               "subagents", "reviews", "code_quality"])
        self.assertEqual(report.GROUPS["code_quality"]["blind_bugs"], "lower")
        self.assertEqual(report.GROUPS["reviews"]["blind_approve"], "higher")
        self.assertEqual(report.GROUPS["errors"]["error_rate"], "lower")
        self.assertEqual(report.GROUPS["rework"], {"rework_commits": "lower", "kit_self_fixes": "lower"})
        self.assertIn("min_to_code", report.GROUPS["speed"])
        self.assertIn("context_peak", report.GROUPS["tokens"])


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
        self.assertEqual(res["tally"]["speed"]["loss"], 1)
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
        self.assertTrue(res2["tally"]["plan_fidelity"]["win"] >= 1)
        self.assertTrue(res2["groups_ok"] is False)  # errors group still has losses over wins

    def test_equal_runs_adopt_with_ties(self):
        res = report.evaluate(data())
        self.assertTrue(res["groups_ok"])
        self.assertEqual(res["work_list"], [])

    def test_missing_s2_blocks_adoption(self):
        res = report.evaluate(data(scenarios=("S1",)))
        self.assertFalse(res["speed_ok"])
        self.assertFalse(res["adopt"])


class AnalysisTest(unittest.TestCase):
    def d3(self):
        return {
            "LT": {"S1": [run(tokens_total=100.0, blind_bugs=0, accept=1.0)],
                   "L1": [run(tokens_total=900.0, blind_bugs=2, accept=0.5)]},
            "SKU": {"S1": [run(tokens_total=200.0, blind_bugs=1, accept=1.0)],
                    "L1": [run(tokens_total=500.0, blind_bugs=0, accept=1.0)]},
            "SKF": {"S1": [run(tokens_total=300.0, blind_bugs=None)],
                    "L1": [run(tokens_total=700.0, blind_bugs=3)]},
        }

    def test_all_arms_medians_ranks_and_sizes(self):
        an = report.analyze(self.d3(), {"S1": "S", "L1": "L"})
        self.assertEqual(list(an), ["X1", "X2", "X3", "X4", "X5", "X6"])
        row = an["X1"]["metrics"]["tokens_total"]
        self.assertEqual(row["all"]["median"], {"LT": 500.0, "SKF": 500.0, "SKU": 350.0})
        self.assertEqual(row["all"]["rank"], {"SKU": 1, "LT": 2, "SKF": 2})
        self.assertEqual(row["S"]["rank"], {"LT": 1, "SKU": 2, "SKF": 3})
        self.assertEqual(row["L"]["median"]["LT"], 900.0)
        self.assertIsNone(row["M"]["median"]["LT"])
        bugs = an["X6"]["metrics"]["blind_bugs"]
        self.assertEqual(bugs["S"]["rank"], {"LT": 1, "SKU": 2})  # SKF has no value
        acc = an["X6"]["metrics"]["accept"]
        self.assertEqual(acc["all"]["rank"]["SKU"], 1)  # higher is better

    def test_descriptive_metric_has_no_rank_and_no_sizes_still_works(self):
        an = report.analyze(self.d3())
        self.assertEqual(an["X2"]["metrics"]["subagents"]["all"]["rank"], {})
        self.assertIsNone(an["X1"]["metrics"]["tokens_total"]["S"]["median"]["LT"])

    def test_every_metric_of_x1_to_x6_is_present(self):
        an = report.analyze(self.d3())
        want = {"X1": ["tokens_total", "tokens_main", "tokens_subagents", "context_peak", "cost_usd"],
                "X2": ["subagents", "subagent_tokens_median", "subagent_tool_calls_median",
                       "subagent_errors", "subagents_wasted", "tasks_per_executor",
                       "subagent_token_share"],
                "X3": ["tool_calls", "tool_errors", "error_rate", "test_runs", "failed_test_runs",
                       "kit_self_fixes"],
                "X4": ["wall_min", "min_to_code", "min_per_task"],
                "X5": ["review_rounds", "review_fix_commits", "blind_findings_total"],
                "X6": ["accept", "suite_green", "blind_bugs", "blind_high", "blind_approve"]}
        for q, keys in want.items():
            for k in keys:
                self.assertIn(k, an[q]["metrics"], k)

    def test_report_section_and_analysis_json(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            cfg = d / "arms.json"
            cfg.write_text(json.dumps({"scenarios_dir": "scn", "scenarios": {
                "S1": {"reps": 1}, "L1": {"reps": 1}}}), encoding="utf-8")
            for sc, size in (("S1", "S"), ("L1", "L")):
                (d / "scn" / sc).mkdir(parents=True)
                (d / "scn" / sc / "expected.json").write_text(json.dumps({"size": size}))
            res = d / "res"
            res.mkdir()
            for arm, scs in self.d3().items():
                for sc, runs in scs.items():
                    (res / f"{arm}-{sc}-r1.metrics.json").write_text(json.dumps(runs[0]))
            text = report.write_report(res, config=cfg).read_text(encoding="utf-8")
            an = json.loads((res / "analysis.json").read_text(encoding="utf-8"))
        self.assertIn("## Efficiency analysis", text)
        self.assertIn("### X6 Code with fewest problems", text)
        self.assertIn("| tokens_total | S | 100 #1 | 300 #3 | 200 #2 |", text)
        self.assertEqual(an["X1"]["metrics"]["tokens_total"]["L"]["median"]["SKU"], 500.0)


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


class SourceOfTruthTest(unittest.TestCase):
    def test_k91_metrics_are_in_the_source_fidelity_group(self):
        g = report.GROUPS["source_fidelity"]
        self.assertEqual((g["conflict_found"], g["gap_recorded"], g["contradiction_left"]),
                         (report.HIGHER, report.HIGHER, report.LOWER))

    def test_scorecard_scores_the_new_metrics(self):
        d = data(lt=run(conflict_found=True, gap_recorded=True, contradiction_left=0),
                 sk=run(conflict_found=False, gap_recorded=False, contradiction_left=2))
        row = report.evaluate(d)["scorecard"]["S1"]
        self.assertEqual(row["conflict_found"]["verdict"], "win")
        self.assertEqual(row["gap_recorded"]["verdict"], "win")
        self.assertEqual(row["contradiction_left"]["verdict"], "win")

    def test_report_names_the_category_and_the_arms(self):
        with tempfile.TemporaryDirectory() as d:
            for arm in ("GATE", "FLOW"):
                (Path(d) / f"{arm}-S5-r1.metrics.json").write_text(
                    json.dumps(run(conflict_found=arm == "FLOW")), encoding="utf-8")
            text = report.write_report(d, "GATE", "FLOW").read_text(encoding="utf-8")
        self.assertIn("Source-of-truth fidelity", text)
        self.assertRegex(text, r"Result: FLOW is (not )?adopted")


if __name__ == "__main__":
    unittest.main()
