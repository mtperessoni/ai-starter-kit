"""Tests of eval/transcript.py against a real stream-json sample plus synthetic events."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
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


if __name__ == "__main__":
    unittest.main()


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
