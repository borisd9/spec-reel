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

    def make(self, builtin_model, language, instruct, clone, tempo):
        self.loads += 1
        self.args = (builtin_model, language, instruct)
        self.clone, self.tempo = clone, tempo

        def synthesize(text, out, voice):
            self.calls.append((text, Path(out).name, voice))
            Path(out).write_bytes(b"RIFF" + text.encode())
        return synthesize

    def texts(self):
        return [text for text, _, _ in self.calls]

    def voices(self):
        return [(name, voice) for _, name, voice in self.calls]


class Base(unittest.TestCase):
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


class QwenVoiceTests(Base):
    def test_voices_every_line_with_one_model_load(self):
        code, _ = self.run_main()
        self.assertEqual(code, 0)
        self.assertEqual(self.fake.loads, 1)
        self.assertEqual(self.fake.texts(), ["Hello there.", "The middle line.", "Goodbye."])
        self.assertEqual(sorted(f.name for f in (self.p / "voice-in").iterdir()), ["00.wav", "01.wav", "02.wav"])
        self.assertEqual(self.fake.args, (qwen_voice.DEFAULT_MODEL, "English", qwen_voice.DEFAULT_INSTRUCT))
        self.assertEqual({voice for _, _, voice in self.fake.calls}, {"Aiden"})
        self.assertEqual((self.fake.clone, self.fake.tempo), (None, 1.0))

    def test_frames_option_voices_only_those(self):
        (self.p / "voice-in").mkdir()
        (self.p / "voice-in/00.wav").write_bytes(b"keep")
        code, _ = self.run_main("--frames", "1", "--speaker", "Ryan")
        self.assertEqual(code, 0)
        self.assertEqual(self.fake.texts(), ["The middle line."])
        self.assertEqual((self.p / "voice-in/00.wav").read_bytes(), b"keep")
        self.assertEqual(self.fake.voices(), [("01.wav", "Ryan")])

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
        self.assertEqual(self.fake.texts(), ["Two K-Bs here."])
        self.assertIn("Two KBs here.", (self.p / "SCRIPT.md").read_text())

    def test_say_is_whole_word_only(self):
        (self.p / "SCRIPT.md").write_text(SCRIPT.replace("The middle line.", "Two KBs and a KB."))
        self.assertEqual(self.run_main("--frames", "1", "--say", "KB=kay-bee")[0], 0)
        self.assertEqual(self.fake.texts(), ["Two KBs and a kay-bee."])

    def test_say_without_equals_fails_before_loading_the_model(self):
        for bad in ("bad", "=x", "x="):
            code, err = self.run_main("--say", bad)
            self.assertEqual(code, 1)
            self.assertIn(f"--say needs WRITTEN=SPOKEN: {bad}", err)
        self.assertEqual(self.fake.loads, 0)

    def test_builtin_respellings_always_apply_and_say_overrides_them(self):
        (self.p / "SCRIPT.md").write_text(SCRIPT.replace("The middle line.", "The id of the PR on v8, and ids."))
        self.assertEqual(self.run_main("--frames", "1")[0], 0)
        self.assertEqual(self.fake.texts(), ["The I-D of the P R on V-eight, and I-Ds."])
        self.fake.calls.clear()
        self.assertEqual(self.run_main("--frames", "1", "--say", "id=eye-dee")[0], 0)
        self.assertEqual(self.fake.texts(), ["The eye-dee of the P R on V-eight, and I-Ds."])

    def test_script_md_is_generated_from_user_script_txt(self):
        (self.p / "user_script.txt").write_text(SCRIPT.replace("Goodbye.", "Goodbye, ticket {{ticket}}."))
        (self.p / "facts.json").write_text('{"ticket": "412"}')
        self.assertEqual(self.run_main("--frames", "2")[0], 0)
        self.assertEqual(self.fake.texts(), ["Goodbye, ticket 412."])

    def clone_files(self, transcript="  Exactly what I said.\n"):
        audio, text = self.p / "me.wav", self.p / "me.txt"
        audio.write_bytes(b"RIFF")
        text.write_text(transcript)
        return audio, text

    def test_clone_options_reach_the_factory_with_the_base_model(self):
        audio, text = self.clone_files()
        code, _ = self.run_main("--clone-audio", str(audio), "--clone-transcript", str(text))
        self.assertEqual(code, 0)
        self.assertEqual(self.fake.clone, (audio, "Exactly what I said."))
        self.assertEqual({voice for _, _, voice in self.fake.calls}, {"clone"})
        self.assertEqual(self.fake.texts(), ["Hello there.", "The middle line.", "Goodbye."])

    def test_clone_paths_expand_the_home_folder(self):
        code, err = self.run_main("--clone-audio", "~/no-such-sample.wav", "--clone-transcript", "~/no-such.txt")
        self.assertEqual(code, 1)
        self.assertIn(f"{Path.home()}/no-such-sample.wav not found", err)

    def test_clone_failures_name_the_problem_and_load_nothing(self):
        audio, text = self.clone_files()
        empty = self.p / "empty.txt"
        empty.write_text(" \n")
        for args, message in [
            (["--clone-audio", str(audio)], "--clone-audio and --clone-transcript go together"),
            (["--clone-transcript", str(text)], "--clone-audio and --clone-transcript go together"),
            (["--clone-audio", str(self.p / "gone.wav"), "--clone-transcript", str(text)], "gone.wav not found"),
            (["--clone-audio", str(audio), "--clone-transcript", str(self.p / "gone.txt")], "gone.txt not found"),
            (["--clone-audio", str(audio), "--clone-transcript", str(empty)], f"{empty} is empty"),
        ]:
            code, err = self.run_main(*args)
            self.assertEqual(code, 1)
            self.assertIn(message, err)
        self.assertEqual(self.fake.loads, 0)

    def test_tempo_reaches_the_factory_and_out_of_range_fails_before_loading(self):
        self.assertEqual(self.run_main("--frames", "2", "--tempo", "0.8")[0], 0)
        self.assertEqual(self.fake.tempo, 0.8)
        loads = self.fake.loads
        for bad in ("0.3", "2.5"):
            code, err = self.run_main("--tempo", bad)
            self.assertEqual(code, 1)
            self.assertIn("--tempo must be between 0.5 and 2.0", err)
        self.assertEqual(self.fake.loads, loads)

    def test_sentences_split_after_punctuation_and_a_version_stays_whole(self):
        self.assertEqual(qwen_voice.sentences("One. Two? Three: four; five!"), ["One.", "Two?", "Three:", "four;", "five!"])
        self.assertEqual(qwen_voice.sentences(" v8.1 shipped "), ["v8.1 shipped"])

    def test_missing_script(self):
        (self.p / "SCRIPT.md").unlink()
        code, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("SCRIPT.md not found", err)


IDS_SCRIPT = "# SCRIPT\n\n" + "".join(
    f"## Line {n} — L (Frame {n})\n\n    {text}\n\n" for n, text in enumerate(
        ["Hello there."] * 3 + ["Each draft gets its own id: the published id."] + ["Plain."] * 2
        + ["Sorted by doc id."] + ["Hidden by the fake, valid."] + ["An id filter."] + ["Plain."] * 4
        + ["Five hundred hidden ids."] + ["Plain."] * 3, 1))


class FramesWithAndTakesTests(Base):
    def setUp(self):
        super().setUp()
        (self.p / "SCRIPT.md").write_text(IDS_SCRIPT)

    def takes(self):
        d = self.p / "voice-takes"
        return sorted(d.iterdir()) if d.is_dir() else []

    def test_frames_with_picks_the_frames_that_say_the_word_or_its_plural(self):
        code, _ = self.run_main("--frames-with", "id")
        self.assertEqual(code, 0)
        self.assertEqual(sorted(f.name for f in (self.p / "voice-in").iterdir()), ["04.wav", "07.wav", "09.wav", "14.wav"])
        self.assertEqual(len(self.fake.calls), 4)  # not "hidden", not "valid"

    def test_frames_with_a_word_nobody_says_fails_before_loading_the_model(self):
        code, err = self.run_main("--frames-with", "queue")
        self.assertEqual(code, 1)
        self.assertIn("no frame says 'queue'", err)
        self.assertEqual(self.fake.loads, 0)

    def test_a_file_is_backed_up_before_it_is_replaced(self):
        (self.p / "voice-in").mkdir()
        (self.p / "voice-in/04.wav").write_bytes(b"old take")
        (self.p / "voice-in/05.wav").write_bytes(b"other frame")
        self.assertEqual(self.run_main("--frames", "4")[0], 0)
        (take,) = self.takes()
        self.assertEqual((take / "04.wav").read_bytes(), b"old take")
        self.assertFalse((take / "05.wav").exists())
        self.assertNotEqual((self.p / "voice-in/04.wav").read_bytes(), b"old take")

    def test_nothing_to_back_up_makes_no_take_folder(self):
        self.assertEqual(self.run_main("--frames", "4")[0], 0)
        self.assertEqual(self.takes(), [])

    def test_restore_puts_a_take_back_and_keeps_the_file_it_replaces(self):
        (self.p / "voice-takes/pre-fix").mkdir(parents=True)
        (self.p / "voice-takes/pre-fix/04.wav").write_bytes(b"chosen take")
        (self.p / "voice-takes/pre-fix/08.wav").write_bytes(b"another")
        (self.p / "voice-takes/pre-fix/video.mp4").write_bytes(b"not audio")
        (self.p / "voice-in").mkdir()
        (self.p / "voice-in/04.mp3").write_bytes(b"newer take")
        code, _ = self.run_main("--restore", "pre-fix", "--frames", "4")
        self.assertEqual(code, 0)
        self.assertEqual(sorted(f.name for f in (self.p / "voice-in").iterdir()), ["04.wav"])
        self.assertEqual((self.p / "voice-in/04.wav").read_bytes(), b"chosen take")
        saved = [t for t in self.takes() if t.name != "pre-fix"]
        self.assertEqual([(t / "04.mp3").read_bytes() for t in saved], [b"newer take"])
        self.assertEqual(self.fake.loads, 0)

    def test_restore_without_frames_puts_back_every_audio_file(self):
        (self.p / "voice-takes/t1").mkdir(parents=True)
        for n in ("04", "08"):
            (self.p / f"voice-takes/t1/{n}.wav").write_bytes(b"x")
        self.assertEqual(self.run_main("--restore", "t1")[0], 0)
        self.assertEqual(sorted(f.name for f in (self.p / "voice-in").iterdir()), ["04.wav", "08.wav"])

    def test_restore_of_an_unknown_take_or_frame_fails(self):
        code, err = self.run_main("--restore", "nope")
        self.assertEqual((code, "voice-takes/nope not found" in err), (1, True))
        (self.p / "voice-takes/t1").mkdir(parents=True)
        (self.p / "voice-takes/t1/04.wav").write_bytes(b"x")
        code, err = self.run_main("--restore", "t1", "--frames", "9")
        self.assertEqual((code, "has no audio for 9" in err), (1, True))


DISCUSSION = """# SCRIPT

**Voices:** A — Aiden; B — Ryan

## Line 1 — Intro (Frame 1)

    Hello there.

## Line 2 — Topic (Frame 2)

**Time:** 4 – 20s

### Turn — A

    What changed with uploads?

### Turn — B

    Files over 5 MB now resume. The id stays.

### Turn — A

    So nothing restarts.

## Line 3 — Other (Frame 3)

    Plain frame.
"""


class DiscussionTests(Base):
    def setUp(self):
        super().setUp()
        (self.p / "SCRIPT.md").write_text(DISCUSSION)

    def names(self):
        return sorted(f.name for f in (self.p / "voice-in").iterdir())

    def test_each_turn_is_a_file_in_its_speakers_voice_with_one_factory_call(self):
        code, err = self.run_main("--voice", "A=Aiden", "--voice", "B=Ryan")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(self.fake.loads, 1)
        self.assertEqual(self.fake.voices(), [
            ("01.wav", "Aiden"), ("02.1.wav", "Aiden"), ("02.2.wav", "Ryan"), ("02.3.wav", "Aiden"), ("03.wav", "Aiden")])
        self.assertEqual(self.names(), ["01.wav", "02.1.wav", "02.2.wav", "02.3.wav", "03.wav"])
        self.assertEqual(self.fake.texts()[2], "Files over 5 MB now resume. The I-D stays.")  # respelled per turn

    def test_a_plain_frame_uses_voice_a_and_a_without_voice_a_is_the_speaker_option(self):
        self.assertEqual(self.run_main("--frames", "3", "--voice", "A=Ryan")[0], 0)
        self.assertEqual(self.fake.voices(), [("03.wav", "Ryan")])
        self.fake.calls.clear()
        self.assertEqual(self.run_main("--frames", "2", "--speaker", "Serena", "--voice", "B=Ryan")[0], 0)
        self.assertEqual(self.fake.voices(), [("02.1.wav", "Serena"), ("02.2.wav", "Ryan"), ("02.3.wav", "Serena")])

    def test_a_b_turn_without_voice_b_fails_before_loading(self):
        code, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("frame 2 turn 2: no voice for B (pass --voice B=...)", err)
        self.assertEqual(self.fake.loads, 0)
        self.assertFalse((self.p / "voice-in").exists())

    def test_voice_b_is_not_needed_when_no_selected_frame_has_a_b_turn(self):
        self.assertEqual(self.run_main("--frames", "1", "3")[0], 0)
        self.assertEqual(self.fake.loads, 1)

    def test_clone_voice_without_the_clone_flags_fails_before_loading(self):
        for spec in ("B=clone", "A=clone", "B=Clone"):
            code, err = self.run_main("--voice", spec)
            self.assertEqual(code, 1)
            self.assertIn("needs --clone-audio and --clone-transcript", err)
        self.assertEqual(self.fake.loads, 0)

    def test_a_clone_and_a_built_in_speaker_mix_in_one_run(self):
        audio, text = self.p / "me.wav", self.p / "me.txt"
        audio.write_bytes(b"RIFF")
        text.write_text("What I said.")
        args = ("--clone-audio", str(audio), "--clone-transcript", str(text))
        self.assertEqual(self.run_main(*args, "--voice", "B=Ryan")[0], 0)
        self.assertEqual(self.fake.loads, 1)
        self.assertEqual(self.fake.voices()[1:4], [("02.1.wav", "clone"), ("02.2.wav", "Ryan"), ("02.3.wav", "clone")])
        self.fake.calls.clear()
        self.assertEqual(self.run_main(*args, "--voice", "A=Aiden", "--voice", "B=clone", "--frames", "2")[0], 0)
        self.assertEqual([v for _, v in self.fake.voices()], ["Aiden", "clone", "Aiden"])

    def test_bad_voice_options_fail_before_loading(self):
        for bad, message in [("Ryan", "--voice needs SPEAKER=VOICE: Ryan"), ("B=", "--voice needs SPEAKER=VOICE: B="),
                             ("C=Ryan", "--voice speaker must be A or B: C=Ryan"), ("=Ryan", "--voice needs SPEAKER=VOICE: =Ryan")]:
            code, err = self.run_main("--voice", bad)
            self.assertEqual(code, 1)
            self.assertIn(message, err)
        self.assertEqual(self.fake.loads, 0)

    def test_a_turn_with_an_unknown_speaker_or_no_text_fails_before_loading(self):
        script = DISCUSSION.replace("### Turn — B", "### Turn — C")
        (self.p / "SCRIPT.md").write_text(script)
        code, err = self.run_main("--voice", "B=Ryan")
        self.assertEqual(code, 1)
        self.assertIn("frame 2 turn 2: speaker must be A or B", err)
        (self.p / "SCRIPT.md").write_text(DISCUSSION.replace("    So nothing restarts.\n", ""))
        code, err = self.run_main("--voice", "B=Ryan")
        self.assertEqual(code, 1)
        self.assertIn("frame 2 turn 3: no spoken text", err)
        (self.p / "SCRIPT.md").write_text(DISCUSSION.replace("**Time:** 4 – 20s\n", "**Time:** 4 – 20s\n\n    Stray text.\n"))
        code, err = self.run_main("--voice", "B=Ryan")
        self.assertEqual(code, 1)
        self.assertIn("frame 2: text before its first turn", err)
        self.assertEqual(self.fake.loads, 0)

    def test_revoicing_a_frame_backs_up_then_removes_all_its_old_files(self):
        vin = self.p / "voice-in"
        vin.mkdir()
        for n in ("02.mp3", "02.1.wav", "02.2.wav", "02.3.wav", "02.4.wav", "03.wav", "20.1.wav"):
            (vin / n).write_bytes(n.encode())
        self.assertEqual(self.run_main("--frames", "2", "--voice", "B=Ryan")[0], 0)
        self.assertEqual(sorted(f.name for f in vin.iterdir()), ["02.1.wav", "02.2.wav", "02.3.wav", "03.wav", "20.1.wav"])
        self.assertNotEqual((vin / "02.1.wav").read_bytes(), b"02.1.wav")  # replaced, not left over
        (take,) = (self.p / "voice-takes").iterdir()
        self.assertEqual(sorted(f.name for f in take.iterdir()), ["02.1.wav", "02.2.wav", "02.3.wav", "02.4.wav", "02.mp3"])
        self.assertEqual((take / "02.2.wav").read_bytes(), b"02.2.wav")

    def test_a_script_with_one_frame_going_from_plain_to_turns_drops_the_plain_file(self):
        vin = self.p / "voice-in"
        vin.mkdir()
        (vin / "02.wav").write_bytes(b"old plain")
        self.assertEqual(self.run_main("--frames", "2", "--voice", "B=Ryan")[0], 0)
        self.assertEqual(self.names(), ["02.1.wav", "02.2.wav", "02.3.wav"])

    def test_restore_puts_back_turn_files_of_a_frame_and_keeps_the_ones_it_replaces(self):
        take = self.p / "voice-takes/t1"
        take.mkdir(parents=True)
        for n in ("02.1.wav", "02.2.wav", "02.3.wav", "03.wav"):
            (take / n).write_bytes(b"take " + n.encode())
        vin = self.p / "voice-in"
        vin.mkdir()
        (vin / "02.wav").write_bytes(b"plain")
        (vin / "02.4.wav").write_bytes(b"extra")
        self.assertEqual(self.run_main("--restore", "t1", "--frames", "2")[0], 0)
        self.assertEqual(sorted(f.name for f in vin.iterdir()), ["02.1.wav", "02.2.wav", "02.3.wav"])
        self.assertEqual((vin / "02.3.wav").read_bytes(), b"take 02.3.wav")
        (saved,) = [t for t in (self.p / "voice-takes").iterdir() if t.name != "t1"]
        self.assertEqual(sorted(f.name for f in saved.iterdir()), ["02.4.wav", "02.wav"])
        self.assertEqual(self.run_main("--restore", "t1")[0], 0)
        self.assertEqual(sorted(f.name for f in vin.iterdir()), ["02.1.wav", "02.2.wav", "02.3.wav", "03.wav"])
        self.assertEqual(self.fake.loads, 0)

    def test_frames_with_picks_a_discussion_frame_and_voices_all_its_turns(self):
        self.assertEqual(self.run_main("--frames-with", "resume", "--voice", "B=Ryan")[0], 0)
        self.assertEqual(self.names(), ["02.1.wav", "02.2.wav", "02.3.wav"])


if __name__ == "__main__":
    unittest.main()
