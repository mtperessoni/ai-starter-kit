"""close_gate.py docs step against the real gate.py (review 1/5 of the efficiency delivery: a removed flag passed every fake)."""

import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "kit" / "scripts"
GATE_DIR = ROOT / "kit" / ".claude" / "skills" / "prd-flow" / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("close_gate", SCRIPTS / "close_gate.py")
close_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(close_gate)


class DocsStepTest(unittest.TestCase):
    def test_every_flag_of_the_docs_step_exists_in_the_real_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(GATE_DIR, root / ".claude" / "skills" / "prd-flow" / "scripts")
            args = close_gate.docs_step(root, "003-orders")
            self.assertEqual(args, ["docs", "003-orders"])
            help_text = subprocess.run([sys.executable, str(GATE_DIR / "gate.py"), "--help"], capture_output=True,
                                       text=True, timeout=60, check=False).stdout
            self.assertIn("--docs", help_text)
            gates = (SCRIPTS / "gates.sh").read_text(encoding="utf-8")
            docs_case = re.search(r"^docs\)\n(.*?)\n    ;;", gates, re.S | re.M).group(1)
            for flag in re.findall(r"--[a-z-]+", docs_case):
                self.assertIn(flag, help_text, f"gates.sh docs passes {flag}, gate.py does not accept it")

    def test_without_the_skill_the_step_is_the_bare_docs_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(close_gate.docs_step(Path(tmp), "s1"), ["docs"])


if __name__ == "__main__":
    unittest.main()
