#!/usr/bin/env python3
"""Voice SCRIPT.md lines on this Mac with Qwen3-TTS (through MLX-Audio) into voice-in/NN.wav.

    uv run --python 3.11 --with mlx-audio==0.6.1 --with soundfile \
        python <skill dir>/scripts/qwen_voice.py <project_dir> [--frames 1 3] [--speaker Aiden]

Then run adopt_voice.py on the same project, exactly as for audio from the user's own engine.
Needs an Apple Silicon Mac. The model downloads once (about 4 GB) into the Hugging Face cache.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adopt_voice import EXTS, parse_script  # noqa: E402

DEFAULT_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16"
DEFAULT_SPEAKER = "Aiden"
DEFAULT_INSTRUCT = "Calm, clear and friendly, a conversational narrator explaining a product update to teammates."


def qwen_synthesizer(model_id, speaker, language, instruct):
    """Load the model once and return synthesize(text, out_path)."""
    import numpy as np
    import soundfile as sf
    from mlx_audio.tts.utils import load_model

    model = load_model(model_id)

    def synthesize(text, out):
        chunks = [np.array(r.audio, dtype=np.float32).reshape(-1) for r in model.generate_custom_voice(
            text=text, speaker=speaker, language=language, instruct=instruct)]
        if not chunks:
            raise RuntimeError("the model returned no audio")
        sf.write(out, np.concatenate(chunks), model.sample_rate, subtype="PCM_16")

    return synthesize


def main(argv, make_synthesizer=qwen_synthesizer):
    ap = argparse.ArgumentParser(prog="qwen_voice.py")
    ap.add_argument("project_dir", type=Path)
    ap.add_argument("--frames", type=int, nargs="+", help="voice only these frames (default: every line)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--speaker", default=DEFAULT_SPEAKER)
    ap.add_argument("--language", default="English")
    ap.add_argument("--instruct", default=DEFAULT_INSTRUCT)
    a = ap.parse_args(argv)

    script = a.project_dir / "SCRIPT.md"
    if not script.exists():
        print(f"SCRIPT.md not found in {a.project_dir}", file=sys.stderr)
        return 1
    lines = dict(parse_script(script.read_text()))
    wanted = a.frames or sorted(lines)
    problems = [f"frame {f}: not in SCRIPT.md" for f in wanted if f not in lines]
    problems += [f"frame {f}: heading has no spoken text" for f in wanted if f in lines and not lines[f]]
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    synthesize = make_synthesizer(a.model, a.speaker, a.language, a.instruct)
    voice_in = a.project_dir / "voice-in"
    voice_in.mkdir(exist_ok=True)
    for frame in wanted:
        nn = f"{frame:02d}"
        for old in voice_in.glob(f"{nn}.*"):  # one file per line, or adopt_voice.py refuses the frame
            if old.suffix.lower() in EXTS:
                old.unlink()
        synthesize(lines[frame], voice_in / f"{nn}.wav")
        print(f"voiced frame {frame} -> voice-in/{nn}.wav", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
