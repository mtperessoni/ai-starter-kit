"""gate.py HTML policy: the change flow only warns (G29, G5), --html is the strict check of the docs-html skill."""

import unittest

from tests.test_kit_scripts import Project

GATE = ".claude/skills/prd-flow/scripts/gate.py"
REPO_MD = ".claude/skills/prd-flow/repo.md"
BUILDER = ".claude/skills/prd-flow/scripts/build_prd_html.py"
PAGE = "docs/prd/prd.html"
CURRENT = "def is_current(root, cfg):\n    return (root / cfg['html']).read_text(encoding='utf-8') == '<p>fresh</p>\\n'\n"
EM_DASH = chr(0x2014)


TRD_BUILDER = ".claude/skills/prd-flow/scripts/build_trd_html.py"
TRD_PAGE = "docs/trd/trd.html"


class GateHtmlPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        self.trd_builder(True)

    def trd_builder(self, current: bool) -> None:
        (self.p.root / TRD_PAGE).parent.mkdir(parents=True, exist_ok=True)
        (self.p.root / TRD_PAGE).write_text("<p>trd</p>\n", encoding="utf-8")
        (self.p.root / "docs/trd/README.md").write_text("# TRD\n", encoding="utf-8")
        (self.p.root / TRD_BUILDER).write_text(f"def is_current(root, cfg):\n    return {current}\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.p.close()

    def mode(self, old: str, new: str) -> None:
        repo = self.p.root / REPO_MD
        repo.write_text(repo.read_text(encoding="utf-8").replace(f"| html_mode | {old} |", f"| html_mode | {new} |"), encoding="utf-8")

    def config(self, key: str, value: str) -> None:
        repo = self.p.root / REPO_MD
        lines = [f"| {key} | {value} |" if line.startswith(f"| {key} |") else line for line in repo.read_text(encoding="utf-8").splitlines()]
        repo.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def page(self, text: str) -> None:
        (self.p.root / PAGE).write_text(text, encoding="utf-8", newline="\n")

    def builder(self, body: str = CURRENT) -> None:
        (self.p.root / BUILDER).write_text(body, encoding="utf-8")

    def test_default_run_generated_stale_page_is_not_printed(self) -> None:
        self.builder()
        self.page("<p>stale</p>\n")
        r = self.p.py(GATE)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("G29", r.stdout)
        self.assertNotIn("/docs-html", r.stdout)

    def test_default_run_generated_missing_page_is_not_printed(self) -> None:
        self.builder("def is_current(root, cfg):\n    return False\n")
        (self.p.root / PAGE).unlink()
        r = self.p.py(GATE)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("G29", r.stdout)

    def test_default_run_generated_current_page_is_silent(self) -> None:
        self.builder()
        self.page("<p>fresh</p>\n")
        r = self.p.py(GATE)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("G29", r.stdout)

    def test_steps_prd_and_trd_also_only_warn(self) -> None:
        self.builder()
        self.page("<p>stale</p>\n")
        for step in ("prd", "trd"):
            r = self.p.py(GATE, "--step", step)
            self.assertNotIn("ERROR G29", r.stdout, step)

    def test_default_run_hand_mode_emits_the_g5_migration_warning_and_no_html_check(self) -> None:
        self.mode("generated", "hand")
        self.page("<p>anything</p>\n")
        r = self.p.py(GATE)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING G5 html_mode hand: the HTML is not checked; migrate to generated with /ai-kit update, then /docs-html", r.stdout)
        self.assertNotIn("G6", r.stdout)
        self.assertNotIn("G10", r.stdout)

    def test_default_run_with_html_none_says_nothing_about_html(self) -> None:
        self.mode("generated", "hand")
        self.config("html", "none")
        r = self.p.py(GATE)
        self.assertNotIn("G5", r.stdout)
        self.assertNotIn("G29", r.stdout)

    def test_default_run_em_dash_in_the_html_page_is_not_scanned(self) -> None:
        self.builder()
        self.page(f"<p>fresh {EM_DASH}</p>\n")
        r = self.p.py(GATE)
        self.assertNotIn("G4", r.stdout)

    def test_default_run_em_dash_in_the_markdown_is_still_an_error(self) -> None:
        section = self.p.root / "docs/prd/shop/05-orders.md"
        section.write_text(section.read_text(encoding="utf-8") + f"\nA note {EM_DASH} here.\n", encoding="utf-8")
        r = self.p.py(GATE)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ERROR G4", r.stdout)

    def test_html_flag_generated_stale_page_is_an_error(self) -> None:
        self.builder()
        self.page("<p>stale</p>\n")
        r = self.p.py(GATE, "--html")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G29", r.stdout)
        self.assertIn("fix: run /docs-html", r.stdout)

    def test_html_flag_generated_missing_page_is_an_error(self) -> None:
        self.builder("def is_current(root, cfg):\n    return False\n")
        (self.p.root / PAGE).unlink()
        r = self.p.py(GATE, "--html")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G29", r.stdout)

    def test_html_flag_generated_current_page_passes(self) -> None:
        self.builder()
        self.page("<p>fresh</p>\n")
        r = self.p.py(GATE, "--html")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_html_flag_scans_the_page_for_em_dash(self) -> None:
        self.builder("def is_current(root, cfg):\n    return True\n")
        self.page(f"<p>x {EM_DASH}</p>\n")
        r = self.p.py(GATE, "--html")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G4", r.stdout)

    def test_html_flag_hand_mode_is_an_error(self) -> None:
        self.mode("generated", "hand")
        r = self.p.py(GATE, "--html")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G5", r.stdout)
        self.assertIn("docs-html builds only html_mode generated; migrate with /ai-kit update", r.stdout)

    def test_default_run_stale_trd_page_is_not_printed(self) -> None:
        self.builder()
        self.page("<p>fresh</p>\n")
        self.trd_builder(False)
        r = self.p.py(GATE)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("G32", r.stdout)

    def test_html_flag_stale_trd_page_is_a_g32_error(self) -> None:
        self.builder()
        self.page("<p>fresh</p>\n")
        self.trd_builder(False)
        r = self.p.py(GATE, "--html")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(f"ERROR G32 {TRD_PAGE} is out of date", r.stdout)

    def test_html_flag_scans_the_trd_page_for_em_dash(self) -> None:
        self.builder()
        self.page("<p>fresh</p>\n")
        (self.p.root / TRD_PAGE).write_text(f"<p>x {EM_DASH}</p>\n", encoding="utf-8")
        r = self.p.py(GATE, "--html")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(f"ERROR G4 em dash in {TRD_PAGE}", r.stdout)

    def test_no_trd_readme_skips_g32(self) -> None:
        self.builder()
        self.page("<p>fresh</p>\n")
        self.trd_builder(False)
        (self.p.root / "docs/trd/README.md").unlink(missing_ok=True)
        r = self.p.py(GATE, "--html")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("G32", r.stdout)

    def test_trd_html_none_skips_g32(self) -> None:
        self.builder()
        self.page("<p>fresh</p>\n")
        self.trd_builder(False)
        self.config("trd_html", "none")
        r = self.p.py(GATE, "--html")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("G32", r.stdout)

    def test_html_flag_with_html_none_checks_nothing(self) -> None:
        self.config("html", "none")
        r = self.p.py(GATE, "--html")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("G29", r.stdout)


if __name__ == "__main__":
    unittest.main()
