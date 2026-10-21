# Spec Reel

A Claude Code skill that turns links to plans and specs into a short narrated explainer video.

You give it one or more links or files. It reads them, writes a digest of why each plan exists, what it changes and what comes next, and writes a timestamped narration script. You approve both. It voices the script on your Mac with [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice) through [MLX-Audio](https://github.com/Blaizzy/mlx-audio), or takes audio you make with any text-to-speech tool you choose. Then it hands scene building to the HyperFrames `faceless-explainer` workflow, which builds scenes synced to the narration and renders an MP4.

Stages: sources, digest (you approve), script (you approve), frame plan (you approve), sketches (you approve), preview (you approve), render.

Every run has its own folder with a `RUN.md` that records the stage and each approval, so an interrupted run can be resumed.

## Prerequisites

- Claude Code
- The HyperFrames skills, including `faceless-explainer`: `npx hyperframes skills`
- Node.js with `npx`
- Python 3
- `ffmpeg` and `ffprobe` on your path
- For the default voice: an Apple Silicon Mac and [`uv`](https://docs.astral.sh/uv/). The skill runs Qwen3-TTS with `uv run --with mlx-audio`, so there is nothing else to install; the model (about 4 GB) downloads on first use. On other machines, use your own engine.
- Optional: the GitHub CLI (`gh`), signed in, to read GitHub links

## Install

Clone it into your skills folder:

```bash
git clone https://github.com/borisd9/spec-reel.git ~/.claude/skills/spec-reel
```

Or clone it somewhere else and link it:

```bash
git clone https://github.com/borisd9/spec-reel.git ~/skills/spec-reel
ln -s ~/skills/spec-reel ~/.claude/skills/spec-reel
```

Start a new Claude Code session. `spec-reel` appears in the skill list.

## Configure

```bash
cp config.example.json config.json
```

`config.json` is ignored by git. The skill creates it and asks for any missing value on the first run, so this step is optional.

| Field | Meaning |
|---|---|
| `output_root` | Where run folders go. Default `~/Movies/hyperframes`. |
| `style_preset` | The faceless-explainer look. Default `blue-professional`. |
| `voice_source` | `qwen` (Qwen3-TTS on your Mac, default) or `own` (your own engine). |
| `qwen_speaker` | `Aiden` (default) or `Ryan`, the two English voices. |
| `qwen_instruct` | A style instruction for Qwen3-TTS. Empty means a calm, conversational narrator. |
| `tts_command` | Default command for your own engine. Empty means you drop audio files. |

## Voice sources

**Qwen3-TTS** (default). Runs locally through MLX-Audio, so the script text never leaves your machine. Model: `mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16` (Apache-2.0). On an Apple Silicon Mac it generates speech about twice as fast as real time. To voice a script by hand:

```bash
uv run --python 3.11 --with mlx-audio==0.6.1 --with soundfile \
  python scripts/qwen_voice.py <run folder> --speaker Aiden
```

**Your own engine.** The skill lists every script line with its frame number and a target file name, `voice-in/NN.<ext>`. Either drop one audio file per line (WAV, MP3, M4A or AIFF), or give a command and the skill runs it once per line. In a command, `{text_file}` is a temp file holding the line's text and `{out}` is `voice-in/NN` with no extension; the command supplies its own extension:

```bash
say -v Samantha -f {text_file} -o {out}.aiff
```

The spoken text reaches the command only through `{text_file}`. A command never contains a credential: if your tool needs a key, the command reads it from an environment variable or a file outside this folder. The skill refuses to save a command that contains a key.

`scripts/adopt_voice.py` then converts the files to WAV, gets word timings with `npx hyperframes transcribe`, and writes the audio metadata faceless-explainer reads. Changing one line means replacing one file and running it again.

## First run

In Claude Code:

```text
/spec-reel https://example.com/plan ~/plans/feature-spec.md
```

The skill asks, in one batch: the links or files, the audience and intent, the target length (default 60-90 seconds) and the voice source. Then approve the digest, approve the script, and review the frame plan, the sketch board and the preview. The MP4 is written to `renders/video.mp4` inside the run folder.

## Tests

```bash
python3 -I -m unittest discover -s scripts -p 'test_*.py' -v
```

The tests use fakes for ffmpeg, ffprobe, transcription and the Qwen3-TTS model, so they need none of them.

## License

MIT, see [LICENSE](LICENSE). The Qwen3-TTS model it downloads is Apache-2.0.
