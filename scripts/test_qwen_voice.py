"""Tests for qwen_voice.py with a fake synthesizer: no MLX, no model download."""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qwen_voice  # noqa: E402

SCRIPT = """# SCRIPT

**Voice:** Qwen3-TTS · Aiden

## Line 0 — Intro (Frame 0)

**Time:** 0.0 – 4.0s

    Hello there.

## Line 1 — Middle (Frame 1)

    The middle line.

## Line 2 — End (Frame 2)

    Goodbye.
"""


class Fake:
    def __init__(self):
        self.loads, self.calls = 0, []

    def make(self, model, speaker, language, instruct):
        self.loads += 1
        self.args = (model, speaker, language, instruct)

        def synthesize(text, out):
            self.calls.append(text)
            Path(out).write_bytes(b"RIFF" + text.encode())
        return synthesize


class QwenVoiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p / "SCRIPT.md").write_text(SCRIPT)
        self.fake = Fake()

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, *args):
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = qwen_voice.main([str(self.p), *args], make_synthesizer=self.fake.make)
        return code, err.getvalue()

    def test_voices_every_line_with_one_model_load(self):
        code, _ = self.run_main()
        self.assertEqual(code, 0)
        self.assertEqual(self.fake.loads, 1)
        self.assertEqual(self.fake.calls, ["Hello there.", "The middle line.", "Goodbye."])
        self.assertEqual(sorted(f.name for f in (self.p / "voice-in").iterdir()), ["00.wav", "01.wav", "02.wav"])
        self.assertEqual(self.fake.args[1:3], ("Aiden", "English"))

    def test_frames_option_voices_only_those(self):
        (self.p / "voice-in").mkdir()
        (self.p / "voice-in/00.wav").write_bytes(b"keep")
        code, _ = self.run_main("--frames", "1", "--speaker", "Ryan")
        self.assertEqual(code, 0)
        self.assertEqual(self.fake.calls, ["The middle line."])
        self.assertEqual((self.p / "voice-in/00.wav").read_bytes(), b"keep")
        self.assertEqual(self.fake.args[1], "Ryan")

    def test_replaces_a_file_of_another_format(self):
        (self.p / "voice-in").mkdir()
        (self.p / "voice-in/02.mp3").write_bytes(b"old")
        (self.p / "voice-in/02.txt").write_text("not audio, left alone")
        self.assertEqual(self.run_main("--frames", "2")[0], 0)
        self.assertEqual(sorted(f.name for f in (self.p / "voice-in").iterdir()), ["02.txt", "02.wav"])

    def test_unknown_frame_fails_before_loading_the_model(self):
        code, err = self.run_main("--frames", "7")
        self.assertEqual(code, 1)
        self.assertIn("frame 7", err)
        self.assertEqual(self.fake.loads, 0)
        self.assertFalse((self.p / "voice-in").exists())

    def test_heading_without_text_fails(self):
        (self.p / "SCRIPT.md").write_text(SCRIPT + "\n## Line 3 — Empty (Frame 3)\n\n**Time:** 9s\n")
        code, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("frame 3", err)
        self.assertEqual(self.fake.calls, [])

    def test_say_respells_only_the_synthesized_text(self):
        (self.p / "SCRIPT.md").write_text(SCRIPT.replace("The middle line.", "Two KBs here."))
        code, _ = self.run_main("--frames", "1", "--say", "KBs=K-Bs")
        self.assertEqual(code, 0)
        self.assertEqual(self.fake.calls, ["Two K-Bs here."])
        self.assertIn("Two KBs here.", (self.p / "SCRIPT.md").read_text())

    def test_say_is_whole_word_only(self):
        (self.p / "SCRIPT.md").write_text(SCRIPT.replace("The middle line.", "Two KBs and a KB."))
        self.assertEqual(self.run_main("--frames", "1", "--say", "KB=kay-bee")[0], 0)
        self.assertEqual(self.fake.calls, ["Two KBs and a kay-bee."])

    def test_say_without_equals_fails_before_loading_the_model(self):
        for bad in ("bad", "=x", "x="):
            code, err = self.run_main("--say", bad)
            self.assertEqual(code, 1)
            self.assertIn(f"--say needs WRITTEN=SPOKEN: {bad}", err)
        self.assertEqual(self.fake.loads, 0)

    def test_missing_script(self):
        (self.p / "SCRIPT.md").unlink()
        code, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("SCRIPT.md not found", err)


if __name__ == "__main__":
    unittest.main()
