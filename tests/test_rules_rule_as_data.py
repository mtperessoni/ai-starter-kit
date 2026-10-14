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


if __name__ == "__main__":
    unittest.main()
