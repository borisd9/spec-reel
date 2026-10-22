#!/usr/bin/env python3
"""Voice SCRIPT.md lines on this Mac with Qwen3-TTS (through MLX-Audio) into voice-in/NN.wav.

    uv run --python 3.11 --with mlx-audio==0.6.1 --with soundfile \
        python <skill dir>/scripts/qwen_voice.py <project_dir> [--frames 1 3 | --frames-with WORD] \
        [--speaker Aiden] [--say KBs=K-Bs ...] [--tempo 0.8] \
        [--clone-audio me.wav --clone-transcript me.txt]
    python3 -I <skill dir>/scripts/qwen_voice.py <project_dir> --restore <take> [--frames 1 3]

Built-in respellings (adopt_voice.BUILTIN_RESPELLINGS: id, ids, PR, v8) are always applied to the text the
voice reads; --say adds to them or replaces one. Before a file is replaced it is copied to
voice-takes/<take>/; --restore puts a take back (all of its files, or only the named frames).
Then run adopt_voice.py on the same project, exactly as for audio from the user's own engine.
--clone-audio and --clone-transcript voice the lines in the speaker of a short recording instead of a built-in
speaker: the transcript file must hold exactly what the recording says (--speaker and --instruct are then ignored).
--tempo slows (below 1) or speeds the voice with ffmpeg, without changing pitch; --speed does nothing for Qwen3-TTS.
Needs an Apple Silicon Mac. The model downloads once (about 4 GB) into the Hugging Face cache.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adopt_voice import BUILTIN_RESPELLINGS, EXTS, parse_script, respell, sync_script, words_of  # noqa: E402

DEFAULT_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
CLONE_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16"
DEFAULT_SPEAKER = "Aiden"
DEFAULT_INSTRUCT = "Calm, clear and friendly, a conversational narrator explaining a product update to teammates."
SENTENCE_GAP_S = 0.3  # the cloning path runs sentences together, so each is voiced alone and joined with this
TEMPO_RANGE = (0.5, 2.0)  # ffmpeg atempo limits


def audio_files(voice_in, frame):
    """The audio files voice-in/ holds for one frame (one expected; adopt_voice.py refuses several)."""
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
    files = sorted(f for f in src.iterdir() if f.suffix.lower() in EXTS and f.stem.isdigit() and (not frames or int(f.stem) in frames))
    if not files:
        return f"voice-takes/{take} has no audio for {' '.join(map(str, frames)) or 'any frame'}"
    now = back_up(voice_in, [int(f.stem) for f in files], time.strftime("%Y%m%d-%H%M%S") + "-before-restore")
    for f in files:
        for old in audio_files(voice_in, int(f.stem)):
            old.unlink()
        shutil.copy2(f, voice_in / f.name)
        print(f"restored frame {int(f.stem)} <- voice-takes/{take}/{f.name}", flush=True)
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


def qwen_synthesizer(model_id, speaker, language, instruct, clone, tempo):
    """Load the model once and return synthesize(text, out_path). clone is None or (audio_path, transcript)."""
    import numpy as np
    import soundfile as sf
    from mlx_audio.tts.utils import load_model

    model = load_model(model_id)
    if clone:
        from mlx_audio.utils import load_audio
        ref_audio = load_audio(str(clone[0]), sample_rate=model.sample_rate)
        gap = np.zeros(int(SENTENCE_GAP_S * model.sample_rate), dtype=np.float32)

    def voice(text):
        if not clone:
            return [r.audio for r in model.generate_custom_voice(text=text, speaker=speaker, language=language, instruct=instruct)]
        parts = []
        for sentence in sentences(text):
            parts += [gap] if parts else []
            parts += [r.audio for r in model.generate(text=sentence, ref_audio=ref_audio, ref_text=clone[1])]
        return parts

    def synthesize(text, out):
        chunks = [np.array(c, dtype=np.float32).reshape(-1) for c in voice(text)]
        if not chunks:
            raise RuntimeError("the model returned no audio")
        sf.write(out, np.concatenate(chunks), model.sample_rate, subtype="PCM_16")
        if tempo != 1.0:
            slow_down(out, tempo)

    return synthesize


def main(argv, make_synthesizer=qwen_synthesizer):
    ap = argparse.ArgumentParser(prog="qwen_voice.py")
    ap.add_argument("project_dir", type=Path)
    ap.add_argument("--frames", type=int, nargs="+", help="voice only these frames (default: every line)")
    ap.add_argument("--frames-with", metavar="WORD", help="voice only the frames whose spoken text has this word (or its plural)")
    ap.add_argument("--restore", metavar="TAKE", help="put voice-takes/TAKE back into voice-in/ (with --frames: only those)")
    ap.add_argument("--model", help=f"default: {DEFAULT_MODEL}, or {CLONE_MODEL} with --clone-audio")
    ap.add_argument("--speaker", default=DEFAULT_SPEAKER)
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
    wanted = a.frames or sorted(lines)
    if a.frames_with:
        word = words_of(a.frames_with)[:1]  # the word or its plural: "id" finds "ids" too
        wanted = [f for f in sorted(lines) if word and {word[0], word[0] + "s"} & set(words_of(lines[f]))]
        if not wanted:
            print(f"no frame says '{a.frames_with}'", file=sys.stderr)
            return 1
    problems = [f"frame {f}: not in SCRIPT.md" for f in wanted if f not in lines]
    problems += [f"frame {f}: heading has no spoken text" for f in wanted if f in lines and not lines[f]]
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    model = a.model or (CLONE_MODEL if clone else DEFAULT_MODEL)
    synthesize = make_synthesizer(model, a.speaker, a.language, a.instruct, clone, a.tempo)
    voice_in = a.project_dir / "voice-in"
    voice_in.mkdir(exist_ok=True)
    take = back_up(voice_in, wanted, time.strftime("%Y%m%d-%H%M%S"))
    if take.is_dir():
        print(f"the files replaced are in {take.relative_to(a.project_dir)}", flush=True)
    for frame in wanted:
        nn = f"{frame:02d}"
        for old in audio_files(voice_in, frame):  # one file per line, or adopt_voice.py refuses the frame
            old.unlink()
        synthesize(respell(lines[frame], pairs), voice_in / f"{nn}.wav")
        print(f"voiced frame {frame} -> voice-in/{nn}.wav", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
