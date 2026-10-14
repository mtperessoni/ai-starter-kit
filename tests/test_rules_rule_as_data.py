import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "rules" / "06-docs-system.md"
CONSTITUTION = ROOT / "kit" / ".specify" / "memory" / "constitution.md"
D2 = (
    "Rule changes land in the PRD in the same commit as the code that implements "
    "them; the commit body records the request and the decision."
)


def ds_rows(text):
    return {m.group(1): m.group(0) for m in re.finditer(r"^\| (DS\d+) \|.*$", text, re.M)}


class RuleAsDataRules(unittest.TestCase):
    def setUp(self):
        self.text = RULES.read_text(encoding="utf-8")
        self.rows = ds_rows(self.text)

    def test_no_ds_id_deleted(self):
        old = subprocess.run(
            ["git", "show", "61750dd:rules/06-docs-system.md"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True,
        ).stdout
        missing = sorted(set(ds_rows(old)) - set(self.rows))
        self.assertEqual(missing, [])

    def test_ds12_no_changelog_line(self):
        row = self.rows["DS12"]
        self.assertIn("frozen", row)
        self.assertNotIn("On promotion", row)

    def test_ds17_no_planned_section(self):
        self.assertIn("Retired", self.rows["DS17"])
        self.assertNotIn("writes a `## Planned", self.rows["DS17"])

    def test_ds18_no_promote_for_s_and_m(self):
        row = self.rows["DS18"]
        self.assertIn("Retired", row)
        self.assertNotIn("The final task of every plan promotes", row)

    def test_ds09_no_pending_marker_for_new_changes(self):
        self.assertIn("no new change adds", self.rows["DS09"])

    def test_ds24_six_errors_only(self):
        row = self.rows["DS24"]
        self.assertNotIn("without a CHANGELOG entry", row)
        self.assertIn("INDEX", row)

    def test_ds33_covers_all_docs(self):
        self.assertIn("all of `docs/`", self.rows["DS33"])

    def test_constitution_has_d2_sentence(self):
        self.assertIn(D2, CONSTITUTION.read_text(encoding="utf-8"))


WF = ROOT / "rules" / "07-workflow.md"


def wf_row(text, rid):
    return re.search(r"^\| %s \|.*$" % rid, text, re.M).group(0)


class RuleAsDataWorkflowText(unittest.TestCase):
    def test_wf_rows_have_no_old_flow(self):
        text = WF.read_text(encoding="utf-8")
        for rid, bad in {
            "WF37": "with Source `planned`",
            "WF39": "docs/prd/CHANGELOG.md` (collected",
            "WF47": "Promote copies the rows into the CHANGELOG entry",
            "WF48": "the CHANGELOG entry reads",
            "WF59": "of the CHANGELOG entry",
            "WF70": "Size M has no TRD Planned section",
            "WF83": "CHANGELOG history",
            "WF43": "rows of the CHANGELOG entry",
        }.items():
            self.assertNotIn(bad, wf_row(text, rid), rid)

    def test_readme_gate_reads_commit_body(self):
        text = (ROOT / "rules" / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("read from the CHANGELOG entry", text)

    def test_ds07_ds13_new_changes_add_no_marker(self):
        rows = ds_rows(RULES.read_text(encoding="utf-8"))
        self.assertNotIn("has Source `planned`", rows["DS07"])
        self.assertIn("no new change adds", rows["DS07"])
        self.assertIn("no new change adds", rows["DS13"])

    def test_templates_have_no_planned_source(self):
        for name in ("prd-section.md", "change-brief.md"):
            t = (ROOT / "kit" / "docs" / "templates" / name).read_text(encoding="utf-8")
            self.assertNotIn("Source `planned`", t, name)
            self.assertNotIn("| planned |", t, name)


class RuleAsDataRound1Text(unittest.TestCase):
    def rule_row(self, name, rid):
        text = (ROOT / "rules" / name).read_text(encoding="utf-8")
        m = re.search(r"^\| " + rid + r" \|.*$", text, re.M)
        self.assertIsNotNone(m, rid)
        return m.group(0)

    def test_r01_no_docs_apply_in_wf_rows(self):
        for rid in ("WF47", "WF52", "WF67", "WF75"):
            row = self.rule_row("07-workflow.md", rid)
            self.assertNotIn("docs `apply`", row, rid)
            self.assertNotIn('write.md "Apply"', row, rid)

    def test_r02_no_promote_or_changelog_entry_for_s_m(self):
        self.assertNotIn("promotion keeps", self.rule_row("01-context-economy.md", "CE28"))
        self.assertNotIn("docs `apply`", self.rule_row("01-context-economy.md", "CE29"))
        self.assertNotIn("the CHANGELOG entry says", self.rule_row("06-docs-system.md", "DS35"))
        self.assertNotIn("holds superseded wording", self.rule_row("06-docs-system.md", "DS03"))

    def test_r06_wf33_warns_on_existing_markers(self):
        self.assertIn("warns", self.rule_row("07-workflow.md", "WF33"))

    def test_r09_templates_no_changelog_target(self):
        for f in (ROOT / "kit" / "docs" / "templates").glob("change-*.md"):
            self.assertNotIn("to the CHANGELOG", f.read_text(encoding="utf-8"), f.name)

    def test_r10_size_m_has_no_plan_or_decisions(self):
        for path in (CONSTITUTION, ROOT / "kit" / "AGENTS.md"):
            t = path.read_text(encoding="utf-8")
            self.assertNotIn("M may keep a `plan.md`", t, path.name)
            self.assertNotIn("M `plan.md` only", t, path.name)
        for rid in ("WF26", "WF27"):
            row = self.rule_row("07-workflow.md", rid)
            self.assertNotIn("an M with waves", row, rid)
            self.assertNotIn("`plan.md` only", row, rid)
        self.assertNotIn("unless M has waves", self.rule_row("06-docs-system.md", "DS49"))

    def test_r13_m07_row_points_to_docs_flow_eval(self):
        t = (ROOT / "MAINTAINING.md").read_text(encoding="utf-8")
        m = re.search(r"^\| M07 \|.*$", t, re.M)
        self.assertIsNotNone(m)
        self.assertIn("/docs-flow-eval", m.group(0))
        self.assertNotIn("wave 2 of the rule-as-data plan", t)


if __name__ == "__main__":
    unittest.main()
