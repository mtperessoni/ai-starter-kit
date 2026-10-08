"""Audit fixes of the chief round: hard gates reach rounds.py, runner wall in the scorecard, last result cost, task waves."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import adoption  # noqa: E402
import agents_report  # noqa: E402
import grade_metrics  # noqa: E402
import protocol  # noqa: E402
import rounds  # noqa: E402
import six  # noqa: E402

_n = [0]


def asst(blocks, parent=None):
    _n[0] += 1
    return {"type": "assistant", "parent_tool_use_id": parent, "cwd": "/p",
            "message": {"id": f"m{_n[0]}", "model": "claude-sonnet-4", "content": blocks,
                        "usage": {"input_tokens": 1000, "output_tokens": 100,
                                  "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}}


def use(tid, name, **inp):
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


def res(tid, text="ok"):
    return {"type": "user", "parent_tool_use_id": None,
            "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "content": text}]}}


def spawn(tid, kind, desc, prompt="go"):
    return asst([use(tid, "Agent", subagent_type=f"prd-flow-{kind}", description=desc, prompt=prompt)])


def write(path, events):
    Path(path).write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")


class ChiefFieldsFlowTest(unittest.TestCase):
    def test_flow_keys_carry_the_chief_fields(self):
        for k in ("chief_violations", "return_compliance", "surveyor_first", "main_violations"):
            self.assertIn(k, six.FLOW_KEYS)
            self.assertIn(k, grade_metrics.efficiency(None))

    def test_rounds_fills_the_hard_gates_from_the_transcript(self):
        d = tempfile.TemporaryDirectory()
        write(Path(d.name) / "FLOW-S5-r1.jsonl", [
            spawn("s", "surveyor", "Survey"), res("s", "no fields here"),
            asst([use("b", "Bash", command="ls")])])
        (Path(d.name) / "FLOW-S5-r1.metrics.json").write_text(
            json.dumps({"status": "ok", "hidden_passed": 1, "hidden_total": 1}), encoding="utf-8")
        run = rounds.load_column(d.name, "FLOW")["S5"][0]
        self.assertEqual(run["chief_violations"], 1)
        self.assertEqual(run["return_compliance"], 0.0)
        self.assertIs(run["surveyor_first"], True)
        gates = {g[0]: g[1] for g in adoption.hard_gates({"S5": [run]})}
        self.assertFalse(gates["Protocol: chief_violations 0 (hard gate)"])
        self.assertFalse(gates["Protocol: return_compliance 1.0 (hard gate)"])

    def test_directions(self):
        self.assertEqual(six.DIRECTION["chief_violations"], six.LOWER)
        self.assertEqual(six.DIRECTION["return_compliance"], six.HIGHER)


class RunnerWallTest(unittest.TestCase):
    def test_scorecard_uses_runner_wall_and_keeps_wall_min_secondary(self):
        self.assertEqual(six.METRICS["M3"][1][0], "runner_wall_min")
        self.assertIn("wall_min", six.METRICS["M3"][1])
        self.assertEqual(six.METRICS["M4"][1][0], "runner_wall_min")
        self.assertEqual(six.DIRECTION["runner_wall_min"], six.LOWER)
        self.assertIn("runner_wall_min", six.ADDITIVE)

    def test_adoption_rule_judges_runner_wall(self):
        base = {"S5": [{"runner_wall_min": 10.0, "wall_min": 5.0, "cost_per_accept": 1.0}]}
        cand = {"S5": [{"runner_wall_min": 20.0, "wall_min": 5.0, "cost_per_accept": 1.0}]}
        rules = {r[0]: r[1] for r in adoption.rules(base, cand)}
        self.assertFalse(rules["S5 runner_wall_min median within +10%"])
        self.assertNotIn("S5 wall_min median within +10%", rules)

    def test_wall_min_row_is_named_for_what_it_is(self):
        self.assertIn("active", six.LABELS["wall_min"])


class LastResultCostTest(unittest.TestCase):
    def test_cumulative_results_count_once(self):
        d = tempfile.TemporaryDirectory()
        usage = {"claude-sonnet-4": {"costUSD": 1.5}}
        ev = [asst([use("x", "Bash", command="ls")]),
              {"type": "result", "duration_ms": 1000, "modelUsage": usage},
              {"type": "result", "duration_ms": 1000, "modelUsage": usage},
              {"type": "result", "duration_ms": 1000, "modelUsage": usage}]
        write(Path(d.name) / "FLOW-S5-r1.jsonl", ev)
        self.assertAlmostEqual(agents_report.report_runs(d.name)[0]["totals"]["cost"], 1.5)

    def test_phases_add(self):
        d = tempfile.TemporaryDirectory()
        usage = {"claude-sonnet-4": {"costUSD": 1.0}}
        for name in ("FLOW-S5-r1.jsonl", "FLOW-S5-r1.p2.jsonl"):
            write(Path(d.name) / name, [asst([use("x", "Bash", command="ls")]),
                                        {"type": "result", "duration_ms": 1, "modelUsage": usage},
                                        {"type": "result", "duration_ms": 1, "modelUsage": usage}])
        self.assertAlmostEqual(agents_report.report_runs(d.name)[0]["totals"]["cost"], 2.0)


class TaskWavesTest(unittest.TestCase):
    def test_close_dispatches_are_not_waves(self):
        ev = [spawn("e1", "executor", "Execute T01: fee", "T01"), res("e1"),
              spawn("r1", "reviewer", "Review Wave 1"), res("r1"),
              spawn("c1", "executor", "Executor close: promote and archive"), res("c1"),
              spawn("c2", "executor", "Run compare gate for slug"), res("c2")]
        a = protocol.analyze(ev)
        self.assertEqual((a["waves"], a["wave_widths"]), (1, [1]))


class FinalEvalFixesTest(unittest.TestCase):
    PLAN = "## Plan\nWAVE 1: T01\nWAVE 2: T02\nReview: per wave\n"

    def test_plan_written_through_bash_counts(self):
        for cmd in (f"cat > changes/001-x/state.md <<'EOF'\n{self.PLAN}EOF",
                    f"printf '%s' '{self.PLAN}' >> .claude/prd-flow/state/x/state.md"):
            a = protocol.analyze([asst([use("B", "Bash", command=cmd)])], {})
            self.assertEqual(a["review_coverage"], 0.0, cmd)

    def test_no_plan_is_still_none(self):
        a = protocol.analyze([asst([use("B", "Bash", command="ls")])], {})
        self.assertIsNone(a["review_coverage"])

    def test_closed_by_gates_close_or_executor_close(self):
        a = protocol.analyze([asst([use("B", "Bash", command="scripts/gates.sh close x")])], {})
        self.assertTrue(a["closed"])
        a = protocol.analyze([asst([use("A", "Agent", subagent_type="prd-flow-executor",
                                        description="Close the change", prompt="close")])], {})
        self.assertTrue(a["closed"])

    def test_never_closed_is_false_and_carries_across_phases(self):
        carry = {}
        a = protocol.analyze([asst([use("B", "Bash", command="ls")])], carry)
        self.assertFalse(a["closed"])
        protocol.analyze([asst([use("B", "Bash", command="scripts/gates.sh close x")])], carry)
        a = protocol.analyze([asst([use("B", "Bash", command="ls")])], carry)
        self.assertTrue(a["closed"])

    def test_closed_false_fails_hard_gate_in_rounds(self):
        gates = adoption.hard_gates({"S8": [{"closed": False}, {"closed": True}]})
        g = [x for x in gates if x[0].startswith("Protocol: closed")][0]
        self.assertFalse(g[1])
        self.assertIn("closed", [f for _, fs in six.METRICS.values() for f in fs])

    def test_phase2_budget_gives_at_least_five_dollars(self):
        import json as _j
        for name in ("arms-min.json", "arms-short.json"):
            cfg = _j.loads((ROOT / "eval" / name).read_text(encoding="utf-8"))
            import run
            share = cfg.get("phase2_share", 0.3)
            b2 = run.split_budget(cfg["scenarios"]["S8"]["budget_usd"], share)[1]
            self.assertGreaterEqual(b2, 5, name)
        self.assertEqual(run.split_budget(10), (7.0, 3.0))


if __name__ == "__main__":
    unittest.main()
