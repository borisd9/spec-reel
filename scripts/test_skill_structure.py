"""Checks that the skill's documents agree with each other and with the files on disk.

These catch the drift that hand edits cause: a renamed reference, a broken link, a script or asset a
document names that is not there, a retired skill still named, a config key missing from the README.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = [ROOT / "SKILL.md", ROOT / "README.md", *sorted((ROOT / "references").glob("*.md"))]
# Files of the installed HyperFrames skill that these docs name on purpose (the dependency check in handoff.md).
EXTERNAL = {"references/film.md", "references/format.md", "references/sound.md"}
NAMED = re.compile(r"(?<![\w/.-])((?:references|scripts|assets)/[\w./-]*[\w]\.(?:md|py|html|json|woff2|txt))")


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
            for rel in set(NAMED.findall(doc.read_text())) - EXTERNAL:
                if rel.startswith("references/types/"):  # the installed HyperFrames explainer route
                    continue
                self.assertTrue((ROOT / rel).is_file(), f"{doc.name} names {rel}, which does not exist")

    def test_every_script_and_asset_is_documented_and_present(self):
        skill = (ROOT / "SKILL.md").read_text() + (ROOT / "references/handoff.md").read_text()
        for rel in ("scripts/finish.py", "scripts/build_index.py", "assets/scene.template.html"):
            self.assertTrue((ROOT / rel).is_file(), rel)
            self.assertIn(rel, skill, f"SKILL.md and handoff.md never mention {rel}")
        self.assertTrue((ROOT / "assets/index.template.html").is_file())
        self.assertTrue((ROOT / "assets/fonts/OFL.txt").is_file())
        self.assertEqual(len(list((ROOT / "assets/fonts").glob("*.woff2"))), 3)

    def test_no_document_names_the_retired_skill(self):
        for doc in DOCS:
            self.assertNotIn("faceless-explainer", doc.read_text(), doc.name)

    def test_relative_links_resolve(self):
        for doc in DOCS:
            for target in re.findall(r"\]\(([^)\s]+)\)", doc.read_text()):
                if re.match(r"^(?:[a-z]+:|#)", target) or "..." in target:  # URLs, anchors, placeholder patterns
                    continue
                path = (doc.parent / target.split("#")[0]).resolve()
                self.assertTrue(path.exists(), f"{doc.name} links to {target}, which does not exist")

    def test_dependency_check_names_the_files_the_docs_rely_on(self):
        """The loop in handoff.md must list every HyperFrames file the skill's docs send the reader to."""
        handoff = (ROOT / "references/handoff.md").read_text()
        loop = re.search(r"^for f in (.+?); do$", handoff, re.M).group(1).split()
        self.assertIn("references/types/explainer.md", loop)
        for rel in EXTERNAL:
            self.assertIn(rel, loop)

    def test_config_keys_match_readme_table(self):
        keys = set(json.loads((ROOT / "config.example.json").read_text()))
        configure = re.search(r"^## Configure\n(.*?)(?=^## )", (ROOT / "README.md").read_text(), re.S | re.M).group(1)
        self.assertEqual(set(re.findall(r"^\| `(\w+)` \|", configure, re.M)), keys)


if __name__ == "__main__":
    unittest.main()
