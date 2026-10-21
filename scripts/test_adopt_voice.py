"""Tests for adopt_voice.py. Fakes replace ffmpeg, ffprobe and Whisper.

The fake "audio" file's text is its spoken words: to_wav copies it, transcribe splits it.
"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import adopt_voice as av

SCRIPT = """# SCRIPT

**Voice:** x

## Line 0 — Intro (Frame 0)

**Time:** 0.0 – 3.0s
**Delivery:** warm

    Hello there team.

### Line 1 — Mid (frame 1)

\tShipped the thing.

## Line 2 — End (Frame 2)

    Next up is more.
"""


def fake_to_wav(src, dst):
    if Path(src).read_text() == "BAD":
        raise RuntimeError("cannot decode")
    Path(dst).write_text(Path(src).read_text())


def fake_probe(wav):
    return 1.0 + 0.5 * len(Path(wav).read_text().split())


def fake_transcribe(wav):
    return [{"text": t, "start": i * 0.5, "end": i * 0.5 + 0.4}
            for i, t in enumerate(Path(wav).read_text().split())]


class Base(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.p = Path(self._td.name)
        (self.p / "SCRIPT.md").write_text(SCRIPT)

    def run_main(self, *args):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = av.main([str(self.p), *args], to_wav=fake_to_wav,
                           probe_duration=fake_probe, transcribe=fake_transcribe)
        return code, err.getvalue()

    def voice_in(self, name, text):
        d = self.p / "voice-in"
        d.mkdir(exist_ok=True)
        (d / name).write_text(text)

    def three_files(self):
        self.voice_in("00.mp3", "hello there team")
        self.voice_in("01.wav", "shipped the thing")
        self.voice_in("02.m4a", "next up is more")

    def meta(self, name="audio_meta.json"):
        return json.loads((self.p / name).read_text())


class AdoptTests(Base):
    def test_three_lines_write_wavs_and_both_metas(self):
        self.three_files()
        code, err = self.run_main()
        self.assertEqual(code, 0, err)
        for n in ("00", "01", "02"):
            self.assertTrue((self.p / "assets/voice" / f"{n}.wav").exists())
        m = self.meta()
        self.assertEqual((m["bgm"], m["bgm_pending"], m["sfx"]), (None, False, []))
        self.assertEqual([v["frame"] for v in m["voices"]], [0, 1, 2])
        v0 = m["voices"][0]
        self.assertEqual(v0["path"], "assets/voice/00.wav")
        self.assertEqual(v0["duration_s"], 2.5)
        self.assertEqual([w["id"] for w in v0["words"]], ["w0", "w1", "w2"])
        self.assertEqual(v0["words"][1], {"id": "w1", "text": "there", "start": 0.5, "end": 0.9})
        e = self.meta("audio_engine_meta.json")
        self.assertEqual([v["id"] for v in e["voices"]], ["00", "01", "02"])
        self.assertNotIn("frame", e["voices"][0])
        self.assertEqual(e["voices"][0]["words"], v0["words"])

    def test_rerun_with_one_replaced_file(self):
        self.three_files()
        self.run_main()
        self.voice_in("01.wav", "shipped it")
        code, err = self.run_main()
        self.assertEqual(code, 0, err)
        self.assertEqual((self.p / "assets/voice/01.wav").read_text(), "shipped it")
        for name, key in (("audio_meta.json", "frame"), ("audio_engine_meta.json", "id")):
            v = [x for x in self.meta(name)["voices"] if x[key] in (1, "01")][0]
            self.assertEqual([w["text"] for w in v["words"]], ["shipped", "it"])

    def test_rerun_keeps_sfx_and_host_entries(self):
        self.three_files()
        self.run_main()
        pl = self.meta()
        pl["bgm"] = {"path": "assets/bed.mp3", "source": "host"}
        pl["sfx"] = [{"frame": 0, "file": "assets/a.wav"},
                     {"frame": 1, "file": "assets/b.wav", "source": "host"}]
        (self.p / "audio_meta.json").write_text(json.dumps(pl))
        en = self.meta("audio_engine_meta.json")
        en["sfx"] = [{"id": "00", "file": "assets/a.wav"}]
        (self.p / "audio_engine_meta.json").write_text(json.dumps(en))
        code, err = self.run_main()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.meta()["sfx"], pl["sfx"])
        self.assertEqual(self.meta()["bgm"], pl["bgm"])
        self.assertEqual(self.meta("audio_engine_meta.json")["sfx"], en["sfx"])

    def test_parse_accepts_lowercase_frame_tabs_and_skips_bold_rows(self):
        self.assertEqual(av.parse_script(SCRIPT),
                         [(0, "Hello there team."), (1, "Shipped the thing."), (2, "Next up is more.")])

    def test_missing_file_names_frame_and_writes_no_meta(self):
        self.voice_in("00.mp3", "hello there team")
        self.voice_in("02.m4a", "next up is more")
        code, err = self.run_main()
        self.assertNotEqual(code, 0)
        self.assertIn("frame 1", err)
        self.assertFalse((self.p / "audio_meta.json").exists())
        self.assertFalse((self.p / "audio_engine_meta.json").exists())

    def test_two_files_for_one_frame(self):
        self.three_files()
        self.voice_in("02.wav", "next up is more")
        code, err = self.run_main()
        self.assertNotEqual(code, 0)
        self.assertIn("frame 2", err)

    def test_no_words_and_unreadable(self):
        self.voice_in("00.mp3", "")
        self.voice_in("01.wav", "BAD")
        self.voice_in("02.m4a", "next up is more")
        code, err = self.run_main()
        self.assertNotEqual(code, 0)
        self.assertIn("frame 0", err)
        self.assertIn("no words", err)
        self.assertIn("frame 1", err)
        self.assertNotIn("frame 2", err)
        self.assertFalse((self.p / "audio_meta.json").exists())

    def test_heading_without_text(self):
        (self.p / "SCRIPT.md").write_text(SCRIPT + "\n## Line 3 — Empty (Frame 3)\n\n**Time:** 1s\n")
        self.three_files()
        code, err = self.run_main()
        self.assertNotEqual(code, 0)
        self.assertIn("frame 3", err)
        self.assertFalse((self.p / "audio_meta.json").exists())


STORYBOARD = """---
format: 1920x1080
---

## Frame 0 — Intro

- voiceover: "Hello there team."
- duration: 3s

## Frame 1 — Silent

- voiceover: ""
- duration: 2s

## Frame 2 — End

- voiceover: "Next up is more."
"""


class CheckTests(Base):
    def project(self, storyboard=STORYBOARD, frames=(0, 2)):
        (self.p / "STORYBOARD.md").write_text(storyboard)
        (self.p / "assets/voice").mkdir(parents=True, exist_ok=True)
        voices = []
        for f in frames:
            (self.p / f"assets/voice/{f:02d}.wav").write_text("x")
            voices.append({"frame": f, "path": f"assets/voice/{f:02d}.wav", "duration_s": 1,
                           "words": [{"id": "w0", "text": "a", "start": 0, "end": 1}]})
        (self.p / "audio_meta.json").write_text(json.dumps({"voices": voices}))

    def test_passes_with_silent_frame(self):
        self.project()
        code, err = self.run_main("--check")
        self.assertEqual(code, 0, err)

    def test_fails_naming_exactly_the_bad_frames(self):
        self.project()
        m = self.meta()
        m["voices"][0]["words"] = []
        (self.p / "audio_meta.json").write_text(json.dumps(m))
        (self.p / "assets/voice/02.wav").unlink()
        code, err = self.run_main("--check")
        self.assertNotEqual(code, 0)
        self.assertIn("frame 0", err)
        self.assertIn("frame 2", err)
        self.assertNotIn("frame 1", err)

    def test_missing_voice_entry_and_scene_headings(self):
        self.project(STORYBOARD.replace("## Frame", "### Scene"), frames=(0,))
        code, err = self.run_main("--check")
        self.assertNotEqual(code, 0)
        self.assertIn("frame 2", err)
        self.assertNotIn("frame 0", err)
        self.assertNotIn("frame 1", err)


INTRO_SCRIPT = """## Line 1 — Intro (Frame 1)
**Delivery:** warm
    This is a short tour of the new upload flow.
## Line 2 — Middle (Frame 2)
    Shipped the thing.
## Line 3 — End (Frame 3)
    Next up is more.
"""

INTRO_STORYBOARD = """## Frame 1 — Intro
- on_screen_title: "The New Upload Flow"
- voiceover: "This is a short tour of the new upload flow."
## Frame 2 — Middle
## Frame 3 — End
"""


class CheckScriptTests(Base):
    def setUp(self):
        super().setUp()
        (self.p / "SCRIPT.md").write_text(INTRO_SCRIPT)
        (self.p / "STORYBOARD.md").write_text(INTRO_STORYBOARD)

    def check(self, user_script, storyboard=INTRO_STORYBOARD):
        (self.p / "user_script.txt").write_text(user_script)
        (self.p / "STORYBOARD.md").write_text(storyboard)
        return self.run_main("--check-script")

    def test_passes_with_other_rows_and_punctuation(self):
        code, err = self.check(INTRO_SCRIPT.replace("Shipped the thing.", "Shipped -- THE thing!")
                               .replace("## Line 3 — End (Frame 3)", "## Line 3 — End (Frame 3)\n**Time:** 9s"))
        self.assertEqual(code, 0, err)

    def test_one_word_differs(self):
        code, err = self.check(INTRO_SCRIPT.replace("is more", "is less"))
        self.assertNotEqual(code, 0)
        self.assertIn("frame 3", err)
        self.assertIn("less", err)
        self.assertNotIn("frame 1", err)

    def test_extra_line_in_script(self):
        code, err = self.check(INTRO_SCRIPT.split("## Line 3")[0])
        self.assertNotEqual(code, 0)
        self.assertIn("3 lines", err)
        self.assertIn("2 lines", err)

    def test_script_without_intro(self):
        code, err = self.check(INTRO_SCRIPT.replace("Intro", "Hook"))
        self.assertNotEqual(code, 0)
        self.assertIn("Line 1 — Intro (Frame 1)", err)

    def test_intro_longer_than_one_short_sentence(self):
        long_intro = "This is a short tour of the new upload flow " + "and more " * 8
        (self.p / "SCRIPT.md").write_text(INTRO_SCRIPT.replace("This is a short tour of the new upload flow.", long_intro))
        code, err = self.check(INTRO_SCRIPT.replace("This is a short tour of the new upload flow.", long_intro))
        self.assertNotEqual(code, 0)
        self.assertIn("at most 20 words", err)

    def test_storyboard_intro_without_title(self):
        code, err = self.check(INTRO_SCRIPT, INTRO_STORYBOARD.replace('"The New Upload Flow"', '""'))
        self.assertNotEqual(code, 0)
        self.assertIn("on_screen_title", err)

    def test_title_on_another_frame_does_not_count(self):
        moved = INTRO_STORYBOARD.replace('- on_screen_title: "The New Upload Flow"\n', "") \
            .replace("## Frame 2 — Middle", '## Frame 2 — Middle\n- on_screen_title: "X"')
        code, err = self.check(INTRO_SCRIPT, moved)
        self.assertNotEqual(code, 0)
        self.assertIn("on_screen_title", err)


if __name__ == "__main__":
    unittest.main()
