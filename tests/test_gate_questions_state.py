"""gate_interview question lint (Q6 to Q9) and --rules reading a state folder that holds only rules.md."""

import unittest

from tests.test_kit_scripts import Project, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"
DIMS = "\n".join(f"| D{n:02d} thing | doc | x |" for n in range(1, 16))
GOOD = '''## Survey
Questions
Q1 · D05 · "The payment provider takes 45 s to answer: what does the customer see?"
  - "Try again" after 20 s, cart kept (Recommended): fewer stuck carts, per ORD-01
  - Wait up to 60 s: today's "wait" rule stays; the customer waits longer
  - The scenario is wrong: say what really happens
'''


class QuestionLintTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        self.repo = repo
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | hand |"), encoding="utf-8")

    def tearDown(self) -> None:
        self.p.close()

    def lint(self, text: str) -> str:
        write(self.p.root, "state/orders/questions.md", text)
        return self.p.py(GATE, "--questions", "state/orders/questions.md").stdout

    def test_a_clean_question_passes(self) -> None:
        out = self.lint(GOOD)
        self.assertNotIn("Q6", out)
        self.assertNotIn("Q7", out)
        self.assertNotIn("Q8", out)
        self.assertNotIn("Q9", out)
        self.assertIn("0 error(s), 0 warning(s)", out)

    def test_an_option_without_a_row_or_rule_text_warns(self) -> None:
        out = self.lint(GOOD.replace('"Try again" after 20 s, cart kept (Recommended): fewer stuck carts, per ORD-01', "Try again after 20 s (Recommended): fewer stuck carts"))
        self.assertIn("WARNING Q6 Q1", out)

    def test_an_option_with_two_decisions_warns(self) -> None:
        out = self.lint(GOOD.replace("Wait up to 60 s:", "Wait up to 60 s and also keep the cart for a day:"))
        self.assertIn("WARNING Q7 Q1", out)

    def test_jargon_from_the_adapter_is_flagged(self) -> None:
        out = self.lint(GOOD.replace("what does the customer see?", "which flag does the handler read?"))
        self.assertIn("WARNING Q8 Q1", out)
        self.assertIn("flag", out)

    def test_the_plain_words_key_replaces_the_list(self) -> None:
        self.repo.write_text(self.repo.read_text(encoding="utf-8").replace("| html_mode | hand |", "| html_mode | hand |\n| plain_words | stuck |"), encoding="utf-8")
        out = self.lint(GOOD)
        self.assertIn("WARNING Q8 Q1", out)
        self.assertIn("stuck", out)

    def test_a_missing_scenario_is_wrong_option_warns(self) -> None:
        out = self.lint(GOOD.replace("  - The scenario is wrong: say what really happens\n", ""))
        self.assertIn("WARNING Q9 Q1", out)

    def test_question_lint_error_makes_them_errors(self) -> None:
        self.repo.write_text(self.repo.read_text(encoding="utf-8").replace("| html_mode | hand |", "| html_mode | hand |\n| question_lint | error |"), encoding="utf-8")
        out = self.lint(GOOD.replace("  - The scenario is wrong: say what really happens\n", ""))
        self.assertIn("ERROR Q9 Q1", out)


RULES_MD = f"""# Rules · orders · 2026-10-07 · Ana

## shop/05-orders.md
| ID | Rule | Source | Change via |
|---|---|---|---|
| ORD-03 | Orders can be reopened. | planned | code |

## Conflicts
| ID | Resolution | Note |
|---|---|---|

## Dimensions
| Dimension | State | Answer |
|---|---|---|
{DIMS}

Confirmed: Ana · 2026-10-07 · "go"
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
