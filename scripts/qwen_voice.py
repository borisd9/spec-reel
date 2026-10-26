#!/usr/bin/env python3
"""Voice SCRIPT.md lines on this Mac with Qwen3-TTS (through MLX-Audio) into voice-in/NN.wav.

    uv run --python 3.11 --with mlx-audio==0.6.1 --with soundfile \
        python <skill dir>/scripts/qwen_voice.py <project_dir> [--frames 1 3 | --frames-with WORD] \
        [--speaker Aiden] [--voice A=Aiden --voice B=Ryan] [--say KBs=K-Bs ...] [--tempo 0.8] \
        [--clone-audio me.wav --clone-transcript me.txt]
    python3 -I <skill dir>/scripts/qwen_voice.py <project_dir> --restore <take> [--frames 1 3]

Built-in respellings (adopt_voice.BUILTIN_RESPELLINGS: id, ids, PR, v8) are always applied to the text the
voice reads; --say adds to them or replaces one. Before a file is replaced it is copied to
voice-takes/<take>/; --restore puts a take back (all of its files, or only the named frames).
Then run adopt_voice.py on the same project, exactly as for audio from the user's own engine.
--clone-audio and --clone-transcript give the `clone` voice, the speaker of a short recording: the transcript file must
hold exactly what the recording says (--speaker is then ignored unless --voice names it; --instruct never reaches the clone).
--voice SPEAKER=VOICE (A or B; VOICE is a built-in speaker name or `clone`) voices a discussion: a line with
`### Turn — A|B` headings gets one file per turn, voice-in/NN.K.wav (K = 1, 2, ... in script order), each in its speaker's
voice; a line without turn headings stays voice-in/NN.wav in A's voice. Without --voice A, A is the clone when the clone
flags are given, else --speaker. A B turn needs --voice B. --frames re-voices every turn of the frame.
--tempo slows (below 1) or speeds the voice with ffmpeg, without changing pitch; --speed does nothing for Qwen3-TTS.
Needs an Apple Silicon Mac. Each model downloads once (about 4 GB) into the Hugging Face cache; a model loads
only when a built-in speaker (--model overrides it) or the clone is first used.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adopt_voice import BUILTIN_RESPELLINGS, EXTS, parse_script, parse_turns, respell, sync_script, words_of  # noqa: E402

DEFAULT_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
CLONE_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16"
DEFAULT_SPEAKER = "Aiden"
DEFAULT_INSTRUCT = "Calm, clear and friendly, a conversational narrator explaining a product update to teammates."
SENTENCE_GAP_S = 0.3  # the cloning path runs sentences together, so each is voiced alone and joined with this
TEMPO_RANGE = (0.5, 2.0)  # ffmpeg atempo limits


def audio_files(voice_in, frame):
    """The audio files voice-in/ holds for one frame: NN.<ext>, or NN.K.<ext> for each turn of a discussion line."""
    return [f for f in voice_in.glob(f"{frame:02d}.*") if f.suffix.lower() in EXTS]


def back_up(voice_in, frames, take):
    """Copy the audio files of these frames into voice-takes/<take>/, so a replaced take is never lost."""
    dest = voice_in.parent / "voice-takes" / take
    for frame in frames:
        for f in audio_files(voice_in, frame):
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest / f.name)
    return dest


def restore(project, take, frames):
    """Put the files of voice-takes/<take>/ (all, or these frames) back into voice-in/. Returns an error or None."""
    src = project / "voice-takes" / take
    if not src.is_dir():
        return f"voice-takes/{take} not found"
    voice_in = project / "voice-in"
    voice_in.mkdir(exist_ok=True)
    files = sorted(f for f in src.iterdir() if f.suffix.lower() in EXTS and re.fullmatch(r"\d+(\.\d+)?", f.stem)
                   and (not frames or int(f.stem.split(".")[0]) in frames))
    if not files:
        return f"voice-takes/{take} has no audio for {' '.join(map(str, frames)) or 'any frame'}"
    restored = sorted({int(f.stem.split(".")[0]) for f in files})
    now = back_up(voice_in, restored, time.strftime("%Y%m%d-%H%M%S") + "-before-restore")
    for frame in restored:  # every old file of the frame goes first, so a restored turn is never removed by its sibling
        for old in audio_files(voice_in, frame):
            old.unlink()
    for f in files:
        shutil.copy2(f, voice_in / f.name)
        print(f"restored frame {int(f.stem.split('.')[0])} <- voice-takes/{take}/{f.name}", flush=True)
    if now.is_dir():
        print(f"the files replaced are in {now.relative_to(project)}")
    return None


def sentences(text):
    """Split after . ! ? ; or : followed by whitespace ("v8.1" stays whole)."""
    return [s for s in re.split(r"(?<=[.!?;:])\s+", text.strip()) if s]


def slow_down(out, tempo):
    """Change the pace of a WAV in place with ffmpeg atempo (pitch unchanged)."""
    tmp = Path(out).with_suffix(".tempo.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out), "-filter:a", f"atempo={tempo}", str(tmp)], check=True)
    os.replace(tmp, out)


def qwen_synthesizer(builtin_model, language, instruct, clone, tempo):
    """Return synthesize(text, out_path, voice); voice is a built-in speaker name or "clone" (clone = (audio, transcript)).
    The built-in model (builtin_model) loads on the first built-in speaker, CLONE_MODEL on the first clone item."""
    import numpy as np
    import soundfile as sf
    from mlx_audio.tts.utils import load_model

    load = lru_cache(maxsize=None)(load_model)

    @lru_cache(maxsize=None)
    def reference():
        from mlx_audio.utils import load_audio
        return load_audio(str(clone[0]), sample_rate=load(CLONE_MODEL).sample_rate)

    def generate(text, voice):
        if voice != "clone":
            model = load(builtin_model)
            return model, [r.audio for r in model.generate_custom_voice(text=text, speaker=voice, language=language, instruct=instruct)]
        model, parts = load(CLONE_MODEL), []
        gap = np.zeros(int(SENTENCE_GAP_S * model.sample_rate), dtype=np.float32)
        for sentence in sentences(text):  # one sentence at a time: the clone runs sentences together otherwise
            parts += [gap] if parts else []
            parts += [r.audio for r in model.generate(text=sentence, ref_audio=reference(), ref_text=clone[1])]
        return model, parts

    def synthesize(text, out, voice):
        model, audio = generate(text, voice)
        chunks = [np.array(c, dtype=np.float32).reshape(-1) for c in audio]
        if not chunks:
            raise RuntimeError("the model returned no audio")
        sf.write(out, np.concatenate(chunks), model.sample_rate, subtype="PCM_16")
        if tempo != 1.0:
            slow_down(out, tempo)

    return synthesize


def voice_map(specs, clone, speaker):
    """--voice SPEAKER=VOICE values -> ({"A": voice, "B": voice}, error). A defaults to the clone, else --speaker."""
    voices = {"A": "clone" if clone else speaker}
    for spec in specs:
        who, _, voice = spec.partition("=")
        if not who or not voice:
            return None, f"--voice needs SPEAKER=VOICE: {spec}"
        if who.upper() not in ("A", "B"):
            return None, f"--voice speaker must be A or B: {spec}"
        voices[who.upper()] = "clone" if voice.lower() == "clone" else voice
    if "clone" in voices.values() and not clone:
        return None, "--voice ...=clone needs --clone-audio and --clone-transcript"
    return voices, None


def work_items(frame, text, turns, voices):
    """One frame -> ([(spoken text, file stem, voice)], [problems]): a turn each (NN.K), or the whole frame (NN) in A's voice."""
    nn = f"{frame:02d}"
    if not turns:
        return [(text, nn, voices["A"])], []
    problems = [f"frame {frame}: text before its first turn"] if " ".join(t for _, t in turns) != text else []
    for k, (who, t) in enumerate(turns, 1):
        where = f"frame {frame} turn {k}"
        if who not in voices:
            problems.append(f"{where}: speaker must be A or B" if who == "?" else f"{where}: no voice for {who} (pass --voice {who}=...)")
        elif not t:
            problems.append(f"{where}: no spoken text")
    return [(t, f"{nn}.{k}", voices.get(who)) for k, (who, t) in enumerate(turns, 1)], problems


def main(argv, make_synthesizer=qwen_synthesizer):
    ap = argparse.ArgumentParser(prog="qwen_voice.py")
    ap.add_argument("project_dir", type=Path)
    ap.add_argument("--frames", type=int, nargs="+", help="voice only these frames (default: every line)")
    ap.add_argument("--frames-with", metavar="WORD", help="voice only the frames whose spoken text has this word (or its plural)")
    ap.add_argument("--restore", metavar="TAKE", help="put voice-takes/TAKE back into voice-in/ (with --frames: only those)")
    ap.add_argument("--model", help=f"the model for built-in speakers (default: {DEFAULT_MODEL}); the clone always uses {CLONE_MODEL}")
    ap.add_argument("--speaker", default=DEFAULT_SPEAKER, help="the built-in speaker of A (and of a line without turns) unless --voice A or the clone says otherwise")
    ap.add_argument("--voice", action="append", default=[], metavar="SPEAKER=VOICE",
                    help="discussion: voice speaker A or B with a built-in speaker name or `clone`; repeatable")
    ap.add_argument("--language", default="English")
    ap.add_argument("--instruct", default=DEFAULT_INSTRUCT)
    ap.add_argument("--clone-audio", type=lambda v: Path(v).expanduser(), metavar="PATH", help="a recording of the voice to clone (WAV)")
    ap.add_argument("--clone-transcript", type=lambda v: Path(v).expanduser(), metavar="PATH", help="a text file with exactly what the recording says")
    ap.add_argument("--tempo", type=float, default=1.0, help="pace of the voice, 0.5 to 2.0; below 1 is slower (default 1.0)")
    ap.add_argument("--say", action="append", default=[], metavar="WRITTEN=SPOKEN",
                    help="say WRITTEN as SPOKEN (whole word, case-sensitive); SCRIPT.md is unchanged; repeatable")
    a = ap.parse_args(argv)

    if a.restore:
        error = restore(a.project_dir, a.restore, a.frames or [])
        if error:
            print(error, file=sys.stderr)
        return 1 if error else 0

    pairs = [tuple(v.split("=", 1)) if "=" in v else (v, "") for v in a.say]
    bad = [v for v, (w, s) in zip(a.say, pairs) if not w or not s]
    if bad:
        print(f"--say needs WRITTEN=SPOKEN: {bad[0]}", file=sys.stderr)
        return 1
    pairs = {**BUILTIN_RESPELLINGS, **dict(pairs)}

    clone = None
    if bool(a.clone_audio) != bool(a.clone_transcript):
        print("--clone-audio and --clone-transcript go together", file=sys.stderr)
        return 1
    if a.clone_audio:
        missing = [p for p in (a.clone_audio, a.clone_transcript) if not p.is_file()]
        if missing:
            print(f"{missing[0]} not found", file=sys.stderr)
            return 1
        transcript = a.clone_transcript.read_text().strip()
        if not transcript:
            print(f"{a.clone_transcript} is empty", file=sys.stderr)
            return 1
        clone = (a.clone_audio, transcript)
    if not TEMPO_RANGE[0] <= a.tempo <= TEMPO_RANGE[1]:
        print(f"--tempo must be between {TEMPO_RANGE[0]} and {TEMPO_RANGE[1]}", file=sys.stderr)
        return 1

    voices, error = voice_map(a.voice, clone, a.speaker)
    if error:
        print(error, file=sys.stderr)
        return 1

    script = a.project_dir / "SCRIPT.md"
    try:
        sync_script(a.project_dir)  # SCRIPT.md is generated from user_script.txt
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    if not script.exists():
        print(f"SCRIPT.md not found in {a.project_dir}", file=sys.stderr)
        return 1
    lines = dict(parse_script(script.read_text()))
    turns = parse_turns(script.read_text())
    wanted = a.frames or sorted(lines)
    if a.frames_with:
        word = words_of(a.frames_with)[:1]  # the word or its plural: "id" finds "ids" too
        wanted = [f for f in sorted(lines) if word and {word[0], word[0] + "s"} & set(words_of(lines[f]))]
        if not wanted:
            print(f"no frame says '{a.frames_with}'", file=sys.stderr)
            return 1
    problems = [f"frame {f}: not in SCRIPT.md" for f in wanted if f not in lines]
    problems += [f"frame {f}: heading has no spoken text" for f in wanted if f in lines and not lines[f]]
    work = {}
    for frame in (f for f in wanted if f in lines and lines[f]):
        work[frame], found = work_items(frame, lines[frame], turns.get(frame), voices)
        problems += found
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    synthesize = make_synthesizer(a.model or DEFAULT_MODEL, a.language, a.instruct, clone, a.tempo)
    voice_in = a.project_dir / "voice-in"
    voice_in.mkdir(exist_ok=True)
    take = back_up(voice_in, wanted, time.strftime("%Y%m%d-%H%M%S"))
    if take.is_dir():
        print(f"the files replaced are in {take.relative_to(a.project_dir)}", flush=True)
    for frame in wanted:
        for old in audio_files(voice_in, frame):  # plain and turn files never coexist, or adopt_voice.py refuses the frame
            old.unlink()
        for text, stem, voice in work[frame]:
            synthesize(respell(text, pairs), voice_in / f"{stem}.wav", voice)
            print(f"voiced frame {frame} -> voice-in/{stem}.wav ({voice})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
