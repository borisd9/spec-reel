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
EXTERNAL = {"references/film.md", "references/format.md", "references/runtimes.md", "references/sound.md",
            "references/spec.md"}
FONTS = {"Inter", "Montserrat", "Outfit", "Nunito", "Oswald", "League Gothic", "Archivo Black", "Space Mono",
         "IBM Plex Mono", "JetBrains Mono", "EB Garamond", "Playfair Display", "Source Code Pro", "Noto Sans JP",
         "Roboto", "Open Sans", "Lato", "Poppins", "Space Grotesk"}
STYLE_KEYS = ["group", "fits", "palette", "fonts", "runtime", "motion", "rules", "avoid", "prompt"]
HF_SEEK = {"painterly", "tape", "toy3d", "pixel", "cel"}
BANNED = ("faceless-explainer", "Skill tool", "run_in_background")
# A path into one agent's HyperFrames copy; the search loop in handoff.md names folders without a trailing slash.
AGENT_PATH = re.compile(r"\.\w+/skills/hyperframes/")
NAMED = re.compile(r"(?<![\w/.-])((?:references|scripts|assets)/[\w./-]*[\w]\.(?:md|py|html|json|woff2|txt))")


def frontmatter(md):
    m = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    return dict(re.findall(r"^([\w-]+):\s*(.*)$", m.group(1), re.M)) if m else {}


class SkillStructureTests(unittest.TestCase):
    def test_frontmatter(self):
        fm = frontmatter((ROOT / "SKILL.md").read_text())
        self.assertEqual(fm.get("name"), "spec-reel")
        self.assertTrue(0 < len(fm.get("description", "").strip('"')) <= 1024)

    def test_named_skill_files_exist(self):
        for doc in DOCS:
            for rel in set(NAMED.findall(doc.read_text())) - EXTERNAL:
                if rel.startswith("references/types/"):  # the installed HyperFrames explainer route
                    continue
                self.assertTrue((ROOT / rel).is_file(), f"{doc.name} names {rel}, which does not exist")

    def test_every_script_and_asset_is_documented_and_present(self):
        skill = (ROOT / "SKILL.md").read_text() + (ROOT / "references/handoff.md").read_text()
        for rel in ("scripts/finish.py", "scripts/build_index.py", "scripts/look_samples.py", "assets/scene.template.html"):
            self.assertTrue((ROOT / rel).is_file(), rel)
            self.assertIn(rel, skill, f"SKILL.md and handoff.md never mention {rel}")
        self.assertTrue((ROOT / "assets/index.template.html").is_file())
        self.assertTrue((ROOT / "assets/fonts/OFL.txt").is_file())
        self.assertEqual(len(list((ROOT / "assets/fonts").glob("*.woff2"))), 3)

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

    def test_no_banned_terms(self):
        """No retired skill, no one agent's tool names, and HyperFrames paths only through <hyperframes dir>."""
        for doc in DOCS:
            text = doc.read_text()
            for term in BANNED:
                self.assertNotIn(term, text, doc.name)
            self.assertIsNone(AGENT_PATH.search(text), doc.name)

    def test_config_keys_match_readme_table(self):
        keys = set(json.loads((ROOT / "config.example.json").read_text()))
        configure = re.search(r"^## Configure\n(.*?)(?=^## )", (ROOT / "README.md").read_text(), re.S | re.M).group(1)
        self.assertEqual(set(re.findall(r"^\| `(\w+)` \|", configure, re.M)), keys)

    def test_look_gate_is_documented(self):
        skill = (ROOT / "SKILL.md").read_text()
        self.assertIn("sources | digest | script | look | scenes | done", skill)
        self.assertIn("gate 3 (look)", skill)
        self.assertIn("scripts/look_samples.py", skill + (ROOT / "references/handoff.md").read_text())
        self.assertIn("gate 3", (ROOT / "references/yolo.md").read_text().lower())

    def test_no_fixed_style_preset(self):
        self.assertNotIn("style_preset", json.loads((ROOT / "config.example.json").read_text()))
        for doc in DOCS:
            self.assertNotIn("style_preset", doc.read_text(), doc.name)

    def test_scene_template_is_a_bare_skeleton(self):
        t = (ROOT / "assets/scene.template.html").read_text()
        for gone in ("eyebrow", "f.blur(", "f.exit("):
            self.assertNotIn(gone, t)
        for kept in ("<template>", 'data-composition-id="SCENE_ID"', "window.__timelines[S] = tl"):
            self.assertIn(kept, t)

    def test_gate_3_decisions_2026_11_09(self):
        skill = (ROOT / "SKILL.md").read_text()
        self.assertIn("last three runs", skill)
        self.assertNotIn("last five runs", skill)
        self.assertIn("scripts/fetch_font.py", skill)
        yolo = (ROOT / "references/yolo.md").read_text()
        self.assertIn("--look", yolo)
        self.assertNotIn("skip look_samples.py", yolo)

    def test_motion_styles_catalog(self):
        text = (ROOT / "references/motion-styles.md").read_text()
        sections = dict(re.findall(r"^## ([a-z0-9-]+) — .+?\n(.*?)(?=^## |\Z)", text, re.S | re.M))
        self.assertEqual(set(sections), {"swiss", "flat-vector", "morph", "line-draw", "dataviz", "isometric",
                                         "dark-keynote", "screencast", "hud", "print", "papercut", *HF_SEEK})
        for sid, body in sections.items():
            self.assertEqual(re.findall(r"^- (\w+):", body, re.M), STYLE_KEYS, sid)
            fonts = re.search(r"^- fonts: (.+)$", body, re.M).group(1)
            display = re.match(r"display ([A-Za-z ]+?) \d", fonts).group(1)
            self.assertNotIn(display, {"Inter", "Space Grotesk", "JetBrains Mono"}, sid)
            for family in re.findall(r"([A-Z][A-Za-z ]+?) \d{3}", fonts):
                self.assertIn(family, FONTS, f"{sid}: {family}")
            self.assertRegex(re.search(r"^- palette: (.+)$", body, re.M).group(1), r"#[0-9a-f]{6}")
            runtime = re.search(r"^- runtime: (.+)$", body, re.M).group(1)
            self.assertIn(runtime, {"gsap", "hf-seek", "gsap + hf-seek"}, sid)
            if sid in HF_SEEK:
                self.assertEqual(runtime, "hf-seek", sid)
        self.assertIn("## Not used, and why", text)
        self.assertIn("## Default avoid list", text)
        self.assertIn("awesomeclaude.ai", text)

    def test_gate_3_uses_the_catalog(self):
        skill = (ROOT / "SKILL.md").read_text()
        self.assertIn("references/motion-styles.md", skill)
        self.assertIn("STYLE:", skill)
        self.assertIn("three different", (ROOT / "references/motion-styles.md").read_text())
        self.assertIn("references/motion-styles.md", (ROOT / "references/yolo.md").read_text())
        loop = re.search(r"^for f in (.+?); do$", (ROOT / "references/handoff.md").read_text(), re.M).group(1).split()
        self.assertIn("references/runtimes.md", loop)
        self.assertIn("references/types/3d.md", loop)


if __name__ == "__main__":
    unittest.main()
