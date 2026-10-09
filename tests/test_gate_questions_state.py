"""--rules reading a state folder that holds only rules.md."""

import unittest

from tests.test_kit_scripts import Project, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"
RULES_MD = """# Rules · orders · 2026-10-07 · Ana

## shop/05-orders.md
| ID | Rule | Source | Change via |
|---|---|---|---|
| ORD-03 | Orders can be reopened. | planned | code |

## Conflicts
| ID | Resolution | Note |
|---|---|---|
"""


class RulesFromStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | hand |"), encoding="utf-8")
        write(self.p.root, "state/orders/rules.md", RULES_MD)

    def tearDown(self) -> None:
        self.p.close()

    def test_rules_reads_a_state_folder_with_only_rules_md(self) -> None:
        r = self.p.py(GATE, "--rules", "state/orders/approved-rules.md")
        self.assertNotIn("Traceback", r.stderr)
        self.assertNotIn("Q2", r.stdout)
        self.assertNotIn("Q3", r.stdout)
        self.assertFalse((self.p.root / "state/orders/approved-rules.md").exists())

    def test_applied_compares_the_rows_of_rules_md_with_the_prd(self) -> None:
        r = self.p.py(GATE, "--rules", "state/orders/approved-rules.md", "--applied")
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("Q4 ORD-03 is not in the PRD yet", r.stdout)

    def test_no_state_record_at_all_is_a_clean_error(self) -> None:
        (self.p.root / "state/orders/rules.md").unlink()
        r = self.p.py(GATE, "--rules", "state/orders/approved-rules.md")
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("ERROR Q2", r.stdout)


if __name__ == "__main__":
    unittest.main()
