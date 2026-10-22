"""Tests for finish.py with a fake runner: no hyperframes, no ffmpeg, no render."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finish  # noqa: E402

STORYBOARD = """## Frame 1 — Intro
- src: compositions/intro.html
## Frame 2 — Feed
- src: compositions/feed.html
"""


class Fake:
    """Records every command; `fail` is a substring of a command line that returns 1; files appear as ffmpeg/render make them."""

    def __init__(self, fail=None):
        self.cmds, self.fail = [], fail

    def __call__(self, cmd, cwd):
        line = " ".join(cmd)
        self.cmds.append(line)
        if self.fail and self.fail in line:
            return 1
        cwd = Path(cwd)
        if "render" in cmd:
            (cwd / "renders").mkdir(exist_ok=True)
            (cwd / "renders/video.raw.mp4").write_text("raw")
        if cmd[0] == "ffmpeg":
            Path(cmd[-1]).write_text("out")
        return 0

    def names(self):
        return [c.split(" -I ")[1].split(" ")[0].rsplit("/", 1)[-1] if " -I " in c else c.split(" ")[2] for c in self.cmds]


class FinishTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.p = Path(self._td.name)
        (self.p / "compositions").mkdir()
        (self.p / "assets/voice").mkdir(parents=True)
        (self.p / "STORYBOARD.md").write_text(STORYBOARD)
        (self.p / "RUN.md").write_text("# Run\n\n## Answers\n- target: 60-90\n- pause: 1.5s\n")
        voices = []
        for frame, name in ((1, "intro"), (2, "feed")):
            (self.p / f"assets/voice/{frame:02d}.wav").write_text(f"voice {frame}")
            (self.p / f"compositions/{name}.html").write_text("<template></template>")
            voices.append({"frame": frame, "path": f"assets/voice/{frame:02d}.wav", "duration_s": 10.0, "words": []})
        (self.p / "audio_meta.json").write_text(json.dumps({"voices": voices}))

    def run_finish(self, *args, fake=None, probe=lambda _: 20.0):
        fake = fake or Fake()
        err, out = io.StringIO(), io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            code = finish.main([str(self.p), *args], runner=fake, probe=probe)
        return code, out.getvalue(), err.getvalue(), fake

    def test_review_runs_the_steps_in_order_on_every_scene_the_first_time(self):
        code, out, err, fake = self.run_finish("--review")
        self.assertEqual(code, 0, err)
        self.assertEqual(fake.names(), ["adopt_voice.py", "adopt_voice.py", "build_index.py", "check", "snapshot"])
        self.assertIn("--pause 1.5", fake.cmds[0])
        self.assertIn("--check", fake.cmds[1])
        self.assertIn("--at 9.5,19.5 --no-end", fake.cmds[4])
        self.assertIn("changed: intro, feed", out)

    def test_review_looks_only_at_what_changed_since_the_last_run(self):
        self.run_finish("--review")
        code, out, _, fake = self.run_finish("--review")
        self.assertEqual(code, 0)
        self.assertEqual(len(fake.cmds), 3)  # adopt, voice check, build: nothing to look at
        self.assertIn("no scene changed", out)
        (self.p / "assets/voice/02.wav").write_text("a new take")
        _, out, _, fake = self.run_finish("--review")
        self.assertIn("changed: feed", out)
        self.assertIn("--at 19.5 --no-end", fake.cmds[-1])
        (self.p / "compositions/intro.html").write_text("<template>edited</template>")
        _, out, _, fake = self.run_finish("--review")
        self.assertIn("changed: intro", out)
        self.assertNotIn("feed", out.split("changed:")[1].split("\n")[0])

    def test_facts_change_marks_every_scene(self):
        self.run_finish("--review")
        (self.p / "facts.json").write_text('{"ticket": "T-2"}')
        self.assertIn("changed: intro, feed", self.run_finish("--review")[1])

    def test_a_failing_step_stops_the_run_and_is_named(self):
        code, _, err, fake = self.run_finish("--review", fake=Fake(fail="--check"))
        self.assertEqual(code, 1)
        self.assertIn("step 'voice check' failed", err)
        self.assertEqual(len(fake.cmds), 2)  # nothing after the failed step

    def test_a_failing_layout_check_stops_before_the_stills_and_forgets_nothing(self):
        code, _, err, fake = self.run_finish("--review", fake=Fake(fail="hyperframes check"))
        self.assertEqual(code, 1)
        self.assertIn("layout check failed", err)
        self.assertFalse(any("snapshot" in c for c in fake.cmds))
        self.assertEqual(finish.read_state(self.p), {})  # the next run looks at everything again

    def test_blur_lint_fails_a_filter_and_allows_the_fade_helper(self):
        (self.p / "compositions/feed.html").write_text('f.blur(tl, "#a", 0.1);\ntl.to("#a", { filter: "blur(8px)" });')
        code, _, err, fake = self.run_finish("--review")
        self.assertEqual(code, 1)
        self.assertIn("step 'fast-capture lint' failed", err)
        self.assertIn("compositions/feed.html:2", err)
        self.assertNotIn("feed.html:1", err)
        self.assertEqual(len(fake.cmds), 3)

    def test_lint_fails_a_tween_callback_that_edits_the_page(self):
        (self.p / "compositions/feed.html").write_text("tl.fromTo(st, { n: 0 }, { n: 9, onUpdate: () => { el.textContent = 'x'; } });")
        code, _, err, _ = self.run_finish("--review")
        self.assertEqual(code, 1)
        self.assertIn("onUpdate callbacks are not seek-safe", err)
        self.assertIn("compositions/feed.html:1", err)

    def test_blur_lint_catches_css_filters_in_index_html(self):
        (self.p / "index.html").write_text("<style>.x { backdrop-filter: blur(var(--r)); }</style>")
        self.assertEqual(self.run_finish("--review")[0], 1)

    def test_final_renders_once_normalizes_checks_and_records(self):
        code, out, err, fake = self.run_finish("--final")
        self.assertEqual(code, 0, err)
        self.assertEqual(fake.names()[:4], ["adopt_voice.py", "adopt_voice.py", "build_index.py", "render"])
        self.assertIn("render . -o renders/video.raw.mp4", fake.cmds[3])
        self.assertIn("qc_video.py", fake.cmds[4])
        self.assertIn("--normalize", fake.cmds[4])
        self.assertIn("--check 60-90", fake.cmds[5])
        self.assertTrue(all(c.startswith("ffmpeg") for c in fake.cmds[6:]))
        self.assertIn("-ss 6.0", fake.cmds[6])  # 60% of frame 1's 10 s
        self.assertTrue((self.p / "renders/video.mp4").exists())
        self.assertFalse((self.p / "renders/video.cover.mp4").exists())
        run_md = (self.p / "RUN.md").read_text()
        self.assertIn("- sync: voice total 20.000 s, MP4 20.000 s, difference 0.000 s", run_md)
        self.assertIn("- qc: pass", run_md)
        self.assertIn("- cover: 6.0 s", run_md)
        self.assertEqual(sorted(finish.read_state(self.p)), ["_facts", "feed", "intro"])
        self.assertIn("done in", out)

    def test_final_fills_the_caption_from_facts(self):
        (self.p / "facts.json").write_text('{"ticket": "T-2"}')
        (self.p / "renders").mkdir()
        (self.p / "renders/share-copy.template.txt").write_text("Ticket {{ticket}} lands next week.")
        self.assertEqual(self.run_finish("--final")[0], 0)
        self.assertEqual((self.p / "renders/share-copy.txt").read_text(), "Ticket T-2 lands next week.")

    def test_final_stops_before_rendering_when_the_build_fails(self):
        code, _, err, fake = self.run_finish("--final", fake=Fake(fail="build_index.py"))
        self.assertEqual(code, 1)
        self.assertIn("step 'build index.html' failed", err)
        self.assertFalse(any("render" in c for c in fake.cmds))

    def test_final_reports_a_sync_difference_above_two_seconds(self):
        self.run_finish("--final", probe=lambda f: 25.0)
        self.assertIn("report it before calling the run done", (self.p / "RUN.md").read_text())

    def test_final_needs_a_target_length(self):
        (self.p / "RUN.md").write_text("# Run\n")
        code, _, err, fake = self.run_finish("--final")
        self.assertEqual(code, 1)
        self.assertIn("--target", err)
        self.assertEqual(fake.cmds, [])
        self.assertEqual(self.run_finish("--final", "--target", "75")[0], 0)

    def test_usage(self):
        for bad in ([], ["--review", "--final"], ["--pause"], ["--pause", ""]):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(finish.main([str(self.p), *bad], runner=Fake()), 1)
            self.assertIn("usage: finish.py", err.getvalue())


if __name__ == "__main__":
    unittest.main()
