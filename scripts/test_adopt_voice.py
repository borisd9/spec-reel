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


def fake_to_wav(src, dst, pad_s=0.0):
    if Path(src).read_text() == "BAD":
        raise RuntimeError("cannot decode")
    Path(dst).write_text(Path(src).read_text() + (f"\nPAD {pad_s}" if pad_s > 0 else ""))


def spoken(wav):
    """The fake wav's words and its padding, split at the PAD marker line."""
    text, _, pad = Path(wav).read_text().partition("\nPAD ")
    return text.split(), float(pad or 0)


def fake_probe(wav):
    words, pad = spoken(wav)
    return 1.0 + 0.5 * len(words) + pad


def fake_transcribe(wav):
    return [{"text": t, "start": i * 0.5, "end": i * 0.5 + 0.4} for i, t in enumerate(spoken(wav)[0])]


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
            # the words are the script's, on the timings of the replaced file ("it" is 2 of 3 tokens)
            self.assertEqual([w["text"] for w in v["words"]], ["Shipped", "the", "thing."])
            self.assertEqual(v["words"][-1]["end"], 0.9)
        self.assertEqual([w["text"] for w in json.loads((self.p / "voice_heard.json").read_text())["1"]],
                         ["shipped", "it"])

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


class SpeechTests(Base):
    def misheard(self):
        self.three_files()
        self.voice_in("01.wav", "shipped the thang")

    def test_adopt_keeps_script_words_saves_heard_and_reports(self):
        self.misheard()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = av.main([str(self.p)], to_wav=fake_to_wav, probe_duration=fake_probe, transcribe=fake_transcribe)
        self.assertEqual(code, 0)
        v1 = [v for v in self.meta()["voices"] if v["frame"] == 1][0]
        self.assertEqual([w["text"] for w in v1["words"]], ["Shipped", "the", "thing."])
        heard = json.loads((self.p / "voice_heard.json").read_text())
        self.assertEqual([w["text"] for w in heard["1"]], ["shipped", "the", "thang"])
        self.assertEqual(sorted(heard), ["0", "1", "2"])
        self.assertIn('frame 1: heard "thang" for "thing."', out.getvalue())
        self.assertIn("--check-speech", out.getvalue())

    def test_pause_pads_every_voice_but_the_last_frames(self):
        self.three_files()
        self.run_main()
        base = {v["frame"]: v["duration_s"] for v in self.meta()["voices"]}
        self.assertEqual(self.run_main("--pause", "1.5")[0], 0)
        got = {v["frame"]: v["duration_s"] for v in self.meta()["voices"]}
        self.assertEqual((got[0], got[1]), (base[0] + 1.5, base[1] + 1.5))
        self.assertEqual(got[2], base[2])

    def test_bad_pause_is_a_usage_failure(self):
        self.three_files()
        for bad in (["--pause", "abc"], ["--pause", "-1"], ["--pause"], ["--pause", "1", "--check"]):
            code, err = self.run_main(*bad)
            self.assertEqual(code, 1, bad)
            self.assertIn("usage: adopt_voice.py", err)
            self.assertIn("--pause SECONDS", err)

    def test_check_speech_passes_when_heard_equals_script(self):
        self.three_files()
        self.run_main()
        self.assertEqual(self.run_main("--check-speech"), (0, ""))

    def test_check_speech_names_the_frame_that_differs(self):
        self.misheard()
        self.run_main()
        code, err = self.run_main("--check-speech")
        self.assertEqual(code, 1)
        self.assertIn('frame 1: heard "thang" for "thing."', err)
        self.assertNotIn("frame 0", err)

    def test_check_speech_reports_unvoiced_frame(self):
        self.three_files()
        self.run_main()
        heard = json.loads((self.p / "voice_heard.json").read_text())
        del heard["2"]
        (self.p / "voice_heard.json").write_text(json.dumps(heard))
        code, err = self.run_main("--check-speech")
        self.assertEqual(code, 1)
        self.assertIn("frame 2: not voiced", err)

    def test_check_speech_without_voice_heard(self):
        code, err = self.run_main("--check-speech")
        self.assertEqual(code, 1)
        self.assertIn("voice_heard.json not found", err)

    def test_failed_adopt_writes_no_voice_heard(self):
        self.voice_in("00.mp3", "hello there team")
        self.run_main()
        self.assertFalse((self.p / "voice_heard.json").exists())


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


class AlignTests(unittest.TestCase):
    @staticmethod
    def heard(*texts):
        return [{"text": t, "start": i * 0.5, "end": i * 0.5 + 0.4} for i, t in enumerate(texts)]

    def test_equal_tokens_keep_script_punctuation_and_heard_timings(self):
        out = av.align_words("It checks, then ships.", self.heard("it", "checks", "then", "ships"))
        self.assertEqual([w["text"] for w in out], ["It", "checks,", "then", "ships."])
        self.assertEqual((out[1]["start"], out[1]["end"]), (0.5, 0.9))

    def test_misheard_word_gets_script_text_and_heard_timing(self):
        out = av.align_words("a reusable KB", self.heard("a", "resubil", "KB"))
        self.assertEqual([w["text"] for w in out], ["a", "reusable", "KB"])
        self.assertEqual((out[1]["start"], out[1]["end"]), (0.5, 0.9))

    def test_extra_heard_word_is_dropped(self):
        out = av.align_words("it ships", self.heard("it", "it", "ships"))
        self.assertEqual([w["text"] for w in out], ["it", "ships"])
        self.assertEqual(out[1]["start"], 1.0)

    def test_script_word_nobody_said_is_zero_length_after_the_previous(self):
        out = av.align_words("it really ships", self.heard("it", "ships"))
        self.assertEqual([w["text"] for w in out], ["it", "really", "ships"])
        self.assertEqual((out[1]["start"], out[1]["end"]), (out[0]["end"], out[0]["end"]))

    def test_two_script_tokens_for_one_heard_token_split_its_span(self):
        out = av.align_words("pre publish", self.heard("prepublish"))
        self.assertEqual([(w["start"], w["end"]) for w in out], [(0.0, 0.2), (0.2, 0.4)])

    def test_speech_diffs_reports_a_misheard_word(self):
        self.assertEqual(av.speech_diffs("we pre-publish it", self.heard("we", "pre-published", "it")),
                         [("pre-publish", "pre-published")])

    def test_speech_diffs_ignores_digits_for_number_words(self):
        self.assertEqual(av.speech_diffs("forty-five of ten", self.heard("45", "of", "10")), [])


class CacheTests(Base):
    """A file is transcribed once: the transcript is remembered by the WAV's hash."""

    def run_counting(self, *args):
        calls = []

        def counting(wav):
            calls.append(Path(wav).name)
            return fake_transcribe(wav)

        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            code = av.main([str(self.p), *args], to_wav=fake_to_wav, probe_duration=fake_probe, transcribe=counting)
        return code, calls

    def test_second_run_transcribes_nothing(self):
        self.three_files()
        self.assertEqual(self.run_counting(), (0, ["00.wav", "01.wav", "02.wav"]))
        self.assertEqual(self.run_counting(), (0, []))
        self.assertEqual(len(list((self.p / "voice-cache").glob("*.json"))), 3)

    def test_one_changed_file_transcribes_once(self):
        self.three_files()
        self.run_counting()
        self.voice_in("01.wav", "shipped it")
        self.assertEqual(self.run_counting(), (0, ["01.wav"]))
        self.assertEqual([v["words"][-1]["text"] for v in self.meta()["voices"]][1], "thing.")

    def test_a_new_pause_is_a_new_file(self):
        self.three_files()
        self.run_counting()
        self.assertEqual(self.run_counting("--pause", "1.0"), (0, ["00.wav", "01.wav"]))

    def test_no_words_is_not_cached(self):
        self.voice_in("00.mp3", "")
        self.voice_in("01.wav", "shipped the thing")
        self.voice_in("02.m4a", "next up is more")
        self.assertEqual(self.run_counting()[0], 1)
        self.assertEqual(len(list((self.p / "voice-cache").glob("*.json"))), 2)

    def test_adopt_says_how_many_came_from_the_cache(self):
        self.three_files()
        self.run_counting()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            av.main([str(self.p)], to_wav=fake_to_wav, probe_duration=fake_probe, transcribe=fake_transcribe)
        self.assertIn("(0 transcribed, 3 from voice-cache/)", out.getvalue())


class HeardTests(unittest.TestCase):
    """Spelling-only differences are not speech errors; a different word is."""

    @staticmethod
    def heard(text):
        return [{"text": t, "start": i * 0.5, "end": i * 0.5 + 0.4} for i, t in enumerate(text.split())]

    def diffs(self, script, heard):
        return av.speech_diffs(script, self.heard(heard))

    def test_spelling_only_differences_pass(self):
        for script, heard in (
                ("The PR 412 build ships on v8 with ids", "The PR412, build ships on V8 with IDs"),
                ("web V-eight index", "webv8 index"),
                ("the same doc id.", "the same docid."),
                ("Web search skips datahub", "WebSearch skips data hub"),
                ("forty-five of ten", "45 of 10"),
                ("sixty-nine percent of them", "69% of them"),
                ("a hundred per search", "100 per search"),
                ("two-second limit", "2 second limit"),
                ("the I-D field", "the ID field")):
            self.assertEqual(self.diffs(script, heard), [], script)

    def test_a_different_word_is_still_a_difference(self):
        self.assertEqual(self.diffs("Three readers returned zero drafts", "Three readers return 0 drafts"),
                         [("returned zero", "return 0")])
        self.assertEqual(self.diffs("PR 412 and ids", "PR412 and docs"), [("ids", "docs")])

    def test_only_the_real_error_is_listed_among_noise(self):
        script = "The PR 412 check ran on web V-eight, and three readers returned zero drafts, about sixty percent."
        heard = "The PR412 check ran on webv8, and three readers return 0 drafts, about 60%."
        self.assertEqual(self.diffs(script, heard), [("returned zero", "return 0")])

    def test_unrespell_maps_the_spoken_form_back(self):
        self.assertEqual(av.unrespell("the I-D of P R twelve on V-eight and I-Ds"), "the id of PR twelve on v8 and ids")

    def test_respell_is_whole_word_and_case_sensitive(self):
        self.assertEqual(av.respell("The id, ids, ID and idle PR on v8", av.BUILTIN_RESPELLINGS),
                         "The I-D, I-Ds, ID and idle P R on V-eight")


class ScriptSourceTests(Base):
    """SCRIPT.md is generated from user_script.txt, with {{facts}} filled in."""

    def setUp(self):
        super().setUp()
        self.three_files()
        (self.p / "user_script.txt").write_text(SCRIPT.replace("Shipped the thing.", "Shipped ticket {{ticket}}."))
        (self.p / "facts.json").write_text(json.dumps({"ticket": "412"}))

    def test_adopt_writes_script_md_from_the_script_and_the_facts(self):
        self.voice_in("01.wav", "shipped ticket 412")
        self.assertEqual(self.run_main()[0], 0)
        self.assertIn("Shipped ticket 412.", (self.p / "SCRIPT.md").read_text())
        self.assertNotIn("{{", (self.p / "SCRIPT.md").read_text())

    def test_a_fact_that_facts_json_lacks_is_named(self):
        (self.p / "user_script.txt").write_text(SCRIPT.replace("Shipped the thing.", "Shipped {{branch}}."))
        code, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("facts.json has no 'branch'", err)

    def test_editing_only_the_script_is_enough(self):
        self.run_main()
        (self.p / "user_script.txt").write_text(SCRIPT.replace("Shipped the thing.", "Shipped ticket {{ticket}} today."))
        self.run_main()
        self.assertIn("today", (self.p / "SCRIPT.md").read_text())


class RiskyTokenTests(unittest.TestCase):
    def test_lists_what_the_voice_may_misread(self):
        got = dict(av.risky_tokens("Fix kb_sync in x-12 for PR412, the dns and v8, then ids and the PR."))
        self.assertEqual(sorted(got), ["PR412", "dns", "kb_sync", "x-12"])

    def test_plain_words_are_not_listed(self):
        self.assertEqual(av.risky_tokens("It is a pre-publish check: the sync, a rhythm and the Hub."), [])


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
- scene_job: change
- before: "Uploads fail silently."
- after: "Uploads show an error."
## Frame 3 — End
- scene_job: next
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

    def test_a_stale_script_md_is_regenerated_not_compared(self):
        code, err = self.check(INTRO_SCRIPT.replace("is more", "is less"))
        self.assertEqual(code, 0, err)
        self.assertIn("Next up is less.", (self.p / "SCRIPT.md").read_text())

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

    def test_intro_counts_written_words_not_the_spoken_spelling(self):
        short = "This is a short tour of the P R two-twelve upload flow with the new retry checks and the pre-publish docs."
        self.assertGreater(len(av.words_of(short)), 20)  # the old count, which failed this intro
        for intro, ok in ((short, True), (short + " Also this.", False)):
            script = INTRO_SCRIPT.replace("This is a short tour of the new upload flow.", intro)
            (self.p / "SCRIPT.md").write_text(script)
            code, err = self.check(script)
            self.assertEqual(code, 0 if ok else 1, err)
            self.assertEqual("at most 20 words" in err, not ok)

    def test_risky_words_warn_without_failing(self):
        risky = INTRO_SCRIPT.replace("Shipped the thing.", "Shipped kb_sync on PR412.")
        (self.p / "SCRIPT.md").write_text(risky)
        code, err = self.check(risky)
        self.assertEqual(code, 0, err)
        self.assertIn('warning: frame 2: "kb_sync"', err)
        self.assertIn('warning: frame 2: "PR412"', err)

    def test_script_md_is_written_when_it_is_missing(self):
        (self.p / "SCRIPT.md").unlink()
        self.assertEqual(self.check(INTRO_SCRIPT)[0], 0)
        self.assertTrue((self.p / "SCRIPT.md").exists())

    def test_storyboard_intro_without_title(self):
        code, err = self.check(INTRO_SCRIPT, INTRO_STORYBOARD.replace('"The New Upload Flow"', '""'))
        self.assertNotEqual(code, 0)
        self.assertIn("on_screen_title", err)

    def with_demo(self, script, storyboard):
        (self.p / "public").mkdir()
        (self.p / "public/demo-01.mp4").write_bytes(b"x")
        (self.p / "SCRIPT.md").write_text(script)
        return self.check(script, storyboard)

    def test_demo_named_by_its_frame_passes(self):
        script = INTRO_SCRIPT.replace("Middle (Frame 2)", "Demo (Frame 2)")
        storyboard = INTRO_STORYBOARD.replace(
            "## Frame 2 — Middle", "## Frame 2 — Demo\n- asset_candidates: public/demo-01.mp4 — [video] the upload")
        code, err = self.with_demo(script, storyboard)
        self.assertEqual(code, 0, err)

    def test_demo_file_without_demo_line_or_frame(self):
        code, err = self.with_demo(INTRO_SCRIPT, INTRO_STORYBOARD)
        self.assertNotEqual(code, 0)
        self.assertIn("0 Demo line(s) for 1 demo file(s)", err)
        self.assertIn("demo-01.mp4: no STORYBOARD.md frame", err)

    def test_frame_without_scene_job_is_named(self):
        code, err = self.check(INTRO_SCRIPT, INTRO_STORYBOARD.replace("- scene_job: next\n", ""))
        self.assertNotEqual(code, 0)
        self.assertIn("frame 3: STORYBOARD.md has no scene_job", err)
        self.assertNotIn("frame 2", err)

    def test_unknown_scene_job_counts_as_missing(self):
        code, err = self.check(INTRO_SCRIPT, INTRO_STORYBOARD.replace("scene_job: next", "scene_job: wow"))
        self.assertNotEqual(code, 0)
        self.assertIn("frame 3: STORYBOARD.md has no scene_job", err)

    def test_change_needs_before_and_after(self):
        code, err = self.check(INTRO_SCRIPT, INTRO_STORYBOARD.replace('- after: "Uploads show an error."\n', ""))
        self.assertNotEqual(code, 0)
        self.assertIn("frame 2: scene_job change needs before and after", err)

    def test_intro_and_demo_frames_need_no_scene_job(self):
        script = INTRO_SCRIPT.replace("Middle (Frame 2)", "Demo (Frame 2)")
        storyboard = INTRO_STORYBOARD.replace(
            "## Frame 2 — Middle\n- scene_job: change\n- before: \"Uploads fail silently.\"\n- after: \"Uploads show an error.\"",
            "## Frame 2 — Demo\n- asset_candidates: public/demo-01.mp4 — [video] the upload")
        code, err = self.with_demo(script, storyboard)
        self.assertEqual(code, 0, err)

    def test_title_on_another_frame_does_not_count(self):
        moved = INTRO_STORYBOARD.replace('- on_screen_title: "The New Upload Flow"\n', "") \
            .replace("## Frame 2 — Middle", '## Frame 2 — Middle\n- on_screen_title: "X"')
        code, err = self.check(INTRO_SCRIPT, moved)
        self.assertNotEqual(code, 0)
        self.assertIn("on_screen_title", err)


if __name__ == "__main__":
    unittest.main()
