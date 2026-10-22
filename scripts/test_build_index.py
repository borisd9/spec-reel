"""Tests for build_index.py: scene ids from the storyboard, cues by word text, facts, the files it supplies."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_index as bi  # noqa: E402

STORYBOARD = """## Frame 1 — Intro
- src: compositions/intro.html
- voiceover: "x"
## Frame 2 — Feed
- scene_job: change
- src: compositions/feed.html
"""


def voice(frame, texts, duration=5.0):
    words = [{"id": f"w{i}", "text": t, "start": round(i * 0.5, 3), "end": round(i * 0.5 + 0.4, 3)}
             for i, t in enumerate(texts)]
    return {"frame": frame, "path": f"assets/voice/{frame:02d}.wav", "duration_s": duration, "words": words}


class BuildIndexTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.p = Path(self._td.name)
        (self.p / "compositions").mkdir()
        (self.p / "STORYBOARD.md").write_text(STORYBOARD)
        self.write_meta(["Meet", "the", "tool."], ["The", "feed", "gets", "a", "draft,", "then", "a", "Draft."])
        (self.p / "compositions/intro.html").write_text("<template></template>")
        self.scene("feed", 'f.rise(tl, "#a", at("feed")); f.rise(tl, "#b", at("draft", 2));')

    def write_meta(self, first, second):
        (self.p / "audio_meta.json").write_text(json.dumps({"voices": [voice(1, first), voice(2, second, 7.0)]}))

    def scene(self, name, body):
        (self.p / f"compositions/{name}.html").write_text(f"<template><script>{body}</script></template>")

    def build(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            return bi.main([str(self.p)]), err.getvalue()

    def words_in_index(self):
        html = (self.p / "index.html").read_text()
        return json.loads(html.split("window.__WORDS = ")[1].split(";\n")[0])

    def test_scene_ids_come_from_the_storyboard_in_frame_order(self):
        self.assertEqual(bi.scene_ids(STORYBOARD), {1: "intro", 2: "feed"})

    def test_builds_hosts_audio_and_word_text_with_timings(self):
        code, err = self.build()
        self.assertEqual(code, 0, err)
        html = (self.p / "index.html").read_text()
        self.assertIn('id="feed" data-composition-id="feed" data-composition-src="compositions/feed.html" data-start="5.000" '
                      'data-duration="7.000"', html)
        self.assertIn('id="vo-02" class="clip" src="assets/voice/02.wav" data-start="5.000"', html)
        self.assertIn('data-duration="12.000" data-width="1920"', html)
        self.assertEqual(self.words_in_index()["feed"][1], ["feed", 0.5])
        for placeholder in ("TOTAL", "HOSTS", "AUDIO", "WORDS", "VO", "DUR", "FACTS", "FACT_VARS"):
            self.assertNotIn(f"%{placeholder}%", html)

    def test_at_resolves_by_text_after_words_are_inserted_before_it(self):
        words = voice(2, ["The", "feed", "gets", "a", "draft,", "then", "a", "Draft."])["words"]
        self.assertEqual(bi.find_word(words, "draft", 2), 3.5)
        longer = voice(2, ["Today", "the", "new", "feed", "gets", "a", "draft,", "then", "a", "Draft."])["words"]
        self.assertEqual(bi.find_word(longer, "feed"), 1.5)
        self.assertEqual(bi.find_word(longer, "draft", 2), 4.5)
        self.assertIsNone(bi.find_word(longer, "draft", 3))

    def test_a_cue_on_a_missing_word_fails_the_build(self):
        self.scene("feed", 'f.rise(tl, "#a", at("queue")); f.rise(tl, "#b", at("draft", 3));')
        code, err = self.build()
        self.assertEqual(code, 1)
        self.assertIn('feed: at("queue", 1)', err)
        self.assertIn('feed: at("draft", 3)', err)
        self.assertFalse((self.p / "index.html").exists())

    def test_comments_and_array_at_are_not_cues(self):
        self.scene("feed", '// at("nothing")\n<!-- at("nothing") -->\nconst x = list.at(0); const f = format(1);')
        self.assertEqual(self.build()[0], 0)

    def test_frames_and_scenes_must_match(self):
        (self.p / "STORYBOARD.md").write_text(STORYBOARD + "## Frame 3 — More\n- src: compositions/more.html\n")
        code, err = self.build()
        self.assertEqual(code, 1)
        self.assertIn("frames [1, 2]", err)

    def test_missing_scene_file_is_named(self):
        (self.p / "compositions/feed.html").unlink()
        code, err = self.build()
        self.assertEqual(code, 1)
        self.assertIn("compositions/feed.html not found", err)

    def test_facts_become_variables_and_a_js_object(self):
        (self.p / "facts.json").write_text(json.dumps({"ticket": "T-12", "title": "It's \"quoted\""}))
        self.assertEqual(self.build()[0], 0)
        html = (self.p / "index.html").read_text()
        self.assertIn('"id": "ticket", "type": "string", "label": "ticket", "default": "T-12"'.replace('"', "&quot;"), html)
        self.assertIn('window.__FACTS = {"ticket":"T-12"', html)

    def test_supplies_fonts_and_progress_strip_without_overwriting(self):
        (self.p / "compositions/progress.html").write_text("mine")
        self.assertEqual(self.build()[0], 0)
        self.assertTrue((self.p / "assets/fonts/space-grotesk-600.woff2").is_file())
        self.assertEqual((self.p / "compositions/progress.html").read_text(), "mine")

    def test_a_run_can_keep_its_own_template(self):
        (self.p / "build").mkdir()
        (self.p / "build/index.template.html").write_text("<body>mine %TOTAL% %HOSTS% %AUDIO% %WORDS% %VO% %DUR% %FACTS% %FACT_VARS%")
        self.assertEqual(self.build()[0], 0)
        self.assertTrue((self.p / "index.html").read_text().startswith("<body>mine 12.000"))

    def test_the_template_has_no_css_blur(self):
        template = (bi.SKILL / "assets/index.template.html").read_text()
        self.assertNotIn("filter:", template.split("<style>")[0])
        self.assertNotRegex(template, r"blur\(\s*\d")


if __name__ == "__main__":
    unittest.main()
