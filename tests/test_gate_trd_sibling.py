"""gate.py --trd (G23 to G26), --sibling (G28) and G29 through throwaway git projects."""

import tempfile
import unittest
from pathlib import Path

from tests.test_kit_scripts import PY, Project, run, write

GATE = ".claude/skills/prd-flow/scripts/gate.py"
REPO_MD = ".claude/skills/prd-flow/repo.md"

TRD = """\
# TRD · orders

## Where it lives

Base: `src/features/orders/`.

| File | Role | Main symbols | IDs |
|---|---|---|---|
| `order_service.py` | Creates orders | `create_order` | ORD-01..02 |
| `ghost_file.py` | Does not exist | `ghost` | ORD-01 |
| `order_service.py::create_order` | Same file, symbol form | `missing_symbol` | ORD-09 |

Prose cites `src/features/orders/order_service.py` and `.../orders/tests/test_order_service.py` and `application/json`.

## Planned

| File | Changes or creates | Symbols |
|---|---|---|
| `src/features/orders/new_thing.py` | creates | `NewThing` |

Prose in Planned cites `src/features/nowhere.py`.
"""


def commit(p: Project, message: str = "edit") -> None:
    run(p.root, "git", "add", "-A", check=True)
    run(p.root, "git", "commit", "-q", "-m", message, check=True)


class TrdTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        write(self.p.root, "docs/trd/orders.md", TRD)
        commit(self.p)
        self.out = self.p.py(GATE, "--trd")

    def tearDown(self) -> None:
        self.p.close()

    def test_a_missing_path_is_an_error(self) -> None:
        self.assertEqual(self.out.returncode, 1, self.out.stdout)
        self.assertIn("ERROR G23", self.out.stdout)
        self.assertIn("ghost_file.py", self.out.stdout)

    def test_existing_paths_and_suffix_forms_pass(self) -> None:
        self.assertEqual(self.out.stdout.count("ERROR G23"), 1, self.out.stdout)

    def test_planned_section_and_creates_rows_are_skipped(self) -> None:
        self.assertNotIn("new_thing", self.out.stdout)
        self.assertNotIn("nowhere", self.out.stdout)

    def test_a_symbol_absent_from_the_row_files_is_a_warning(self) -> None:
        self.assertIn("WARNING G24", self.out.stdout)
        self.assertIn("missing_symbol", self.out.stdout)
        self.assertNotIn("`create_order`", self.out.stdout)

    def test_an_id_the_files_never_mention_is_a_warning(self) -> None:
        self.assertIn("WARNING G25", self.out.stdout)
        self.assertIn("ORD-09", self.out.stdout)
        self.assertNotIn("ORD-02", self.out.stdout)

    def test_a_file_over_budget_is_a_warning_including_part_files(self) -> None:
        write(self.p.root, "docs/trd/orders/part-one.md", "# part\n" + "line\n" * 300)
        commit(self.p)
        r = self.p.py(GATE, "--trd")
        self.assertIn("WARNING G26", r.stdout)
        self.assertIn("docs/trd/orders/part-one.md", r.stdout)

    def test_the_planned_heading_is_a_config_key(self) -> None:
        repo = self.p.root / REPO_MD
        repo.write_text(repo.read_text(encoding="utf-8").replace("| planned_heading | Planned |", "| planned_heading | Next |"), encoding="utf-8")
        text = (self.p.root / "docs/trd/orders.md").read_text(encoding="utf-8").replace("## Planned", "## Next")
        write(self.p.root, "docs/trd/orders.md", text)
        commit(self.p)
        r = self.p.py(GATE, "--trd")
        self.assertNotIn("nowhere", r.stdout)

    def test_it_writes_nothing(self) -> None:
        before = run(self.p.root, "git", "status", "--porcelain").stdout
        self.p.py(GATE, "--trd")
        self.assertEqual(run(self.p.root, "git", "status", "--porcelain").stdout, before)


class TrdEdgeTest(unittest.TestCase):
    def test_a_short_row_and_a_non_ascii_file_name(self) -> None:
        p = Project()
        try:
            write(p.root, "src/features/orders/café.py", "x = 1\n")
            write(p.root, "docs/trd/orders.md", "| File | Role | Main symbols | IDs |\n|---|---|---|---|\n"
                  "| `order_service.py` |\n| `café.py` | Coffee | `x` | |\n")
            commit(p)
            r = p.py(GATE, "--trd")
            self.assertNotIn("Traceback", r.stderr)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        finally:
            p.close()

    def test_an_ellipsis_is_a_placeholder_not_a_path(self) -> None:
        p = Project()
        try:
            write(p.root, "docs/trd/orders.md", "# Orders\n\nImports like `src/features/...` or `src/.../order.py` resolve through aliases.\n")
            commit(p)
            r = p.py(GATE, "--trd")
            self.assertNotIn("ERROR G23", r.stdout)
        finally:
            p.close()

    def test_a_git_ignored_path_and_a_glob_folder_are_not_missing(self) -> None:
        p = Project()
        try:
            write(p.root, ".gitignore", ".claude/prd-flow/state/\n")
            write(p.root, "docs/trd/orders.md", "# Orders\n\nLogs go to `.claude/prd-flow/state/_tests`; tests live in `src/features/*/tests/`.\n")
            commit(p)
            r = p.py(GATE, "--trd")
            self.assertNotIn("ERROR G23", r.stdout)
        finally:
            p.close()


class SiblingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        self.sib = tempfile.TemporaryDirectory()
        self.sib_root = Path(self.sib.name)
        self.sibling = self.sib_root / "docs/prd/shop"
        write(self.p.root, "docs/prd/shop/a.md", "one\ntwo\n")
        commit(self.p)
        self.orders = (self.p.root / "docs/prd/shop/05-orders.md").read_text(encoding="utf-8")

    def tearDown(self) -> None:
        self.p.close()
        self.sib.cleanup()

    def share(self, sibling: Path) -> None:
        repo = self.p.root / REPO_MD
        text = repo.read_text(encoding="utf-8").replace(
            "| `<docs/prd/triage-documents>` | `<C:/Projects/backend/docs/prd/triage-documents>` | `<this repository or the sibling>` |",
            f"| `docs/prd/shop` | `{sibling.as_posix()}` | this repository |",
        )
        repo.write_text(text, encoding="utf-8")

    def test_identical_folders_pass_with_other_line_endings(self) -> None:
        self.sibling.mkdir(parents=True)
        (self.sibling / "05-orders.md").write_bytes(self.orders.replace("\n", "\r\n").encode("utf-8"))
        (self.sibling / "a.md").write_bytes(b"one\r\ntwo\r\n")
        self.share(self.sibling)
        r = self.p.py(GATE, "--sibling")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_different_content_is_g28(self) -> None:
        write(self.sib_root, "docs/prd/shop/a.md", "one\nthree\n")
        self.share(self.sibling)
        r = self.p.py(GATE, "--sibling")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("ERROR G28", r.stdout)

    def test_a_file_only_on_one_side_is_g28(self) -> None:
        write(self.sib_root, "docs/prd/shop/a.md", "one\ntwo\n")
        write(self.sib_root, "docs/prd/shop/extra.md", "x\n")
        self.share(self.sibling)
        r = self.p.py(GATE, "--sibling")
        self.assertIn("ERROR G28", r.stdout)
        self.assertIn("extra.md", r.stdout)

    def test_a_relative_sibling_path_resolves_against_the_repository_root(self) -> None:
        write(self.p.root, "other/shop/a.md", "one\nthree\n")
        self.share(Path("other/shop"))
        r = run(self.p.root / "src", PY, str(self.p.root / GATE), "--sibling")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("ERROR G28", r.stdout)

    def test_a_heading_with_a_suffix_is_still_the_shared_section(self) -> None:
        repo = self.p.root / REPO_MD
        text = repo.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^## Shared PRDs")
        repo.write_text(text.replace("## Shared PRDs", "## Shared PRDs (note)", 1), encoding="utf-8")
        write(self.sib_root, "docs/prd/shop/a.md", "one\nthree\n")
        self.share(self.sibling)
        self.assertIn("ERROR G28", self.p.py(GATE, "--sibling").stdout)

    def test_an_absent_sibling_is_a_warning(self) -> None:
        self.share(self.sibling / "nope")
        r = self.p.py(GATE, "--sibling")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING G28", r.stdout)

    def test_placeholder_rows_are_ignored(self) -> None:
        r = self.p.py(GATE, "--sibling")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("G28", r.stdout)


class GeneratedHtmlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        repo = self.p.root / REPO_MD
        text = repo.read_text(encoding="utf-8")
        text = text.replace("| html_mode | hand |", "| html_mode | generated |")
        repo.write_text(text, encoding="utf-8")
        self.builder = self.p.root / ".claude/skills/prd-flow/scripts/build_prd_html.py"

    def tearDown(self) -> None:
        self.p.close()

    def fake(self, body: str) -> None:
        self.builder.write_text(body, encoding="utf-8")

    def page(self, text: str) -> None:
        (self.p.root / "docs/prd/prd.html").write_text(text, encoding="utf-8", newline="\n")

    def test_a_stale_html_is_g29_with_the_hint(self) -> None:
        self.fake("def is_current(root, cfg):\n    return (root / cfg['html']).read_text(encoding='utf-8') == '<p>fresh</p>\\n'\n")
        self.page("<p>stale</p>\n")
        r = self.p.py(GATE)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING G29", r.stdout)
        self.assertIn("fix: run /docs-html", r.stdout)

    def test_a_missing_html_is_g29(self) -> None:
        self.fake("def is_current(root, cfg):\n    return False\n")
        (self.p.root / "docs/prd/prd.html").unlink()
        r = self.p.py(GATE)
        self.assertIn("WARNING G29", r.stdout)

    def test_an_unimportable_builder_is_reported_not_a_crash(self) -> None:
        self.fake("raise ImportError('boom')\n")
        r = self.p.py(GATE)
        self.assertIn("WARNING G29", r.stdout)
        self.assertIn("boom", r.stdout)
        self.assertNotIn("Traceback", r.stderr)
