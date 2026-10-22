"""Tests for qc_video.py. Fakes replace ffprobe and ffmpeg."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import qc_video as qc

GOOD = {"streams": [{"codec_type": "video", "codec_name": "h264", "pix_fmt": "yuv420p", "width": 1920, "height": 1080},
                    {"codec_type": "audio", "codec_name": "aac"}], "duration": 75.0}


class QcTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.p = Path(self._td.name)
        (self.p / "renders").mkdir()
        (self.p / "renders/video.mp4").write_text("original")

    def run_main(self, *args, info=GOOD, black=(), loudnorm=None):
        err, out = io.StringIO(), io.StringIO()
        kw = {"loudnorm": loudnorm} if loudnorm else {}
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            code = qc.main([str(self.p), *args], probe=lambda v: info, black_spans=lambda v: list(black), **kw)
        return code, out.getvalue(), err.getvalue()

    def stream(self, **changes):
        video = {**GOOD["streams"][0], **changes}
        return {**GOOD, "streams": [video, GOOD["streams"][1]]}

    def test_good_video_passes(self):
        self.assertEqual(self.run_main("--check", "75"), (0, "qc: pass\n", ""))

    def test_each_problem_is_listed(self):
        info = {"streams": [{"codec_type": "video", "codec_name": "hevc", "pix_fmt": "yuv444p",
                             "width": 1280, "height": 720}], "duration": 40.0}
        code, _, err = self.run_main("--check", "75", info=info, black=[(0.0, 1.2)])
        self.assertEqual(code, 1)
        for want in ("not h264", "not yuv420p", "1280x720", "no audio stream", "black from 0.0s to 1.2s", "length 40.0s"):
            self.assertIn(want, err)

    def test_one_problem_only(self):
        code, _, err = self.run_main("--check", "75", info=self.stream(pix_fmt="yuv422p"))
        self.assertEqual((code, err.count("\n")), (1, 1))
        self.assertIn("not yuv420p", err)

    def test_length_tolerance_is_12_percent(self):
        self.assertEqual(self.run_main("--check", "75", info={**GOOD, "duration": 75 * 1.12 - 0.1})[0], 0)
        self.assertEqual(self.run_main("--check", "75", info={**GOOD, "duration": 75 * 1.12 + 0.1})[0], 1)
        self.assertEqual(self.run_main("--check", "75", info={**GOOD, "duration": 75 * 0.88 - 0.1})[0], 1)

    def test_blackdetect_output_is_parsed(self):
        out = "[blackdetect @ 0x1] black_start:1.5 black_end:2.75 black_duration:1.25\nother line\n"
        self.assertEqual([(float(a), float(b)) for a, b in qc.BLACK_RE.findall(out)], [(1.5, 2.75)])

    def test_missing_video_and_bad_usage(self):
        (self.p / "renders/video.mp4").unlink()
        self.assertIn("not found", self.run_main("--check", "75")[2])
        for bad in ([], ["--check"], ["--check", "abc"], ["--check", "0"], ["--check", "-5"], ["--check", "nan"]):
            code, _, err = self.run_main(*bad)
            self.assertEqual(code, 1, bad)
            self.assertIn("usage: qc_video.py", err)

    def test_normalize_replaces_the_video_through_a_temp_file(self):
        def fake(src, dst):
            self.assertEqual(Path(dst).name, "video.norm.mp4")
            Path(dst).write_text("normalized " + Path(src).read_text())
        code, out, _ = self.run_main("--normalize", loudnorm=fake)
        self.assertEqual(code, 0)
        self.assertEqual((self.p / "renders/video.mp4").read_text(), "normalized original")
        self.assertEqual([f.name for f in (self.p / "renders").iterdir()], ["video.mp4"])

    def test_failed_normalize_keeps_the_original(self):
        def fake(src, dst):
            Path(dst).write_text("half")
            raise RuntimeError("boom")
        code, _, err = self.run_main("--normalize", loudnorm=fake)
        self.assertEqual(code, 1)
        self.assertIn("boom", err)
        self.assertEqual((self.p / "renders/video.mp4").read_text(), "original")
        self.assertEqual([f.name for f in (self.p / "renders").iterdir()], ["video.mp4"])


if __name__ == "__main__":
    unittest.main()
