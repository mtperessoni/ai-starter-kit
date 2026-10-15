"""preamble.py: the fixed context every session and subagent loads before its first action (CE18, audit 2026-10-15 H01)."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("preamble", ROOT / "kit" / "scripts" / "preamble.py")
preamble = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preamble)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class PreambleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.repo = base / "repo"
        self.home = base / "home"
        write(self.repo / "CLAUDE.md", "a" * 400 + "\n@AGENTS.md\n")
        write(self.repo / "AGENTS.md", "b" * 800 + "\n@docs/extra.md\n")
        write(self.repo / "docs" / "extra.md", "c" * 40)
        write(self.repo / "docs" / "lazy.md", "z" * 10000)
        write(self.repo / ".claude" / "agents" / "rev.md",
              "---\nname: rev\ndescription: " + "d" * 120 + "\nmodel: sonnet\n---\n\n" + "body " * 500)
        write(self.repo / ".claude" / "skills" / "s1" / "SKILL.md",
              "---\nname: s1\ndescription: " + "e" * 80 + "\n---\n" + "body " * 500)
        write(self.home / ".claude" / "CLAUDE.md", "f" * 200)
        slug = preamble.project_slug(self.repo)
        write(self.home / ".claude" / "projects" / slug / "memory" / "MEMORY.md", "g" * 300)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_parts_follow_imports_and_skip_lazy_files(self):
        parts = preamble.measure(self.repo, self.home)
        self.assertEqual(parts["repo_instructions"], 400 + 800 + 40 + len("\n@AGENTS.md\n") + len("\n@docs/extra.md\n"))
        self.assertNotIn("lazy", " ".join(preamble.sources(self.repo, self.home)))

    def test_agent_and_skill_count_only_their_descriptions(self):
        parts = preamble.measure(self.repo, self.home)
        self.assertLess(parts["agent_descriptions"], 200)
        self.assertGreaterEqual(parts["agent_descriptions"], 120)
        self.assertLess(parts["skill_descriptions"], 150)

    def test_user_files_and_memory_index(self):
        parts = preamble.measure(self.repo, self.home)
        self.assertEqual(parts["user_instructions"], 200)
        self.assertEqual(parts["memory_index"], 300)

    def test_over_budget_warns_and_within_budget_is_quiet(self):
        parts = preamble.measure(self.repo, self.home)
        warns = preamble.warnings(parts, {"repo_instructions": 100})
        self.assertEqual(len(warns), 1)
        self.assertIn("repo_instructions", warns[0])
        self.assertEqual(preamble.warnings(parts, {"repo_instructions": 100000}), [])

    def test_tokens_estimate(self):
        self.assertEqual(preamble.tokens(3500), 1000)


if __name__ == "__main__":
    unittest.main()
