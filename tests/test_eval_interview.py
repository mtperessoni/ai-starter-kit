"""I8: interview metrics from a transcript (user_touchpoints, repeated_topics, post_prd_reversals, sheet_decisions,
docs_gate_reruns, heredoc_commands, stuck_minutes, orphans_at_wave_end, questions_after_plan, agents_over_150k,
interview_to_code_tokens), the context budget check, the S12 scenario and the phase-2 prompt."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import interview_metrics as im  # noqa: E402
import transcript  # noqa: E402

_n = [0]


def ts(sec):
    return f"2026-10-09T10:{sec // 60:02d}:{sec % 60:02d}Z"


def asst(blocks, parent=None, sec=0):
    _n[0] += 1
    return {"type": "assistant", "parent_tool_use_id": parent, "timestamp": ts(sec),
            "message": {"id": f"m{_n[0]}", "model": "x", "content": blocks,
                        "usage": {"input_tokens": 1, "output_tokens": 1}}}


def use(tid, name, **inp):
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


def text(t):
    return {"type": "text", "text": t}


def res(tid, out="ok", parent=None, error=False, sec=0):
    b = {"type": "tool_result", "tool_use_id": tid, "content": out}
    if error:
        b["is_error"] = True
    return {"type": "user", "parent_tool_use_id": parent, "timestamp": ts(sec), "message": {"content": [b]}}


def turn_end(sec=0):
    return {"type": "result", "timestamp": ts(sec), "duration_ms": 1000, "result": "x"}


def bash(cmd, parent=None, tid=None, sec=0):
    _n[0] += 1
    return asst([use(tid or f"b{_n[0]}", "Bash", command=cmd)], parent, sec)


def ask(q, tid=None):
    _n[0] += 1
    return asst([use(tid or f"q{_n[0]}", "AskUserQuestion", questions=[{"question": q}])])


def spawn(tid, subagent_type, desc="x", sec=0):
    return asst([use(tid, "Agent", subagent_type=subagent_type, description=desc, prompt="p")], None, sec)


class TouchpointsTest(unittest.TestCase):
    def test_turn_ends_and_questions_before_first_code_commit(self):
        ev = [ask("Which timeout?"), turn_end(), bash("git commit -m 'docs(prd): rules'"),
              turn_end(), bash("git commit -m 'feat(x): code'"), ask("late?"), turn_end()]
        self.assertEqual(im.analyze(ev)["user_touchpoints"], 3)

    def test_no_commit_counts_all(self):
        self.assertEqual(im.analyze([turn_end(), turn_end()])["user_touchpoints"], 2)


class RepeatedTopicsTest(unittest.TestCase):
    def test_similar_question_is_repeated(self):
        ev = [ask("Should the minimum order be compared before discounts or after discounts?"),
              ask("Is the minimum order compared before discounts, or after the discounts?"),
              ask("Which rollback strategy do you prefer for the deploy?")]
        self.assertEqual(im.analyze(ev)["repeated_topics"], 1)

    def test_distinct_questions(self):
        ev = [ask("Which timeout applies to payments?"), ask("Who is notified when an order is refused?")]
        self.assertEqual(im.analyze(ev)["repeated_topics"], 0)

    def test_question_lines_in_main_text(self):
        ev = [asst([text("Do you want the retry to reuse the same payment timeout value?")]),
              asst([text("Should the retry reuse the same payment timeout value, yes or no?")])]
        self.assertEqual(im.analyze(ev)["repeated_topics"], 1)


class ReversalsTest(unittest.TestCase):
    def edit(self, path, old, new):
        _n[0] += 1
        return asst([use(f"e{_n[0]}", "Edit", file_path=path, old_string=old, new_string=new)])

    def test_prd_rule_edit_after_prd_commit(self):
        ev = [bash("git commit -m 'docs(prd): checkout rules'"),
              self.edit("/p/docs/prd/product/04-checkout.md", "| CHK-02 | waits 20 s |", "| CHK-02 | waits 30 s |"),
              self.edit("/p/docs/prd/CHANGELOG.md", "a", "b"), self.edit("/p/src/a.py", "CHK-02", "CHK-03")]
        self.assertEqual(im.analyze(ev)["post_prd_reversals"], 1)

    def test_edit_before_prd_commit_is_free(self):
        ev = [self.edit("/p/docs/prd/product/04-checkout.md", "| CHK-02 | a |", "| CHK-02 | b |"),
              bash("git commit -m 'docs(prd): checkout rules'")]
        self.assertEqual(im.analyze(ev)["post_prd_reversals"], 0)

    def test_none_without_a_prd_commit(self):
        self.assertIsNone(im.analyze([turn_end()])["post_prd_reversals"])


SHEET = """# change
## Decisions (answer by number)
**1. First** · rule A-01
- A) x (Recommended)
**2. Second** · mechanism
- A) y (Recommended)
## How to answer
`ok`
"""


class SheetTest(unittest.TestCase):
    def test_sheet_decisions(self):
        self.assertEqual(im.sheet_decisions(SHEET), 2)
        self.assertEqual(im.analyze([], sheet_text=SHEET)["sheet_decisions"], 2)

    def test_no_sheet_is_none(self):
        self.assertIsNone(im.analyze([])["sheet_decisions"])


class GateAndHeredocTest(unittest.TestCase):
    def test_docs_gate_reruns_after_failure_before_first_executor(self):
        g = "python .claude/skills/prd-flow/scripts/gate.py --rules s1"
        ev = [bash(g, "d1", tid="g1"), res("g1", "ERROR R01", "d1", error=True),
              bash(g, "d1", tid="g2"), res("g2", "ERROR R02", "d1", error=True),
              bash(g, "d1", tid="g3"), res("g3", "ok", "d1"),
              spawn("x1", "prd-flow-executor"), bash(g, "e1", tid="g4"), res("g4", "ERROR", "e1", error=True),
              bash(g, "e1", tid="g5")]
        self.assertEqual(im.analyze(ev)["docs_gate_reruns"], 2)

    def test_heredoc_commands_any_agent(self):
        ev = [bash("cat > a.md <<'EOF'\nx\nEOF"), bash("python - <<'EOF'\nprint(1)\nEOF", "a1"),
              bash("python -\n", "a1"), bash("git status")]
        self.assertEqual(im.analyze(ev)["heredoc_commands"], 3)


class StuckAndOrphansTest(unittest.TestCase):
    def test_stuck_minutes_alive_minus_tool_time(self):
        ev = [spawn("a1", "prd-flow-executor", sec=0),
              bash("sleep 1", "a1", tid="t1", sec=0), res("t1", "ok", "a1", sec=60),
              asst([text("thinking")], "a1", sec=600)]
        self.assertAlmostEqual(im.analyze(ev)["stuck_minutes"], 9.0, places=3)

    def test_stuck_none_without_timestamps_is_zero(self):
        self.assertEqual(im.analyze([turn_end()])["stuck_minutes"], 0.0)

    def test_orphans_from_reap_output(self):
        ev = [bash("scripts/gates.sh reap", tid="r1"), res("r1", "reaped: 2\nleft: 0"),
              bash("scripts/gates.sh reap", tid="r2"), res("r2", "reaped: 1\nleft: 0")]
        self.assertEqual(im.analyze(ev)["orphans_at_wave_end"], 3)

    def test_orphans_from_telemetry_and_null(self):
        tel = [{"ev": "agent_stuck", "agent": "a1", "reason": "alive"},
               {"ev": "agent_stuck", "agent": "a1", "reason": "idle"}, {"ev": "x", "agent": "a2"}]
        self.assertEqual(im.analyze([], telemetry=tel)["orphans_at_wave_end"], 1)
        self.assertIsNone(im.analyze([])["orphans_at_wave_end"])


class QuestionsAfterPlanTest(unittest.TestCase):
    def test_questions_after_first_executor(self):
        ev = [ask("before?"), spawn("x1", "prd-flow-executor"), ask("after one?"),
              asst([text("Is the cutoff 5 or 6 for the pain score?")]), ask("after two?")]
        self.assertEqual(im.analyze(ev)["questions_after_plan"], 3)

    def test_none_without_executor(self):
        self.assertEqual(im.analyze([ask("q?")])["questions_after_plan"], 0)


def row(kind, desc, tokens):
    return {"type": kind, "description": desc, "tokens": tokens}


class BudgetTest(unittest.TestCase):
    def test_violations(self):
        detail = [row("prd-flow-surveyor", "survey", 70000), row("prd-flow-docs", "docs apply", 90000),
                  row("prd-flow-docs", "docs adjust", 85000), row("prd-flow-executor", "T01", 160000),
                  row("prd-flow-surveyor", "survey", 50000)]
        v = im.budget_violations(detail)
        self.assertEqual(len(v), 3)
        self.assertTrue(any("surveyor" in x and "60000" in x for x in v))
        self.assertTrue(any("docs" in x and "80000" in x for x in v))
        self.assertTrue(any("150000" in x for x in v))

    def test_over_150k_and_ratio(self):
        detail = [row("prd-flow-surveyor", "s", 100000), row("prd-flow-docs", "docs apply", 50000),
                  row("prd-flow-executor", "T01", 300000), row("prd-flow-executor", "T02", 100000)]
        m = im.detail_metrics(detail)
        self.assertEqual(m["agents_over_150k"], 1)
        self.assertAlmostEqual(m["interview_to_code_tokens"], 0.375)
        self.assertEqual(m["budget_violations"], [x for x in im.budget_violations(detail)])

    def test_ratio_none_without_executor(self):
        self.assertIsNone(im.detail_metrics([row("prd-flow-surveyor", "s", 10)])["interview_to_code_tokens"])


class WiringTest(unittest.TestCase):
    def test_summarize_carries_the_fields(self):
        import tempfile
        ev = [ask("Which timeout?"), turn_end(), bash("git commit -m 'feat: x'"),
              {"type": "result", "subtype": "success", "total_cost_usd": 0.1, "duration_ms": 5, "num_turns": 1}]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.jsonl"
            p.write_text("\n".join(json.dumps(e) for e in ev), encoding="utf-8")
            s = transcript.summarize(str(p))
        for k in im.FIELDS:
            self.assertIn(k, s)
        self.assertEqual(s["user_touchpoints"], 2)


class ScenarioTest(unittest.TestCase):
    S12 = ROOT / "eval" / "scenarios" / "S12"

    def test_files_and_expected(self):
        for f in ("request.md", "decisions.md", "expected.json"):
            self.assertTrue((self.S12 / f).is_file(), f)
        exp = json.loads((self.S12 / "expected.json").read_text(encoding="utf-8"))
        self.assertEqual(exp["case"], "C5")
        self.assertEqual(exp["follow_up_sheets"], 1)
        self.assertTrue(exp["gap_topic"])
        self.assertTrue(exp["prd_facts"])

    def test_decisions_answer_by_number_with_one_ambiguity(self):
        t = (self.S12 / "decisions.md").read_text(encoding="utf-8")
        self.assertRegex(t, r"(?m)^ok$")
        self.assertRegex(t, r"(?m)^A\d: ")
        self.assertRegex(t, r"(?m)^scope: ")
        self.assertRegex(t, r"(?i)not sure")
        self.assertNotIn("—", t)

    def test_arms_file_runs_s12(self):
        cfg = json.loads((ROOT / "eval" / "arms-sheet.json").read_text(encoding="utf-8"))
        self.assertIn("S12", cfg["scenarios"])

    def test_phase2_prompt_uses_sheet_syntax(self):
        t = (ROOT / "eval" / "prompt-phase2.md").read_text(encoding="utf-8")
        for token in ("sheet.md", "`ok`", "`1B`", "`A2: ...`", "{decisions}"):
            self.assertIn(token, t)


class DocsTest(unittest.TestCase):
    def test_metrics_doc_lists_every_field(self):
        t = (ROOT / "eval" / "METRICS.md").read_text(encoding="utf-8")
        for k in im.FIELDS:
            self.assertIn(f"`{k}`", t)
        self.assertIn("budget_violations", t)


if __name__ == "__main__":
    unittest.main()
