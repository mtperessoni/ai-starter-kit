"""C6-07: chief_violations, return_compliance, surveyor_first, agents_report start cost, adoption gates."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import adoption  # noqa: E402
import agents_report  # noqa: E402
import protocol  # noqa: E402
import transcript  # noqa: E402

_n = [0]
GOOD = "Did it.\nStatus: done\nFiles: a.md\nCommit: abc1234\nRoute: none\nNext: dispatch the docs agent"


def asst(blocks, parent=None):
    _n[0] += 1
    return {"type": "assistant", "parent_tool_use_id": parent, "cwd": "/p",
            "message": {"id": f"m{_n[0]}", "model": "x", "content": blocks,
                        "usage": {"input_tokens": 1, "output_tokens": 1, "cache_read_input_tokens": 0,
                                  "cache_creation_input_tokens": 7 + _n[0]}}}


def use(tid, name, **inp):
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


def res(tid, text, parent=None):
    return {"type": "user", "parent_tool_use_id": parent,
            "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "content": text}]}}


def spawn(tid, kind, prompt="go"):
    return asst([use(tid, "Agent", subagent_type=f"prd-flow-{kind}", description=kind, prompt=prompt)])


def chief(*blocks):
    return asst(list(blocks))


class ChiefViolationsTest(unittest.TestCase):
    def count(self, *events):
        return protocol.analyze(list(events))["chief_violations"]

    def test_allowed_tools_are_free(self):
        ev = [spawn("s", "surveyor"), chief(use("q", "AskUserQuestion", questions=[])),
              chief(use("r", "Read", file_path="/p/changes/001-x/state.md")),
              chief(use("w", "Edit", file_path="/p/changes/001-x/state.md")),
              chief(use("rp", "Read", file_path="/p/.claude/skills/prd-flow/repo.md"))]
        self.assertEqual(self.count(*ev), 0)

    def test_bash_is_always_a_violation(self):
        ev = [spawn("s", "surveyor"), chief(use("b", "Bash", command="git status"))]
        self.assertEqual(self.count(*ev), 1)

    def test_other_reads_and_tools_are_violations(self):
        ev = [spawn("s", "surveyor"), chief(use("r", "Read", file_path="/p/changes/001-x/plan.md")),
              chief(use("t", "TodoWrite", todos=[])), chief(use("g", "Grep", pattern="x"))]
        self.assertEqual(self.count(*ev), 3)

    def test_subagent_calls_do_not_count(self):
        ev = [spawn("s", "surveyor"), asst([use("b", "Bash", command="ls")], parent="s")]
        self.assertEqual(self.count(*ev), 0)

    def test_none_without_any_dispatch(self):
        self.assertIsNone(self.count(chief(use("b", "Bash", command="ls"))))

    def test_worker_only_blind_spot_names(self):
        for name in ("dispatch.md", "survey.md", "sheet.md", "write.md", "run.md"):
            a = protocol.analyze([spawn("s", "surveyor"), chief(use("r", "Read", file_path=f"/p/x/{name}"))])
            self.assertEqual(a["worker_only_reads"], 1, name)


class ReturnAndFirstTest(unittest.TestCase):
    def test_compliance_share(self):
        ev = [spawn("a", "surveyor"), res("a", GOOD), spawn("b", "docs"), res("b", "Status: done\nFiles: none"),
              spawn("c", "executor"), res("c", GOOD)]
        a = protocol.analyze(ev)
        self.assertAlmostEqual(a["return_compliance"], 2 / 3)
        self.assertEqual((a["returns_total"], a["returns_ok"]), (3, 2))

    def test_last_result_counts_and_none_without_returns(self):
        self.assertIsNone(protocol.analyze([spawn("a", "surveyor")])["return_compliance"])
        ev = [spawn("a", "surveyor"), res("a", "launched"), res("a", GOOD)]
        self.assertEqual(protocol.analyze(ev)["return_compliance"], 1.0)

    def test_surveyor_first(self):
        self.assertTrue(protocol.analyze([spawn("a", "surveyor"), spawn("b", "docs")])["surveyor_first"])
        self.assertFalse(protocol.analyze([spawn("b", "docs"), spawn("a", "surveyor")])["surveyor_first"])
        self.assertIsNone(protocol.analyze([chief(use("r", "Read", file_path="/p/a"))])["surveyor_first"])

    def test_surveyor_first_carries_across_phases(self):
        carry = {}
        protocol.analyze([spawn("a", "surveyor")], carry)
        self.assertTrue(protocol.analyze([spawn("b", "docs")], carry)["surveyor_first"])

    def test_phases_merge(self):
        d = tempfile.TemporaryDirectory()
        p1, p2 = Path(d.name) / "r.jsonl", Path(d.name) / "r.p2.jsonl"
        w = lambda p, ev: p.write_text("\n".join(json.dumps(e) for e in ev), encoding="utf-8")
        w(p1, [spawn("a", "surveyor"), res("a", GOOD), chief(use("b", "Bash", command="ls"))])
        w(p2, [spawn("b", "docs"), res("b", "bad"), chief(use("c", "Bash", command="ls"))])
        s = transcript.summarize_phases([str(p1), str(p2)])
        self.assertEqual(s["chief_violations"], 2)
        self.assertEqual(s["return_compliance"], 0.5)
        self.assertTrue(s["surveyor_first"])


class AgentsReportTest(unittest.TestCase):
    def test_generic_type_sizes_and_start_write(self):
        d = tempfile.TemporaryDirectory()
        ev = [asst([use("a1", "Agent", subagent_type="general-purpose", description="x", prompt="p" * 50)]),
              asst([use("c", "Read", file_path="/p/a")], parent="a1"), res("a1", "r" * 30)]
        (Path(d.name) / "FLOW-S5-r1.jsonl").write_text("\n".join(json.dumps(e) for e in ev), encoding="utf-8")
        row = [r for r in agents_report.report_runs(d.name)[0]["rows"] if r["agent"] == "a1"][0]
        self.assertEqual((row["role"], row["prompt_chars"], row["return_chars"]), ("general-purpose", 50, 30))
        self.assertGreater(row["start_write"], 0)
        self.assertIn("start_write", agents_report.COLS)


class GatesTest(unittest.TestCase):
    def test_hard_gates_present(self):
        runs = {"FLOW": [{"chief_violations": 1, "return_compliance": 0.5, "surveyor_first": False}]}
        text = {g[0]: g[1] for g in adoption.hard_gates(runs)}
        self.assertFalse(text["Protocol: chief_violations 0 (hard gate)"])
        self.assertFalse(text["Protocol: return_compliance 1.0 (hard gate)"])
        self.assertFalse(text["Protocol: surveyor_first true (hard gate)"])
        ok = {"FLOW": [{"chief_violations": 0, "return_compliance": 1.0, "surveyor_first": True}]}
        self.assertTrue({g[0]: g[1] for g in adoption.hard_gates(ok)}["Protocol: surveyor_first true (hard gate)"])


if __name__ == "__main__":
    unittest.main()
