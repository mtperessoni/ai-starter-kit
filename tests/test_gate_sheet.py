"""gate.py --sheet (S1 to S6) and the answers check of --rules (Q3): every sheet item answered, no unasked mechanism."""

import unittest

from tests.test_kit_scripts import Project, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"
STATE = ".claude/prd-flow/state/orders"
ROW = "| ORD-03 | Orders can be reopened. | planned | code |"
RULES_MD = f"# Rules · orders · 2026-10-09 · Ana\n\n## shop/05-orders.md\n| ID | Rule | Source | Change via |\n|---|---|---|---|\n{ROW}\n"
PACK = "# Pack · orders\nBase: abc1234 · Branch: x\nRequest: r\nConflicts: ORD-01\n\n## Rules\n### docs/prd/shop/05-orders.md\n| ORD-03 | Orders can be reopened. |\n"

SHEET = """# Orders can be reopened

## What changes in the rules
| Rule | Today | Becomes | Kind |
|---|---|---|---|
| ORD-03 | (none) | "Orders can be reopened" | adds |
| ORD-01 | "An order needs one item" | "An order needs two items" | rewrites |

## What does not change
- Shipping and the receipt layout.

## Assumed (holds unless you correct it)
- A1 Applies to every tenant.

## Decisions (answer by number)
**1. How long an order stays reopenable** · rule ORD-03
Today: a closed order stays closed (ORD-03).
Why it matters: support reopens by hand.
- A) 20 days (Recommended): fewer manual reopenings
- B) 60 days: more room for the customer
Example: an order closed 25 days ago, under (A) stays closed.
Interacts with: 2

**2. Who can reopen** · mechanism
Today: nobody.
Why it matters: abuse.
- A) Support only (Recommended): safe
- B) The customer: easier
Example: the customer asks, under (A) support answers.

## How to answer
`ok` accepts every recommendation and assumption.
"""
SHEET_2 = """# Follow-up

## Decisions (answer by number)
**1. Which `REOPEN_WINDOW` unit** · rule ORD-03
Today: days.
Why it matters: clarity.
- A) Days (Recommended): simple
- B) Hours: precise
Example: 20 days under (A).
"""
ANSWERS = "## Reply 1\nok\n\n## Resolution\n| Item | Answer | From |\n|---|---|---|\n| 1 | A | ok |\n| 2 | A | ok |\n| A1 | accepted | ok |\n| scope | accepted | ok |\n"


class SheetBase(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        repo = self.p.root / ".claude/skills/prd-flow/repo.md"
        repo.write_text(repo.read_text(encoding="utf-8").replace("| html_mode | generated |", "| html_mode | hand |"), encoding="utf-8")

    def tearDown(self) -> None:
        self.p.close()

    def sheet(self, text: str = SHEET, pack: str | None = PACK) -> str:
        write(self.p.root, f"{STATE}/sheet.md", text)
        if pack is not None:
            write(self.p.root, f"{STATE}/pack.md", pack)
        return self.p.py(GATE, "--sheet", "orders").stdout


class SheetLintTest(SheetBase):
    def test_a_good_sheet_passes(self) -> None:
        self.assertIn("0 error(s), 0 warning(s)", self.sheet())

    def test_help_lists_sheet(self) -> None:
        self.assertIn("--sheet", self.p.py(GATE, "--help").stdout)

    def test_questions_is_an_alias(self) -> None:
        write(self.p.root, f"{STATE}/sheet.md", SHEET)
        write(self.p.root, f"{STATE}/pack.md", PACK)
        self.assertIn("0 error(s)", self.p.py(GATE, "--questions", "orders").stdout)

    def test_s1_a_decision_without_today(self) -> None:
        self.assertIn("ERROR S1", self.sheet(SHEET.replace("Today: nobody.\n", "")))

    def test_s1_a_decision_without_why_or_example(self) -> None:
        self.assertIn("ERROR S1", self.sheet(SHEET.replace("Why it matters: abuse.\n", "")))
        self.assertIn("ERROR S1", self.sheet(SHEET.replace("Example: the customer asks, under (A) support answers.\n", "")))

    def test_s1_two_recommended_or_none(self) -> None:
        self.assertIn("ERROR S1", self.sheet(SHEET.replace("- B) The customer: easier", "- B) The customer (Recommended): easier")))
        self.assertIn("ERROR S1", self.sheet(SHEET.replace(" (Recommended): safe", ": safe")))

    def test_s1_a_single_option(self) -> None:
        self.assertIn("ERROR S1", self.sheet(SHEET.replace("- B) The customer: easier\n", "")))

    def test_s2_a_conflicting_rule_missing_from_the_diff(self) -> None:
        out = self.sheet(SHEET.replace('| ORD-01 | "An order needs one item" | "An order needs two items" | rewrites |\n', ""))
        self.assertIn("ERROR S2", out)
        self.assertIn("ORD-01", out)

    def test_s3_two_decisions_on_the_same_rule_and_scope(self) -> None:
        out = self.sheet(SHEET.replace("**2. Who can reopen** · mechanism", "**2. How long an order stays reopenable** · rule ORD-03"))
        self.assertIn("ERROR S3", out)

    def test_s3_more_than_eight_assumed_lines(self) -> None:
        extra = "".join(f"- A{n} line {n}.\n" for n in range(2, 10))
        self.assertIn("ERROR S3", self.sheet(SHEET.replace("- A1 Applies to every tenant.\n", "- A1 Applies to every tenant.\n" + extra)))

    def test_s4_jargon_in_a_title_warns(self) -> None:
        out = self.sheet(SHEET.replace("Who can reopen", "Which flag reopens"))
        self.assertIn("WARNING S4", out)
        self.assertNotIn("ERROR", out)

    def test_s5_a_comparison_without_a_number_warns(self) -> None:
        text = SHEET.replace("Today: nobody.", "Today: nobody, and it stays closed after the deadline.").replace("Support only (Recommended)", "Support only (Recommended)")
        self.assertIn("WARNING S5", self.sheet(text))
        self.assertNotIn("S5", self.sheet())

    def test_s6_an_interaction_with_a_missing_decision(self) -> None:
        self.assertIn("ERROR S6", self.sheet(SHEET.replace("Interacts with: 2", "Interacts with: 7")))

    def test_the_scope_section_is_mandatory(self) -> None:
        self.assertIn("ERROR S0", self.sheet(SHEET.replace("- Shipping and the receipt layout.\n", "")))

    def test_a_missing_sheet_is_an_error(self) -> None:
        self.assertIn("ERROR", self.p.py(GATE, "--sheet", "orders").stdout)

    def test_only_short_sheets_outside_a_c5_are_linted_without_sheet_md(self) -> None:
        write(self.p.root, f"{STATE}/sheet-short-1.md", SHEET_2)
        self.assertNotIn("ERROR S0", self.p.py(GATE, "--sheet", "orders").stdout)
        write(self.p.root, f"{STATE}/sheet-short-1.md", SHEET_2.replace("Today:", "Now:"))
        self.assertIn("ERROR S1", self.p.py(GATE, "--sheet", "orders").stdout)

    def test_s0_a_sheet_without_a_title_line(self) -> None:
        self.assertIn("ERROR S0", self.sheet(SHEET.replace("# Orders can be reopened\n\n", "", 1)))

    def test_s0_a_sheet_without_how_to_answer(self) -> None:
        out = self.sheet(SHEET.replace("## How to answer\n`ok` accepts every recommendation and assumption.\n", ""))
        self.assertIn("ERROR S0", out)
        self.assertIn("How to answer", out)

    def test_s0_an_adds_row_needs_none_as_today(self) -> None:
        out = self.sheet(SHEET.replace("| ORD-03 | (none) |", '| ORD-03 | "Orders stay closed" |'))
        self.assertIn("ERROR S0", out)
        self.assertIn("ORD-03", out)

    def test_s0_a_missing_pack_warns_that_s2_cannot_run(self) -> None:
        out = self.sheet(SHEET, pack=None)
        self.assertIn("WARNING S0", out)
        self.assertIn("pack.md", out)
        self.assertNotIn("ERROR", out)

    def test_the_sheet_two_items_are_keyed_two_dot_n(self) -> None:
        write(self.p.root, f"{STATE}/sheet-2.md", SHEET_2)
        out = self.sheet()
        self.assertIn("0 error(s)", out)


class AnswersTest(SheetBase):
    def setUp(self) -> None:
        super().setUp()
        write(self.p.root, f"{STATE}/rules.md", RULES_MD)
        write(self.p.root, f"{STATE}/sheet.md", SHEET)
        write(self.p.root, f"{STATE}/answers.md", ANSWERS)

    def gate(self) -> str:
        return self.p.py(GATE, "--rules", f"{STATE}/approved-rules.md").stdout

    def test_every_item_answered_passes(self) -> None:
        self.assertNotIn("Q3", self.gate())

    def test_a_missing_resolution_row_is_q3(self) -> None:
        write(self.p.root, f"{STATE}/answers.md", ANSWERS.replace("| 2 | A | ok |\n", ""))
        out = self.gate()
        self.assertIn("ERROR Q3", out)
        self.assertIn("item 2", out)

    def test_a_missing_assumed_or_scope_row_is_q3(self) -> None:
        write(self.p.root, f"{STATE}/answers.md", ANSWERS.replace("| A1 | accepted | ok |\n", "").replace("| scope | accepted | ok |\n", ""))
        out = self.gate()
        self.assertIn("item A1", out)
        self.assertIn("item scope", out)

    def test_a_missing_answers_file_is_q3(self) -> None:
        (self.p.root / STATE / "answers.md").unlink()
        self.assertIn("ERROR Q3", self.gate())

    def test_an_unasked_mechanism_is_q3(self) -> None:
        write(self.p.root, f"{STATE}/rules.md", RULES_MD.replace("Orders can be reopened.", "Orders can be reopened while the environment variable REOPEN_ORDERS is on."))
        out = self.gate()
        self.assertIn("ERROR Q3", out)
        self.assertIn("REOPEN_ORDERS", out)

    def test_an_unasked_backticked_switch_is_q3(self) -> None:
        write(self.p.root, f"{STATE}/rules.md", RULES_MD.replace("Orders can be reopened.", "Orders can be reopened when the feature flag `reopenEnabled` is set."))
        out = self.gate()
        self.assertIn("ERROR Q3", out)
        self.assertIn("reopenEnabled", out)

    def test_a_generic_word_elsewhere_on_the_row_does_not_make_a_token_a_mechanism(self) -> None:
        text = "Orders can be reopened. The Kind column, a table of options and the flag of the order id `OrderRef` stay."
        write(self.p.root, f"{STATE}/rules.md", RULES_MD.replace("Orders can be reopened.", text))
        self.assertNotIn("Q3", self.gate())

    def test_the_mechanism_word_in_another_cell_than_the_token_is_not_a_hit(self) -> None:
        row = "| ORD-03 | Orders can be reopened by `reopenedAt`. | planned, new endpoint later | code |"
        write(self.p.root, f"{STATE}/rules.md", RULES_MD.replace(ROW, row))
        self.assertNotIn("Q3", self.gate())

    def test_new_table_and_add_a_column_are_mechanisms(self) -> None:
        for phrase in ("adds a new table `order_reopen`", "will add a column `reopenedAt`"):
            with self.subTest(phrase=phrase):
                write(self.p.root, f"{STATE}/rules.md", RULES_MD.replace("Orders can be reopened.", f"Orders can be reopened and it {phrase}."))
                self.assertIn("ERROR Q3", self.gate())

    def test_short_sheets_are_keyed_s_k_and_linted(self) -> None:
        short = SHEET_2.replace("`REOPEN_WINDOW`", "window") + "\n## Assumed (holds unless you correct it)\n- A1 Same tenants.\n\n## What does not change\n- Receipts.\n"
        write(self.p.root, f"{STATE}/sheet-short-1.md", short)
        out = self.gate()
        for key in ("s1.1", "s1.A1", "s1.scope"):
            self.assertIn(f"item {key}", out)
        rows = "| s1.1 | A | ok |\n| s1.A1 | accepted | ok |\n| s1.scope | accepted | ok |\n"
        write(self.p.root, f"{STATE}/answers.md", ANSWERS + rows)
        self.assertNotIn("Q3", self.gate())
        write(self.p.root, f"{STATE}/sheet-short-1.md", short.replace("Today: days.\n", ""))
        write(self.p.root, f"{STATE}/pack.md", PACK)
        self.assertIn("ERROR S1", self.p.py(GATE, "--sheet", "orders").stdout)

    def test_a_mechanism_present_in_the_sheet_is_fine(self) -> None:
        write(self.p.root, f"{STATE}/rules.md", RULES_MD.replace("Orders can be reopened.", "Orders can be reopened by the switch `reopenEnabled`."))
        write(self.p.root, f"{STATE}/sheet.md", SHEET.replace("Support only", "A switch `reopenEnabled` for support only"))
        self.assertNotIn("Q3", self.gate())

    def test_plain_words_are_not_mechanisms(self) -> None:
        text = "Orders can be reopened: a red flag in the Kind column, an acceptable table of options, many endpoints."
        write(self.p.root, f"{STATE}/rules.md", RULES_MD.replace("Orders can be reopened.", text))
        write(self.p.root, f"{STATE}/decisions.md", "# Decisions\n\n| DEC-01 | the Kind column is a table of switches |\n")
        self.assertNotIn("Q3", self.gate())

    def test_sheet_two_items_are_keyed_two_dot_n(self) -> None:
        write(self.p.root, f"{STATE}/sheet-2.md", SHEET_2)
        out = self.gate()
        self.assertIn("item 2.1", out)
        write(self.p.root, f"{STATE}/answers.md", ANSWERS + "| 2.1 | A | Reply 2 |\n")
        self.assertNotIn("Q3", self.gate())

    def test_backticks_in_the_item_cell_are_ignored(self) -> None:
        write(self.p.root, f"{STATE}/answers.md", ANSWERS.replace("| 2 | A | ok |", "| `2` | A | ok |"))
        self.assertNotIn("Q3", self.gate())

    def test_rules_accepts_the_slug(self) -> None:
        write(self.p.root, f"{STATE}/answers.md", ANSWERS.replace("| 2 | A | ok |\n", ""))
        out = self.p.py(GATE, "--rules", "orders").stdout
        self.assertIn("ERROR Q3", out)
        self.assertIn("item 2", out)

    def test_docs_runs_the_sheet_checks_when_sheet_md_exists(self) -> None:
        write(self.p.root, f"{STATE}/sheet.md", SHEET.replace("Today: nobody.\n", ""))
        write(self.p.root, f"{STATE}/pack.md", PACK)
        self.assertIn("ERROR S1", self.p.py(GATE, "--docs", "orders", "--fresh").stdout)

    def test_help_has_one_line_per_flag(self) -> None:
        out = self.p.py(GATE, "--help").stdout
        for flag in ("--base", "--pack", "--rules", "--plan", "--sheet", "--trace", "--change", "--final", "--applied", "--trd", "--html", "--sibling", "--snapshot", "--docs", "--fresh", "--status", "--prd", "--state", "--step"):
            self.assertIn(flag, out)

    def test_no_sheet_means_no_answers_check(self) -> None:
        (self.p.root / STATE / "sheet.md").unlink()
        (self.p.root / STATE / "answers.md").unlink()
        self.assertNotIn("Q3", self.gate())


if __name__ == "__main__":
    unittest.main()
