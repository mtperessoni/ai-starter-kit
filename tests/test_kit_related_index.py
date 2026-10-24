"""K1: the import index selects exactly what the per-module scan selected."""

import json
import sys
import unittest

from tests.test_kit_scripts import KIT, Project, write

FILES = {
    "pkg/__init__.py": "",
    "pkg/core/__init__.py": "",
    "pkg/core/engine.py": "x = 1\n",
    "pkg/core/stages.py": "x = 1\n",
    "pkg/stages/__init__.py": "",
    "pkg/stages/thing.py": "x = 1\n",
    "pkg/util.py": "x = 1\n",
    "top.py": "x = 1\n",
    "web/app.js": "export const a = 1;\n",
    "docs/notes.txt": "pkg.core.engine\n",
    "tests/test_dotted.py": "import pkg.core.engine\n",
    "tests/test_dotted_as.py": "import os, pkg.core.stages as s\n",
    "tests/test_from_names.py": "from pkg.core import engine, stages\n",
    "tests/test_from_pkg.py": "from pkg import util\n",
    "tests/test_stem_is_package.py": "from pkg.stages import thing\n",
    "tests/test_top.py": "import top\n",
    "tests/test_util.py": "x = 1\n",
    "tests/test_comment.py": "# import pkg.core.engine\nx = 'from pkg.util import x'\n",
    "tests/test_wrapped.py": "from pkg.core import (\n    engine,\n    stages,\n)\n",
    "tests/test_js.test.js": "import { a } from './web/app';\n",
    "pkg/core/tests/test_relative_name.py": "from .engine import x\n",
    "pkg/core/tests/test_relative_pkg.py": "from . import engine\n",
    "pkg/other/tests/test_relative_up.py": "from ..core import engine\n",
    "pkg/other/tests/test_relative_far.py": "from ...pkg.core import stages\n",
}


def old_selection(rt, root, cfg, module: str) -> set[str]:
    """The scan this index replaced: every test against imports_module, per module."""
    tests = rt.test_files(root, cfg)
    packages = frozenset(part for f in rt.listed_files(root) for part in f.split("/")[:-1])
    path = root / module
    names = rt.mirror_names(path, cfg)
    picked = set()
    for t in tests:
        text = t.read_text(encoding="utf-8", errors="replace")
        if rt.test_name(t) in names or rt.stem(t) in names or rt.imports_module(text, path, root, packages):
            picked.add(rt.rel(t, root))
    return picked


class ImportIndexTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p = Project()
        for name, text in FILES.items():
            write(self.p.root, name, text)
        config = json.loads((self.p.root / "ai-kit.json").read_text(encoding="utf-8"))
        config["code_extensions"] = [".py", ".js"]
        config["tests"]["always"] = []
        self.cfg = config
        scripts = str(KIT / "scripts")
        sys.path.insert(0, scripts)
        self.addCleanup(sys.path.remove, scripts)
        import related_tests

        self.rt = related_tests

    def tearDown(self) -> None:
        self.p.close()
        sys.modules.pop("related_tests", None)
        sys.modules.pop("kit_config", None)

    def modules(self) -> list[str]:
        return [name for name in FILES if not self.rt.is_test(name, self.cfg) and name.rsplit(".", 1)[-1] in ("py", "js")] + [
            "src/features/orders/order_service.py",
            "src/features/billing/invoice.py",
        ]

    def test_every_module_selects_what_the_old_scan_selected(self) -> None:
        for module in self.modules():
            with self.subTest(module=module):
                new = set(self.rt.related(self.p.root, self.cfg, [module]))
                self.assertEqual(new, old_selection(self.rt, self.p.root, self.cfg, module))

    def test_the_index_selects_the_dotted_from_and_relative_importers(self) -> None:
        picked = set(self.rt.related(self.p.root, self.cfg, ["pkg/core/engine.py"]))
        self.assertTrue(
            {
                "tests/test_dotted.py",
                "tests/test_from_names.py",
                "pkg/other/tests/test_relative_up.py",
            }
            <= picked
        )
        self.assertNotIn("tests/test_comment.py", picked)
        self.assertNotIn("tests/test_stem_is_package.py", picked)

    def test_a_non_python_file_selects_nothing(self) -> None:
        self.assertEqual(self.rt.related(self.p.root, self.cfg, ["docs/notes.txt"]), [])

    def test_a_stem_that_is_also_a_package_name_matches_only_its_module(self) -> None:
        picked = set(self.rt.related(self.p.root, self.cfg, ["pkg/core/stages.py"]))
        self.assertNotIn("tests/test_stem_is_package.py", picked)
        self.assertIn("tests/test_dotted_as.py", picked)

    def test_python_modules_are_matched_through_the_index_not_a_scan_per_module(self) -> None:
        def scan(*args, **kwargs):
            raise AssertionError("per-module scan")

        self.rt.imports_module = scan
        self.assertIn("tests/test_dotted.py", self.rt.related(self.p.root, self.cfg, ["pkg/core/engine.py"]))

    def test_the_old_reference_is_not_empty(self) -> None:
        self.assertIn("tests/test_dotted.py", old_selection(self.rt, self.p.root, self.cfg, "pkg/core/engine.py"))


if __name__ == "__main__":
    unittest.main()
