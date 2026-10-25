# Spec Reel

[![skills.sh](https://skills.sh/b/borisd9/spec-reel)](https://skills.sh/borisd9/spec-reel)

<img width="1024" height="572" alt="Spec Reel logo" src="https://github.com/user-attachments/assets/586ad0a4-15ee-4b85-a283-3bf0f9c668e2" />

An agent skill (Claude Code, Codex, Cursor and other agents that read `SKILL.md`) that turns links to plans and specs into a short narrated explainer video.

You give it one or more links or files. It reads them, writes a digest of why each plan exists, what it changes and what comes next, and writes a timestamped narration script. You approve both. It voices the script on your Mac with [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice) through [MLX-Audio](https://github.com/Blaizzy/mlx-audio), optionally in your own cloned voice, or takes audio you make with any text-to-speech tool you choose. Then it builds one scene per script line with the HyperFrames explainer route, each cued on the words of its narration, and renders an MP4.

Every video opens with an intro scene: the approved title on screen, narrated by one short sentence on what the video is about. When the feature can be shown, a demo scene shows it: a mock or a screen recording found in your sources or given by you. You can skip the demo.

How a run goes:

1. Read your links and files.
2. Write a digest, a title and a demo choice. You approve or edit.
3. Write the narration script. You approve or edit.
4. Voice the script on your Mac, in the background, while the frame plan is written. You review the frame plan.
5. Build one scene per line, cued on the words of the narration.
6. Check that every fact on screen comes from your sources.
7. Look at stills of the scenes (`finish.py --review`, seconds, no render). You approve or ask for changes; a change rebuilds only the scenes you name.
8. Render the MP4 once (`finish.py --final`), normalize its loudness and check its format and length.
9. Put the title on the first frame as the cover, and write a share caption.
10. Report what was made.

With `--yolo`, the skill makes every approval itself and lists those decisions in the report (see [First run](#first-run)).

Every run has its own folder with a `RUN.md` that records the stage and each approval, so an interrupted run can be resumed.

## Prerequisites

- A coding agent that reads Agent Skills (`SKILL.md`)
- The HyperFrames skills: `npx hyperframes skills` (the skill offers to run this when they are missing)
- Node.js with `npx`
- Python 3.10 or later
- `ffmpeg` and `ffprobe` on your path
- For the default voice: an Apple Silicon Mac and [`uv`](https://docs.astral.sh/uv/). The skill runs Qwen3-TTS with `uv run --with mlx-audio`, so there is nothing else to install; the model (about 4 GB) downloads on first use. On other machines, use your own engine.
- Optional: the GitHub CLI (`gh`), signed in, to read GitHub links

## Install

```bash
npx skills add borisd9/spec-reel
```

Or clone it into your skills folder (`~/.claude/skills/` for Claude Code, or the skills folder your agent reads):

```bash
git clone https://github.com/borisd9/spec-reel.git ~/.claude/skills/spec-reel
```

Or clone it somewhere else and link it:

```bash
git clone https://github.com/borisd9/spec-reel.git ~/skills/spec-reel
ln -s ~/skills/spec-reel ~/.claude/skills/spec-reel
```

Start a new agent session. `spec-reel` appears in the skill list.

To update later, re-run `npx skills add borisd9/spec-reel`, or pull in the folder you cloned: `git -C ~/.claude/skills/spec-reel pull` (or `~/skills/spec-reel` for a linked clone).

## Configure

```bash
cp config.example.json config.json
```

`config.json` is ignored by git. The skill creates it and asks for any missing value on the first run, so this step is optional.

| Field | Meaning |
|---|---|
| `output_root` | Where run folders go. Default `~/Movies/hyperframes`. |
| `style_preset` | The look of the scenes. Default `blue-professional`, the one the bundled scene template implements; for another, restyle a copy of `assets/index.template.html` as `build/index.template.html` in the run. |
| `voice_source` | `qwen` (Qwen3-TTS on your Mac, default) or `own` (your own engine). `clone` (your cloned voice) is opt-in: the skill offers it at the voice question and never sets it. |
| `qwen_speaker` | `Aiden` (default) or `Ryan`, the two English voices. |
| `qwen_instruct` | A style instruction for Qwen3-TTS. Empty means a calm, conversational narrator. |
| `qwen_clone_audio` | Path to a recording of the voice to clone (`~` allowed). Empty by default; setting it does not select the clone. |
| `qwen_clone_transcript` | Path to a text file with exactly what that recording says. Empty by default. |
| `qwen_tempo` | Pace of any Qwen3-TTS voice, `0.5` to `2.0`; below `1.0` is slower, pitch unchanged. Default `1.0`. |
| `tts_command` | Default command for your own engine. Empty means you drop audio files. |
| `slide_pause_s` | Seconds of silence after every line but the last. Default `1.0`. |
| `captions` | `off` (default) or `on`. |
| `pronunciations` | Respellings for Qwen3-TTS, added to the built-in ones (`id`, `ids`, `PR`, `v8`), for example `{"KBs": "K-Bs"}`. Default `{}`. |

## Voice sources

**Qwen3-TTS** (default). Runs locally through MLX-Audio, so the script text never leaves your machine. Model: `mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16` (Apache-2.0). On an Apple Silicon Mac it generates speech faster than real time: about a minute for 90 seconds of narration, after the first model load. To voice a script by hand:

```bash
uv run --python 3.11 --with mlx-audio==0.6.1 --with soundfile \
  python scripts/qwen_voice.py <run folder> --speaker Aiden
```

**Your cloned voice (optional).** Pick it at the voice question of a run; it is never the default. Record 10 to 20 seconds of clear speech as a WAV file and write exactly what you say into a text file. The skill asks for both paths the first time and remembers them in `config.json`. Use only your own voice, or the voice of someone who agreed to it being cloned. It is still Qwen3-TTS on your Mac, with the Base model (`mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16`, downloads once, about 4 GB). Cloned speech often comes out faster than the speaker talks: set `qwen_tempo` to about `0.8` if it sounds rushed. By hand:

```bash
uv run --python 3.11 --with mlx-audio==0.6.1 --with soundfile \
  python scripts/qwen_voice.py <run folder> --clone-audio me.wav --clone-transcript me.txt --tempo 0.8
```

**Your own engine.** The skill lists every script line with its frame number and a target file name, `voice-in/NN.<ext>`. Either drop one audio file per line (WAV, MP3, M4A or AIFF), or give a command and the skill runs it once per line. In a command, `{text_file}` is a temp file holding the line's text and `{out}` is `voice-in/NN` with no extension; the command supplies its own extension:

```bash
say -v Samantha -f {text_file} -o {out}.aiff
```

The spoken text reaches the command only through `{text_file}`. A command never contains a credential: if your tool needs a key, the command reads it from an environment variable or a file outside this folder. The skill refuses to save a command that contains a key.

`scripts/adopt_voice.py` then converts the files to WAV, gets word timings with `npx hyperframes transcribe`, and writes the audio metadata the build reads. It keeps the script's own words on the transcript timings and reports lines that were heard differently (`--check-speech`; spelling-only differences are not reported). A transcript is remembered by the audio's hash, so changing one line means replacing one file and running it again: only that file is transcribed. To re-voice by word, `qwen_voice.py --frames-with id`; every voicing first copies the files it replaces into `voice-takes/`, and `--restore` puts a take back.

## First run

Ask your agent to use spec-reel on your links. In Claude Code:

```text
/spec-reel https://example.com/plan ~/plans/feature-spec.md
```

For a run with no questions at all, add `--yolo`:

```text
/spec-reel --yolo https://example.com/plan ~/plans/feature-spec.md
```

It uses the defaults (a team update, about 75 seconds, the configured voice), decides every review itself, renders the MP4, and ends with a list of everything it decided without you. It never posts or shares the video. Your agent may still ask permission to run commands (`npx`, `ffmpeg`, `uv`, `curl`, `gh`) unless your permission mode allows them.

Without `--yolo`, the skill asks, in one batch: the links or files, the audience and intent, the target length (default 60-90 seconds) and the voice source. Then approve the digest, approve the script, review the frame plan, and approve the stills before the render. Before the stills, the skill checks that every name, number and capability shown on screen comes from your sources.

`scripts/finish.py <run> --review` and `--final` are the two commands that follow any change: adopt the voice, build `index.html`, check the scenes, and (for `--final`) render, normalize the loudness to -16 LUFS with `scripts/qc_video.py`, check the MP4's format, audio, black spans and length, and add the cover. `--review` looks only at the scenes that changed since its last run. Scenes use no CSS filters, so the renderer stays in fast capture.

Inside the run folder, `renders/` then holds:

- `video.mp4`, whose first frame is the intro title, so chat apps show it as the thumbnail;
- `cover.jpg`, that same frame, for platforms that take a separate thumbnail;
- `share-copy.txt`, a one-to-three-sentence caption to post with the video.

## Tests

```bash
python3 -I -m unittest discover -s scripts -p 'test_*.py' -v
```

The tests use fakes for ffmpeg, ffprobe, transcription and the Qwen3-TTS model, so they need none of them. `scripts/test_skill_structure.py` also checks that the documents agree: every named file and link exists (scripts, references, assets), no document names a retired skill, one agent's skill folder or tool names, and `config.example.json` matches the table above.

Every pull request runs `.github/workflows/checks.yml`: these tests on Linux and macOS, `ruff`, a gitleaks secret scan, and a scan for names the repository keeps private (its word list is a repository secret, so pull requests from forks skip it).

## Credits

The cover frame, the share caption and the on-screen claim check are adapted from [brag](https://github.com/latent-spaces/brag) by Shunit Haviv Hakimi (MIT).

Change-line, style and scene-card rules adapted from [marketingskills](https://github.com/coreyhaines31/marketingskills) (MIT, Corey Haines) and [story-skills](https://github.com/danjdewhurst/story-skills) (MIT).

## License

MIT, see [LICENSE](LICENSE). The Qwen3-TTS model it downloads is Apache-2.0.
