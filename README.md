# Spec Reel

A Claude Code skill that turns links to plans and specs into a short narrated explainer video.

You give it one or more links or files. It reads them, writes a digest of why each plan exists, what it changes and what comes next, and writes a timestamped narration script. You approve both. Then it hands scene building to the HyperFrames `faceless-explainer` workflow, which builds scenes synced to the narration and renders an MP4. Narration comes from faceless-explainer's own voice engine, or from audio you make with any text-to-speech tool you choose.

Stages: sources, digest (you approve), script (you approve), frame plan (you approve), sketches (you approve), preview (you approve), render.

Every run has its own folder with a `RUN.md` that records the stage and each approval, so an interrupted run can be resumed.

## Prerequisites

- Claude Code
- The HyperFrames skills, including `faceless-explainer`: `npx hyperframes skills`
- Node.js with `npx`
- Python 3
- `ffmpeg` and `ffprobe` on your path
- Optional: the GitHub CLI (`gh`), signed in, to read GitHub links

## Install

Clone it into your skills folder:

```bash
git clone <repository-url> ~/.claude/skills/spec-reel
```

Or clone it somewhere else and link it:

```bash
git clone <repository-url> ~/skills/spec-reel
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
| `voice_source` | `faceless` (faceless-explainer's engine, default) or `own` (your own engine). |
| `voice` | A voice id for faceless-explainer's engine. Empty means its remembered or default voice. |
| `tts_command` | Default command for your own engine. Empty means you drop audio files. |

## Voice sources

**faceless-explainer's engine** (default). faceless-explainer picks a provider from your sign-in status and sends the approved script text to it. The skill tells you this before you approve the script.

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

The tests use fakes for ffmpeg, ffprobe and transcription, so they need none of them.
