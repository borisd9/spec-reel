"""Checks that the skill's documents agree with each other and with the files on disk.

These catch the drift that hand edits cause: a renamed reference, a broken link, a delta line
edited in one place only, a delta added without updating its count, a config key missing from
the README.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = [ROOT / "SKILL.md", ROOT / "README.md", *sorted((ROOT / "references").glob("*.md"))]
NUMBERS = {"three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
# Files of the installed HyperFrames skills that these docs name on purpose.
EXTERNAL = {"references/brief-format.md", "references/script-format.md"}
DELTA_LINE = re.compile(r"^(?:- )?(faceless-explainer deltas in force: .+)$", re.M)


def frontmatter(md):
    m = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    return dict(re.findall(r"^([\w-]+):\s*(.*)$", m.group(1), re.M)) if m else {}


class SkillStructureTests(unittest.TestCase):
    def test_frontmatter(self):
        fm = frontmatter((ROOT / "SKILL.md").read_text())
        self.assertEqual(fm.get("name"), "spec-reel")
        self.assertTrue(0 < len(fm.get("description", "").strip('"')) <= 1024)
        self.assertTrue(fm.get("argument-hint"))

    def test_named_skill_files_exist(self):
        for doc in DOCS:
            for rel in set(re.findall(r"(?<![\w/.-])((?:references|scripts)/[\w.-]+\.(?:md|py))", doc.read_text())) - EXTERNAL:
                self.assertTrue((ROOT / rel).is_file(), f"{doc.name} names {rel}, which does not exist")

    def test_relative_links_resolve(self):
        for doc in DOCS:
            for target in re.findall(r"\]\(([^)\s]+)\)", doc.read_text()):
                if re.match(r"^(?:[a-z]+:|#)", target) or "..." in target:  # URLs, anchors, placeholder patterns
                    continue
                path = (doc.parent / target.split("#")[0]).resolve()
                self.assertTrue(path.exists(), f"{doc.name} links to {target}, which does not exist")

    def test_delta_line_is_identical_everywhere(self):
        lines = {doc.name: DELTA_LINE.findall(doc.read_text()) for doc in (ROOT / "SKILL.md", ROOT / "references/handoff.md")}
        for name, found in lines.items():
            self.assertEqual(len(found), 1, f"{name} should hold the delta line once")
        self.assertEqual(lines["SKILL.md"], lines["handoff.md"])

    def test_delta_count_matches_its_word(self):
        handoff = (ROOT / "references/handoff.md").read_text()
        word, body = re.search(r"^## The (\w+) deltas\n(.*?)(?=^## )", handoff, re.S | re.M).groups()
        self.assertEqual(len(re.findall(r"^\d+\. \*\*", body, re.M)), NUMBERS[word])
        for said in re.findall(r"\b(\w+) (?:small )?deltas\b", (ROOT / "SKILL.md").read_text()):
            if said in NUMBERS:
                self.assertEqual(said, word, "SKILL.md and handoff.md name different delta counts")

    def test_config_keys_match_readme_table(self):
        keys = set(json.loads((ROOT / "config.example.json").read_text()))
        configure = re.search(r"^## Configure\n(.*?)(?=^## )", (ROOT / "README.md").read_text(), re.S | re.M).group(1)
        self.assertEqual(set(re.findall(r"^\| `(\w+)` \|", configure, re.M)), keys)


if __name__ == "__main__":
    unittest.main()
