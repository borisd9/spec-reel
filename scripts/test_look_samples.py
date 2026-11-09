"""Tests for look_samples.py: one-frame sample projects per look, checked before any render, rendered one by one."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import look_samples as ls  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INTRO = '<template><script>f.rise(tl, "#a", at("tool"));</script></template>'


def voice(frame, texts, duration=5.0):
    words = [{"id": f"w{i}", "text": t, "start": round(i * 0.5, 3), "end": round(i * 0.5 + 0.4, 3)}
             for i, t in enumerate(texts)]
    return {"frame": frame, "path": f"assets/voice/{frame:02d}.wav", "duration_s": duration, "words": words}


class LookSamplesTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.p = Path(self._td.name)
        self.calls, self.result = [], 0
        meta = {"voices": [voice(1, ["Meet", "the", "tool."]), voice(2, ["More", "words", "here."])]}
        (self.p / "audio_meta.json").write_text(json.dumps(meta))
        (self.p / "assets/voice").mkdir(parents=True)
        (self.p / "assets/voice/01.wav").write_bytes(b"wav")
        (self.p / "compositions").mkdir()
        (self.p / "compositions/intro.html").write_text("run intro")
        (self.p / "build").mkdir()
        (self.p / "build/marker").write_text("run build")
        (self.p / "index.html").write_text("run index")
        (self.p / "hyperframes.json").write_text("{}")
        (self.p / "meta.json").write_text("{}")
        for name in ("1-paper", "2-blueprint"):
            look = self.p / "looks" / name
            (look / "compositions").mkdir(parents=True)
            (look / "index.template.html").write_text((ROOT / "assets/index.template.html").read_text())
            (look / "compositions/intro.html").write_text(INTRO)

    def runner(self, cmd, cwd):
        self.calls.append((cmd, cwd))
        return self.result

    def main_err(self, *args):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = ls.main([str(self.p), *args], runner=self.runner)
        return code, err.getvalue()

    def main(self, *args):
        return self.main_err(*args)[0]

    def test_builds_one_frame_sample_per_look_and_renders_each(self):
        self.assertEqual(self.main(), 0)
        self.assertEqual([c[1].parent.name for c in self.calls], ["1-paper", "2-blueprint"])
        for name in ("1-paper", "2-blueprint"):
            sample = self.p / "looks" / name / "sample"
            meta = json.loads((sample / "audio_meta.json").read_text())
            self.assertEqual([v["frame"] for v in meta["voices"]], [1])
            self.assertTrue((sample / "assets/voice/01.wav").exists())
            self.assertIn('data-composition-id="intro"', (sample / "index.html").read_text())
            self.assertIn(str(self.p / "looks" / name / "intro.mp4"), self.calls[["1-paper", "2-blueprint"].index(name)][0])

    def test_relative_project_dir_gives_an_absolute_output_path(self):
        cwd = os.getcwd()
        os.chdir(self.p)
        self.addCleanup(os.chdir, cwd)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ls.main(["."], runner=self.runner), 0)
        self.assertTrue(all(Path(c[0][-1]).is_absolute() for c in self.calls))

    def test_one_look_only(self):
        self.assertEqual(self.main("--look", "2-blueprint"), 0)
        self.assertEqual([c[1].parent.name for c in self.calls], ["2-blueprint"])
        self.assertFalse((self.p / "looks/1-paper/sample").exists())

    def test_no_audio_meta_fails_before_render(self):
        (self.p / "audio_meta.json").unlink()
        code, err = self.main_err()
        self.assertEqual(code, 1)
        self.assertIn("audio_meta.json", err)
        self.assertEqual(self.calls, [])

    def test_look_missing_intro_is_named(self):
        (self.p / "looks/2-blueprint/compositions/intro.html").unlink()
        code, err = self.main_err()
        self.assertEqual(code, 1)
        self.assertIn("2-blueprint", err)
        self.assertEqual(self.calls, [])

    def test_blur_in_look_template_fails_before_render(self):
        t = self.p / "looks/1-paper/index.template.html"
        t.write_text(t.read_text().replace("window.fx = {", 'window.fx = {\n  smear(tl, s, t) { tl.fromTo(s, {filter: "blur(4px)"}, {filter: "blur(0px)"}, t); },'))
        code, err = self.main_err()
        self.assertEqual(code, 1)
        self.assertIn("looks/1-paper/index.template.html", err)
        self.assertEqual(self.calls, [])

    def test_cue_on_a_word_the_intro_lacks_fails(self):
        (self.p / "looks/1-paper/compositions/intro.html").write_text('<template><script>at("missing");</script></template>')
        code, err = self.main_err()
        self.assertEqual(code, 1)
        self.assertIn('at("missing"', err)

    def test_failed_render_is_named(self):
        self.result = 1
        code, err = self.main_err()
        self.assertEqual(code, 1)
        self.assertIn("1-paper", err)

    def test_run_files_untouched(self):
        before = {f: f.read_bytes() for f in (self.p / "index.html", self.p / "compositions/intro.html", self.p / "build/marker")}
        self.main()
        for f, data in before.items():
            self.assertEqual(f.read_bytes(), data)

    def test_project_files_are_copied_when_present(self):
        self.main()
        sample = self.p / "looks/1-paper/sample"
        self.assertTrue((sample / "hyperframes.json").exists())
        self.assertTrue((sample / "meta.json").exists())
        self.assertFalse((sample / "package.json").exists())

    def test_rerun_replaces_the_sample(self):
        self.main()
        (self.p / "looks/1-paper/sample/stale.txt").write_text("x")
        self.main()
        self.assertFalse((self.p / "looks/1-paper/sample/stale.txt").exists())


if __name__ == "__main__":
    unittest.main()
