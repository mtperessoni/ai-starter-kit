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


if __name__ == "__main__":
    unittest.main()
