"""Tests of eval/transcript.py against a real stream-json sample plus synthetic events."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import protocol  # noqa: E402
import transcript  # noqa: E402

SAMPLE = ROOT / "tests" / "fixtures" / "stream_sample.jsonl"
USAGE = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")


def tmp_file(lines):
    d = tempfile.TemporaryDirectory()
    p = Path(d.name) / "t.jsonl"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return d, p


def assistant_tokens():
    """Per assistant message id: total tokens, and the ids that belong to a subagent."""
    totals, subs = {}, set()
    for line in SAMPLE.read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        if e["type"] == "assistant":
            totals[e["message"]["id"]] = sum(e["message"]["usage"].get(k, 0) for k in USAGE)
            if e.get("parent_tool_use_id"):
                subs.add(e["message"]["id"])
    return totals, subs


class SummarizeTest(unittest.TestCase):
    def setUp(self):
        self.s = transcript.summarize(SAMPLE)

    def test_result_fields(self):
        self.assertAlmostEqual(self.s["cost_usd"], 0.0422578)
        self.assertAlmostEqual(self.s["wall_min"], 5245 / 60000, places=4)
        self.assertEqual(self.s["turns"], 2)
        self.assertFalse(self.s["is_error"])
        self.assertEqual(self.s["subtype"], "success")

    def test_tokens_prefer_model_usage(self):
        self.assertEqual(self.s["input_tokens"], 539)
        self.assertEqual(self.s["output_tokens"], 183)
        self.assertEqual(self.s["cache_read_tokens"], 43778)
        self.assertEqual(self.s["cache_write_tokens"], 18213)
        self.assertEqual(self.s["tokens_total"], 539 + 183 + 43778 + 18213)

    def test_context_peak_main_thread_only(self):
        self.assertEqual(self.s["context_peak"], 8 + 22157 + 9204)

    def test_subagents_and_share(self):
        totals, subs = assistant_tokens()
        self.assertEqual(self.s["subagents"], 1)
        self.assertAlmostEqual(self.s["subagent_token_share"],
                               sum(totals[i] for i in subs) / sum(totals.values()))

    def test_tool_errors_and_skills(self):
        self.assertEqual(self.s["tool_errors"], 1)
        self.assertEqual(self.s["skills"], ["prd-gate", "speckit-plan"])

    def test_started_at(self):
        self.assertIsInstance(self.s["started_at"], float)
        self.assertGreater(self.s["started_at"], 1.7e9)


class RobustnessTest(unittest.TestCase):
    def test_malformed_unknown_and_empty(self):
        d, p = tmp_file(["not json", "[1]", json.dumps({"type": "weird"}), ""])
        with d:
            s = transcript.summarize(p)
        self.assertIsNone(s["cost_usd"])
        self.assertEqual(s["tokens_total"], 0)
        self.assertEqual(s["skills"], [])
        self.assertIsNone(s["subagent_token_share"])
        self.assertIsNone(s["started_at"])
        self.assertEqual(s["tool_errors"], 0)

    def test_fallback_without_result_dedupes_by_message_id(self):
        a = {"type": "assistant", "parent_tool_use_id": None, "message": {"id": "m1", "content": [],
             "usage": {"input_tokens": 1, "output_tokens": 2, "cache_read_input_tokens": 3,
                       "cache_creation_input_tokens": 4}}}
        d, p = tmp_file([json.dumps(a), json.dumps(a)])
        with d:
            s = transcript.summarize(p)
        self.assertEqual(s["tokens_total"], 10)
        self.assertEqual(s["output_tokens"], 2)
        self.assertEqual(s["subagent_token_share"], 0.0)

    def test_missing_file(self):
        self.assertEqual(transcript.summarize(Path("does-not-exist.jsonl"))["tokens_total"], 0)


def asst(mid, blocks, parent=None, usage=None):
    return json.dumps({"type": "assistant", "parent_tool_use_id": parent, "message": {
        "id": mid, "content": blocks,
        "usage": usage or {"input_tokens": 10, "output_tokens": 5}}})


def use(tid, name, **inp):
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


def res(tid, text="", err=False, parent=None, ts=None):
    e = {"type": "user", "parent_tool_use_id": parent, "message": {"content": [
        {"type": "tool_result", "tool_use_id": tid, "content": text, "is_error": err}]}}
    if ts:
        e["timestamp"] = ts
    return json.dumps(e)


class EfficiencyTest(unittest.TestCase):
    def setUp(self):
        lines = [
            asst("m1", [use("b1", "Bash", command="python -m pytest -q"),
                        use("a1", "Agent", subagent_type="general-purpose", description="implement T1")]),
            res("b1", "2 failed, 5 passed in 1s", ts="2026-10-04T10:00:00Z"),
            asst("s1", [use("sb", "Bash", command="ls")], parent="a1"),
            asst("s1", [], parent="a1"),  # same id again, counted once
            res("sb", "boom", err=True, parent="a1"),
            asst("s2", [use("sr", "Read", file_path="x")], parent="a1",
                 usage={"input_tokens": 1, "output_tokens": 1}),
            res("a1", "line1\nline2\nline3"),
            asst("m2", [use("a2", "Agent", subagent_type="code-reviewer", description="review the diff")]),
            asst("t1", [use("r3", "Read", file_path="y")], parent="a2"),
            res("a2", "ok", err=True),
            asst("m3", [{"type": "text", "text": "review: 2/5 done"},
                        use("b2", "Bash", command="bash scripts/gates.sh"),
                        use("b3", "Bash", command="python -m unittest")]),
            res("b2", "all good"),
            res("b3", "Ran 3 tests\nFAILED (failures=1)"),
        ]
        d, p = tmp_file(lines)
        with d:
            self.s = transcript.summarize(p)

    def test_tokens_split_and_dedupe(self):
        self.assertEqual(self.s["tokens_subagents"], 15 + 2 + 15)
        self.assertEqual(self.s["tokens_main"], 15 * 3)

    def test_tool_calls_and_error_rate(self):
        self.assertEqual(self.s["tool_calls"], 8)
        self.assertEqual(self.s["tool_errors"], 2)
        self.assertAlmostEqual(self.s["error_rate"], 2 / 8)

    def test_test_runs(self):
        self.assertEqual(self.s["test_runs"], 3)
        self.assertEqual(self.s["failed_test_runs"], 2)

    def test_review_rounds_from_text(self):
        self.assertEqual(self.s["review_rounds"], 2)

    def test_subagent_detail(self):
        d1, d2 = self.s["subagent_detail"]
        self.assertEqual((d1["type"], d1["description"]), ("general-purpose", "implement T1"))
        self.assertEqual((d1["tokens"], d1["tool_calls"], d1["tool_errors"]), (17, 2, 1))
        self.assertEqual((d1["return_lines"], d1["is_error"]), (3, False))
        self.assertTrue(d2["is_error"])
        self.assertIsInstance(d1["started_at"], float)
        self.assertEqual(self.s["subagent_errors"], 1)
        self.assertEqual(self.s["subagent_tokens_median"], 16)
        self.assertEqual(self.s["subagent_tool_calls_median"], 1.5)

    def test_review_rounds_fallback_counts_reviewer_agents(self):
        d, p = tmp_file([asst("m", [use("a", "Agent", subagent_type="reviewer", description="x"),
                                    use("b", "Agent", description="Review round")])])
        with d:
            self.assertEqual(transcript.summarize(p)["review_rounds"], 2)

    def test_empty_defaults(self):
        d, p = tmp_file([""])
        with d:
            s = transcript.summarize(p)
        self.assertIsNone(s["error_rate"])
        self.assertEqual((s["tool_calls"], s["test_runs"], s["review_rounds"]), (0, 0, 0))
        self.assertEqual(s["subagent_detail"], [])
        self.assertIsNone(s["subagent_tokens_median"])


class AssistantTextTest(unittest.TestCase):
    def test_main_thread_text_blocks_keep_their_time(self):
        a = json.loads(asst("m1", [{"type": "text", "text": "PRC-03 conflicts with the new cap"}]))
        a["timestamp"] = "2026-10-04T10:00:00Z"
        sub = asst("s1", [{"type": "text", "text": "subagent chatter"}], parent="a1")
        d, p = tmp_file([json.dumps(a), sub, asst("m2", [{"type": "text", "text": "no time"}])])
        with d:
            s = transcript.summarize(p)
        texts = s["assistant_texts"]
        self.assertEqual([x["text"] for x in texts], ["PRC-03 conflicts with the new cap", "no time"])
        self.assertIsInstance(texts[0]["t"], float)
        self.assertIsNone(texts[1]["t"])

    def test_empty_transcript_has_no_texts(self):
        d, p = tmp_file([""])
        with d:
            self.assertEqual(transcript.summarize(p)["assistant_texts"], [])


def ev(kind, ts=None, parent=None, mid=None, blocks=(), usage=None):
    e = {"type": kind, "message": {"content": list(blocks)}}
    if ts:
        e["timestamp"] = f"2026-10-07T10:{ts}Z"
    if parent:
        e["parent_tool_use_id"] = parent
    if mid:
        e["message"]["id"] = mid
        e["message"]["usage"] = usage or {"input_tokens": 1}
    return json.dumps(e)


def tool_use(tid, name="Bash", **inp):
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


def tool_result(tid, text, is_error=True):
    return {"type": "tool_result", "tool_use_id": tid, "is_error": is_error, "content": text}


class SixMetricsTest(unittest.TestCase):
    def summary(self):
        lines = [
            ev("assistant", "00:00", mid="m1", blocks=[tool_use("A1", "Agent", description="build")]),
            ev("assistant", "01:00", "A1", "s1", [tool_use("b1", command="python gate.py")]),
            ev("user", "03:00", "A1", blocks=[tool_result("b1", "ERROR Q1 missing")]),
            ev("assistant", "05:00", "A1", "s2", [tool_use("b2", command="ls")]),
            ev("assistant", "06:00", mid="m2", blocks=[tool_use("b3", command="python .claude/skills/x/scripts/gate.py")]),
            ev("user", "06:30", blocks=[tool_result("b3", "python: not found")]),
            ev("assistant", "07:00", mid="m3", blocks=[tool_use("b4", "Read", file_path="x")]),
            ev("user", "07:10", blocks=[tool_result("b4", "File does not exist")]),
            ev("assistant", "07:20", mid="m4", blocks=[tool_use("b5", command="pytest")]),
            ev("user", "07:30", blocks=[tool_result("b5", "Traceback (most recent call last)")]),
            ev("user", "07:40", blocks=[tool_result("b4", "weird failure")]),
            ev("user", "07:50", blocks=[tool_result("b4", "Traceback in a fine read", is_error=False)]),
            json.dumps({"type": "result", "duration_ms": 600000, "is_error": False}),
        ]
        d, p = tmp_file(lines)
        with d:
            return transcript.summarize(p)

    def test_time_split(self):
        s = self.summary()
        self.assertAlmostEqual(s["agent_min"], 4.0)
        self.assertAlmostEqual(s["main_min"], 6.0)
        self.assertEqual(s["cold_starts"], 1)

    def test_error_kinds(self):
        k = self.summary()["error_kinds"]
        self.assertEqual(k, {"gate_check": 1, "environment": 1, "missing_file": 1,
                             "test_failure": 1, "other": 1})

    def test_gate_runs_split_by_parent(self):
        s = self.summary()
        self.assertEqual((s["gate_runs_main"], s["gate_runs_sub"]), (1, 1))

    def test_no_wall_gives_none_main_min(self):
        d, p = tmp_file([ev("assistant", "00:00", mid="m1")])
        with d:
            s = transcript.summarize(p)
        self.assertIsNone(s["main_min"])
        self.assertEqual(s["error_kinds"]["other"], 0)


def raw(e):
    return json.dumps(e)


def result_event(usage):
    return raw({"type": "result", "total_cost_usd": 3.0, "modelUsage": usage})


class OutputQualityFieldsTest(unittest.TestCase):
    def summarize(self, lines):
        d, p = tmp_file(lines)
        with d:
            return transcript.summarize(p)

    def test_cost_split_by_init_model(self):
        s = self.summarize([
            raw({"type": "system", "subtype": "init", "model": "opus"}),
            result_event({"opus": {"costUSD": 2.0, "inputTokens": 10, "outputTokens": 10,
                                   "cacheReadInputTokens": 60, "cacheCreationInputTokens": 20},
                          "haiku": {"costUSD": 0.5, "inputTokens": 0, "outputTokens": 0,
                                    "cacheReadInputTokens": 0, "cacheCreationInputTokens": 0},
                          "sonnet": {"costUSD": 0.25}})])
        self.assertEqual((s["cost_main_usd"], s["cost_subagents_usd"]), (2.0, 0.75))
        self.assertAlmostEqual(s["cache_hit_rate"], 60 / 90)
        self.assertAlmostEqual(s["output_share"], 10 / 100)

    def test_missing_data_is_none(self):
        s = self.summarize([ev("assistant", "00:00", mid="m1")])
        for k in ("cost_main_usd", "cost_subagents_usd", "cache_hit_rate", "output_share",
                  "gate_fail_ratio"):
            self.assertIsNone(s[k])
        self.assertEqual(s["rereads"], 0)
        self.assertFalse(s["docs_dispatched"])

    def test_no_init_model_gives_none_cost_split(self):
        s = self.summarize([result_event({"opus": {"costUSD": 2.0}})])
        self.assertIsNone(s["cost_main_usd"])

    def test_gate_fail_ratio(self):
        def res(tid, text, err=False):
            return ev("user", blocks=[{"type": "tool_result", "tool_use_id": tid, "content": text,
                                       "is_error": err}])
        s = self.summarize([
            ev("assistant", "00:00", mid="a", blocks=[tool_use("g1", command="python gate.py x"),
                                                     tool_use("g2", command="python gate.py y"),
                                                     tool_use("g3", command="python gate.py z"),
                                                     tool_use("b1", command="ls")]),
            res("g1", "ok"), res("g2", "ERROR G1 bad"), res("g3", "boom", True), res("b1", "ERROR x")])
        self.assertAlmostEqual(s["gate_fail_ratio"], 2 / 3)

    def test_rereads_per_context(self):
        rd = lambda i, f: tool_use(i, "Read", file_path=f)
        s = self.summarize([
            ev("assistant", "00:00", mid="a", blocks=[rd("1", "a"), rd("2", "a"), rd("3", "b")]),
            ev("assistant", "00:01", mid="b", parent="S", blocks=[rd("4", "a"), rd("5", "a")]),
            ev("assistant", "00:02", mid="c", parent="T", blocks=[rd("6", "a")])])
        self.assertEqual(s["rereads"], 2)

    def test_docs_dispatched(self):
        agent = lambda **i: ev("assistant", "00:00", mid="a", blocks=[tool_use("A", "Agent", **i)])
        self.assertTrue(self.summarize([agent(description="Run Planner", prompt="x")])["docs_dispatched"])
        self.assertTrue(self.summarize([agent(description="d", prompt="the prd-WRITER task")])["docs_dispatched"])
        self.assertFalse(self.summarize([agent(description="executor", prompt="code")])["docs_dispatched"])


def _ev(kind, ts, parent=None, **kw):
    return {"type": kind, "timestamp": ts, "parent_tool_use_id": parent, **kw}


def _call(mid, ts, blocks, usage=None, parent=None):
    base = {"input_tokens": 1, "cache_read_input_tokens": 100, "cache_creation_input_tokens": 10, "output_tokens": 5}
    return _ev("assistant", ts, parent, message={"id": mid, "usage": usage or base, "content": blocks})


def _use(tid, name, **inp):
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


def _done(ts, tid, text="ok", parent=None):
    return _ev("user", ts, parent, message={"content": [{"type": "tool_result", "tool_use_id": tid, "content": text}]})


def _flow_session():
    first = {"input_tokens": 5, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 40000, "output_tokens": 1}
    return [
        _call("m1", "2026-10-07T10:00:00Z", [_use("S", "Agent", subagent_type="prd-flow-surveyor", prompt="go")], first),
        _done("2026-10-07T10:01:00Z", "S"),
        _call("m2", "2026-10-07T10:01:10Z", [_use("D", "Agent", description="Write docs and plan", prompt="docs")]),
        _done("2026-10-07T10:02:00Z", "D"),
        _call("m3", "2026-10-07T10:02:10Z", [_use("E1", "Agent", subagent_type="prd-flow-executor", prompt="T01 go"),
                                             _use("E2", "Agent", subagent_type="prd-flow-executor", prompt="T02 go")]),
        _call("s1", "2026-10-07T10:02:20Z", [], parent="E1"), _call("s2", "2026-10-07T10:02:20Z", [], parent="E2"),
        _call("s3", "2026-10-07T10:06:20Z", [], parent="E1"), _call("s4", "2026-10-07T10:06:20Z", [], parent="E2"),
        _done("2026-10-07T10:06:30Z", "E1"), _done("2026-10-07T10:06:31Z", "E2"),
        _call("m4", "2026-10-07T10:06:40Z", [_use("E3", "Agent", subagent_type="prd-flow-executor", prompt="T03 go")]),
        _done("2026-10-07T10:08:00Z", "E3"),
        _call("m5", "2026-10-07T10:08:10Z", [_use("R", "Agent", description="Review the wave", prompt="r")]),
        _done("2026-10-07T10:09:00Z", "R"),
    ]


class FlowMetricsTest(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = Path(d.name) / "t.jsonl"
        p.write_text("\n".join(json.dumps(e) for e in _flow_session()) + "\n", encoding="utf-8")
        self.s = transcript.summarize(p)

    def test_dispatch_map_by_type_then_description(self):
        self.assertEqual(self.s["agents_by_role"]["executor"], 3)
        self.assertEqual(self.s["agents_by_role"]["docs"], 1)
        self.assertEqual(self.s["agents_by_role"]["reviewer"], 1)
        self.assertEqual(self.s["dispatch_map"], 1.0)

    def test_waves_and_widths_follow_returns(self):
        self.assertEqual((self.s["waves"], self.s["wave_widths"]), (2, [2, 1]))

    def test_parallel_factor_over_the_execution_phase(self):
        self.assertGreater(self.s["parallel_factor"], 1.0)

    def test_start_context_and_cache_write(self):
        self.assertEqual(self.s["start_context"], 40005)
        self.assertEqual(self.s["main_calls"], 5)
        self.assertEqual(self.s["cache_busts"], 0)
        self.assertEqual(self.s["main_violations"], 0)

    def test_main_violations_count_edits_reads_and_extra_gates(self):
        ev = [_call("a", "2026-10-07T10:00:00Z", [_use("r", "Read", file_path="/p/src/orders/x.py"),
                                                  _use("w", "Edit", file_path="/p/docs/prd/a.md")]),
              _call("b", "2026-10-07T10:00:10Z", [_use("S", "Agent", subagent_type="prd-flow-surveyor", prompt="g")]),
              _call("c", "2026-10-07T10:00:20Z", [_use("g", "Bash", command="python gate.py --final")])]
        self.assertEqual(protocol.analyze(ev)["main_violations"], 3)

    def test_redispatch_of_a_task_card_is_counted(self):
        ev = _flow_session() + [
            _call("m6", "2026-10-07T10:09:10Z", [_use("E4", "Agent", subagent_type="prd-flow-executor", prompt="T03 again")]),
            _done("2026-10-07T10:09:50Z", "E4")]
        self.assertEqual(protocol.analyze(ev)["redispatches"], 1)


if __name__ == "__main__":
    unittest.main()
