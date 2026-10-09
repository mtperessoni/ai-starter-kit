"""Runtime text consistency (MAINTAINING.md M10, M11, M13 and removed concepts).

M11: a rule ID of rules/ cited in a runtime file must be defined as a table row
`| <ID> |` somewhere in kit/ (a file the agent loads).
M10: no sentence of 14 or more words is repeated verbatim across the prd-flow
skill and agent files; no interpreter fallback chain in instructions.
M13: "references before the first mode" counts the distinct `reference/*.md`
file names mentioned in the body of a prd-flow agent file before its first
heading that starts a mode or task section (a `## ` heading containing Mode,
mode, Task, task, Modes or Tasks, or a bold mode label line); the body starts
after the YAML frontmatter. At most 3.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "kit"
TEXT_EXT = {".md", ".py", ".sh"}

SKILL_DIR = KIT / ".claude" / "skills" / "prd-flow"
AGENTS = sorted((KIT / ".claude" / "agents").glob("prd-flow-*.md"))

unittest.TestCase.maxDiff = None
DUPLICATE_ALLOWLIST = {}


def runtime_files():
    files = [p for p in KIT.rglob("*") if p.is_file() and p.suffix in TEXT_EXT]
    files.append(ROOT / "global" / "CLAUDE.md")
    return [p for p in files if "__pycache__" not in p.parts and "fixtures" not in p.parts]


def rel(p):
    return p.relative_to(ROOT).as_posix()


def rule_prefixes():
    found = set()
    for p in (ROOT / "rules").glob("*.md"):
        for m in re.finditer(r"^\| (?:\*\*)?([A-Z]{2})\d{2}\b", p.read_text(encoding="utf-8"), re.M):
            found.add(m.group(1))
    return found


def body(path):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def body_lines(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    start = 0
    if lines and lines[0] == "---":
        for i in range(1, len(lines)):
            if lines[i] == "---":
                start = i + 1
                break
    return [(i + 1, lines[i]) for i in range(start, len(lines))]


class RuleIdsDefined(unittest.TestCase):
    def test_m11_no_dangling_rule_citation(self):
        self.assertEqual(self.dangling(lambda r: not r.startswith("kit/scripts/")), [])

    def test_m11_no_dangling_rule_citation_in_scripts(self):
        # retro_detectors.py emits rule IDs as finding data for the kit maintainer, not as instructions.
        self.assertEqual(self.dangling(lambda r: r.startswith("kit/scripts/") and not r.endswith("retro_detectors.py")), [])

    def dangling(self, scope):
        prefixes = rule_prefixes()
        self.assertTrue(prefixes)
        pat = re.compile(r"\b(?:%s)\d{2}\b" % "|".join(sorted(prefixes)))
        defined = set()
        files = runtime_files()
        for p in files:
            for m in re.finditer(r"^\| (?:\*\*)?([A-Z]{2}\d{2})\b", p.read_text(encoding="utf-8"), re.M):
                defined.add(m.group(1))
        dangling = []
        for p in files:
            if not scope(rel(p)):
                continue
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                for m in pat.finditer(line):
                    if m.group(0) not in defined:
                        dangling.append("%s:%d %s" % (rel(p), n, m.group(0)))
        return dangling


class NoDuplicateSentences(unittest.TestCase):
    def test_m10_no_long_sentence_in_two_files(self):
        files = list(SKILL_DIR.rglob("*.md")) + AGENTS
        seen = {}
        for p in files:
            text = body(p)
            for sent in re.split(r"(?<=[.!?:])\s+|\n+", text):
                s = re.sub(r"\s+", " ", sent.strip(" |-*`>#"))
                if len(s.split()) >= 14:
                    seen.setdefault(s, set()).add(rel(p))
        dups = ["%s :: %s" % (sorted(v), s[:80]) for s, v in seen.items()
                if len(v) > 1 and s not in DUPLICATE_ALLOWLIST]
        self.assertEqual(dups, [])

    def test_m10_single_interpreter_instruction(self):
        bad = []
        pat = re.compile(r"/c/Python314|python3? \|\||\|\| ?python|python3 \|\| ")
        for p in runtime_files():
            if p.suffix != ".md":
                continue
            for n, line in body_lines(p):
                if pat.search(line):
                    bad.append("%s:%d" % (rel(p), n))
        self.assertEqual(bad, [])


class AgentReferenceBudget(unittest.TestCase):
    def test_m13_at_most_three_references_before_first_mode(self):
        mode_head = re.compile(r"^(?:#{2,3} .*\b(?:[Mm]odes?|[Tt]asks?)\b.*|\*\*(?:[Mm]ode|[Tt]ask)\b.*)$")
        for p in AGENTS:
            before = []
            for line in body(p).splitlines():
                if mode_head.match(line):
                    break
                before.append(line)
            refs = set(re.findall(r"reference/([\w-]+\.md)", "\n".join(before)))
            self.assertLessEqual(len(refs), 3, "%s names %s" % (rel(p), sorted(refs)))


class RemovedConcepts(unittest.TestCase):
    PATTERNS = [
        (r"\bdocs `?(?:rules|prd-plan|trd-plan)\b", "removed docs mode"),
        (r"`(?:rules|prd-plan|trd-plan)`", "removed docs mode"),
        (r"\bfolded\b", "folded"),
        (r"[Rr]ound 0", "round 0"),
        (r"\bDimensions\b", "Dimensions"),
        (r"delta\.md", "delta.md"),
        (r"question_lint", "question_lint"),
        (r"--questions", "--questions"),
        (r"Confirmed:", "Confirmed: line"),
        (r"\bG25\b", "gone warning"),
    ]

    def test_removed_concepts_not_mentioned(self):
        found = []
        for p in runtime_files():
            r = rel(p)
            if p.suffix != ".md" or "skills/prd-create/" in r:
                continue
            for n, line in body_lines(p):
                for pat, name in self.PATTERNS:
                    if re.search(pat, line):
                        found.append("%s:%d %s" % (r, n, name))
                if re.search(r"G28", line) and "--sibling" not in line:
                    found.append("%s:%d G28 outside --sibling" % (r, n))
                if "prd-flow" in r or "agents/prd-flow" in r:
                    if re.search(r"interview\.md", line) and "reference/interview.md" not in line \
                            and "[interview.md]" not in line and "interview.md](" not in line:
                        found.append("%s:%d interview.md state file" % (r, n))
        self.assertEqual(found, [])

    def test_g29_g32_only_with_html_flag(self):
        bad = []
        for p in runtime_files():
            if p.suffix != ".md":
                continue
            for n, line in body_lines(p):
                if re.search(r"\bG(?:29|32)\b", line) and "--html" not in line \
                        and "docs-html" not in rel(p):
                    bad.append("%s:%d" % (rel(p), n))
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
