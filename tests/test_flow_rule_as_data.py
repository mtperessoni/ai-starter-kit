"""Rule as data (plan-rule-as-data S1, S2, S5, S7, S8, S10): the flow text.

A rule change of size S or M lands its approved rows in the PRD in the commit of
the code that implements them; the commit body is the record; no docs agent,
Planned TRD section, CHANGELOG append or promote step exists for S and M.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "kit" / ".claude" / "skills" / "prd-flow"
AGENTS = ROOT / "kit" / ".claude" / "agents"


def text(path):
    return path.read_text(encoding="utf-8")


def flow_files():
    files = [SKILL / "SKILL.md", SKILL / "repo.md"]
    files += sorted((SKILL / "reference").glob("*.md"))
    files += sorted(AGENTS.glob("prd-flow-*.md"))
    return files


class RuleAsDataTest(unittest.TestCase):
    def test_no_planned_marker_or_section_is_instructed(self):
        for p in flow_files():
            t = text(p)
            self.assertNotIn("## Planned", t, p.name)
            self.assertNotIn("pending code)*", t, p.name)
            self.assertNotIn("TP01", t, p.name)

    def test_no_changelog_append(self):
        for p in flow_files():
            for line in text(p).splitlines():
                low = line.lower()
                if "changelog" in low:
                    self.assertTrue(
                        "frozen" in low or "never" in low,
                        f"{p.name}: {line.strip()[:120]}",
                    )

    def test_promote_only_for_size_l(self):
        for p in flow_files():
            for line in text(p).splitlines():
                if re.search(r"promot", line, re.I):
                    self.assertTrue(
                        re.search(r"size L|frozen|\bL\b", line),
                        f"{p.name}: {line.strip()[:120]}",
                    )

    def test_no_docs_apply_dispatch(self):
        self.assertNotIn("apply", text(AGENTS / "prd-flow-docs.md"))
        self.assertNotIn("apply", text(SKILL / "reference" / "dispatch.md"))
        self.assertNotIn("apply", text(SKILL / "reference" / "write.md").lower().replace("applies", ""))
        skill = text(SKILL / "SKILL.md")
        self.assertNotIn("apply", skill.lower().replace("applies", ""))

    def test_executor_commit_body_is_the_record(self):
        ex = text(AGENTS / "prd-flow-executor.md") + text(SKILL / "reference" / "run.md")
        for token in ("Decided:", "(rejected:", "(assumed)", "--history", "Rules:"):
            self.assertIn(token, ex, token)
        for token in ("Red:", "Request:", "Assumed:", "gate.py --fix", "Self-check", "deliveries/"):
            self.assertNotIn(token, ex, token)
        self.assertIn("never an ID alone", ex)

    def test_executor_writes_rows_with_the_code(self):
        ex = text(AGENTS / "prd-flow-executor.md")
        self.assertIn("Becomes", ex)
        self.assertIn("same commit", ex)
        self.assertNotRegex(ex, r"Grep[^\n]*old value|old value[^\n]*Grep")

    def test_executor_carries_cost_rules(self):
        ex = text(AGENTS / "prd-flow-executor.md")
        self.assertRegex(ex, r"at most 10 lines")
        self.assertRegex(ex, r"never `cat`")
        self.assertRegex(ex, r"8 Edits")
        self.assertNotIn("vitest", ex)
        self.assertIn("scripts/gates.sh one", ex)
        self.assertRegex(ex, r"never reread")

    def test_dispatch_names_executor_for_implementation(self):
        d = text(SKILL / "reference" / "dispatch.md")
        self.assertRegex(d, r"[Ii]mplementation[^\n]*prd-flow-executor[^\n]*never `general-purpose`")

    def test_surveyor_cost(self):
        s = text(AGENTS / "prd-flow-surveyor.md")
        self.assertNotRegex(s, r"base lint")
        self.assertNotIn("gates.sh setup", s)
        self.assertNotIn("prd-sweep", s)
        self.assertNotIn("sweep.md", s)
        sheet = text(SKILL / "reference" / "sheet.md")
        self.assertRegex(sheet, r"exact row text")

    def test_trd_names_symbols_never_values(self):
        w = text(SKILL / "reference" / "write.md")
        self.assertRegex(w, r"never a rule value")
        self.assertRegex(w, r"open `changes/` folder")

    def test_size_l_keeps_plan_and_decisions(self):
        w = text(SKILL / "reference" / "write.md")
        self.assertIn("decisions.md", w)
        self.assertIn("plan.md", w)
        self.assertRegex(w, r"never in a docs-only commit")


if __name__ == "__main__":
    unittest.main()
