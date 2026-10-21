# Handoff to faceless-explainer

After gate 2 (the approved script), this skill writes `BRIEF.md` and then drives the installed faceless-explainer skill (its `SKILL.md`, Steps 0-6) with the five deltas below. Nothing in faceless-explainer is copied or patched here.

Do not invoke the `hyperframes` skill through the Skill tool; it may be disabled for model invocation. Read the installed faceless-explainer `SKILL.md` and the files it points to directly. faceless-explainer is installed in the user's Claude Code skills folder (`~/.claude/skills/faceless-explainer/SKILL.md`); its `<SKILL_DIR>` is that folder.

When resuming at stage `faceless`, re-read faceless-explainer's `SKILL.md` and this file before acting, then continue from the storyboard's frontmatter, as faceless-explainer's Step 0 rule (1) describes when `BRIEF.md` exists.

## BRIEF.md

Write it into the run folder right after `npx hyperframes init` (the run folder is initialized first, so this file is written after it). Shape per the installed HyperFrames `references/brief-format.md`. faceless-explainer Step 0 then finds it and asks nothing.

```markdown
---
workflow: faceless-explainer
flow: automation
storyboard: yes
message: "<one sentence from the run answers: the one thing the video must say>"
audience: "<from the run answers>"
destination: desktop
aspect: 1920x1080
language: en
length: <target length from the run answers, e.g. 75s>
angle: narrative
style_preset: <config style_preset>
narration: yes
vo_mode: verbatim
---

## Intent

<One short paragraph: what the video is, for whom, and the intent from the run answers.>
Beat order: the intro (the title "<the digest's Title>" on screen and one sentence on what the
video is about), then why it exists, what it changes, what comes next. The approved script is in
`user_script.txt`; keep its wording.

## Notes

- faceless-explainer deltas in force: skip the update question and continue offline at Step 0; this skill's voicing replaces Step 3.1; voice check after voicing, after fetch-sfx and after any re-voice; script lines one-to-one with frames, Frame 1 the title intro; Step 6 rebuilds named frames only. Full text: <this skill's directory>/references/handoff.md.
- music: none (the storyboard sets `music: none`; captions stay on).
- Voice: <"Qwen3-TTS · <config qwen_speaker>" or "the user's own engine">, voiced by this skill.
```

Replace `<this skill's directory>` with the real absolute path when writing the file. `storyboard: yes` with `flow: automation` is the collaborative mode: the user reviews the frame plan, the sketch board and the preview.

`user_script.txt` already sits at the project root, where faceless-explainer Step 1 saves a user script. `capture/extracted/visible-text.txt` (the approved digest) and `tokens.json` already exist; Step 1 checks they exist and does not rewrite them.

## The five deltas

Everything else in faceless-explainer runs as written, including Step 5's `sync-durations` and `fetch-sfx`.

1. **Skip the "keep this skill fresh" update question**, because `init` already updated the skills. **At Step 0's sign-in status, relay it and continue offline**: this skill makes the narration and music is `none`, so no hosted provider is needed.
2. **This skill's voicing replaces Step 3.1.** Never run faceless-explainer's `audio.mjs` voice generation. Do the voicing steps below at the same point: after the Step 3 plan approval, before Step 4.
3. **Voice check** (below) after voicing, again after Step 5's `fetch-sfx`, and after any re-voice.
4. **Script lines map one-to-one onto frames, and Frame 1 is the title intro.** In Step 3, write one frame per line of `user_script.txt`, in the same order, with the same spoken words. Labels, `Time` and `Delivery` may change, except that Line 1 stays labeled `Intro`. Frame 1 is the intro scene:

   ```markdown
   ## Frame 1 — Intro
   - on_screen_title: "<the digest's Title, word for word>"
   - voiceover: "<Line 1's spoken text>"
   ```

   Its narrative asks for the title as the dominant on-screen text, nothing competing with it, and the intro line as the narration. This replaces faceless-explainer's opening-hook guidance for Frame 1; its hook strategy applies from Frame 2. After the Step 3 plan approval and before any voicing, run the script check:

   ```bash
   python3 -I <this skill's directory>/scripts/adopt_voice.py . --check-script
   ```

   It also fails when `user_script.txt` does not open with `## Line 1 — Intro (Frame 1)`, when that line is longer than 20 words, or when `STORYBOARD.md` Frame 1 has no `on_screen_title`. When it fails:
   - a missing or empty `on_screen_title` is fixed by writing the approved title into Frame 1, and the check runs again;
   - a wording change the user asked for at the Step 3 plan review is applied to `user_script.txt` first, gate 2 is re-approved and its new SHA-256 recorded in `RUN.md`, `SCRIPT.md` is updated to match, and the check runs again;
   - any other mismatch is fixed by rewriting `SCRIPT.md`'s spoken lines from `user_script.txt`, and the check runs again.
5. **Step 6 change requests rebuild only the named frames**, one frame worker each. When a named frame's spoken text changed:
   1. Update that line in both `user_script.txt` and `SCRIPT.md`.
   2. Record the new SHA-256 of `user_script.txt` and the change time in `RUN.md` as the user's approval of that edit.
   3. Re-voice that line alone. Qwen3-TTS: run `qwen_voice.py` with `--frames <N>`. Own engine: replace that line's `voice-in/NN.<ext>` file. Then run `adopt_voice.py .`.
   4. Run the voice check.
   5. Run `sync-durations` and `captions.mjs build`, then rebuild every frame whose duration changed.

   Every voice generation in a run, including re-voicing, goes through the run's chosen voice source. A run never mixes the two sources.

## Voicing (replaces Step 3.1)

Both voice sources end the same way: one audio file per script line in `voice-in/`, then `adopt_voice.py`.

### Qwen3-TTS (default)

Runs on this Mac (Apple Silicon) with Qwen3-TTS through MLX-Audio. The script text does not leave the machine. From the project folder:

```bash
uv run -q --python 3.11 --with mlx-audio==0.6.1 --with soundfile \
  python <this skill's directory>/scripts/qwen_voice.py . --speaker <config qwen_speaker>
```

Add `--instruct "<config qwen_instruct>"` when that value is set; when it is empty the script uses a calm, conversational narrator. The first run downloads the model (about 4 GB) into the Hugging Face cache; later runs load it in seconds. It writes `voice-in/NN.wav` for every line, or only the lines named with `--frames`.

When it fails because the Mac is not Apple Silicon or MLX-Audio cannot load, stop, say so, and offer the user's own engine instead (switch per the voice check below).

### The user's own engine

1. Parse the final `SCRIPT.md` and show the user each line as: frame number, spoken text, target file `voice-in/NN.<ext>` (`NN` is the two-digit frame number; `<ext>` is `wav`, `mp3`, `m4a` or `aiff`).
2. Get the audio.
   - **The user names a TTS command** (or the config `tts_command` is set; a command named at run time overrides it for that run): write each line's text to a temp file and run the command once per line, one line at a time. `{text_file}` becomes that temp file and `{out}` becomes `voice-in/NN` with no extension; the command supplies its own extension, for example `say -v Samantha -f {text_file} -o {out}.aiff`. Spoken text reaches the command only through `{text_file}`, never inline. A command without both placeholders is completed by asking the user, never by putting the text inline. A command never contains a credential: it reads any key itself from an environment variable or a file outside the skill folder. Record in `RUN.md` only that a command was used, never its text.
   - **Otherwise** wait for the user to drop one file per line into `voice-in/`.

### Then, for both sources

From the project folder run:

```bash
python3 -I <this skill's directory>/scripts/adopt_voice.py .
```

It converts each file to `assets/voice/NN.wav` (44.1 kHz mono), reads its length, gets word timings with `npx hyperframes transcribe`, and writes `audio_meta.json` and `audio_engine_meta.json` in the shapes faceless-explainer reads. It exits non-zero and lists the lines with a missing file, several files, an unreadable file, or no words; no meta file is written then. Re-running is free and rebuilds everything from `voice-in/`. A re-run keeps any `bgm`, `sfx` and host entries already in the meta files and replaces only `voices`.

## Voice check

From the project folder:

```bash
python3 -I <this skill's directory>/scripts/adopt_voice.py . --check
```

It confirms that every frame whose storyboard `voiceover` is non-empty has a voice entry in `audio_meta.json` with an existing WAV and a non-empty `words` list. Silent frames are skipped. Run it:

- after voicing;
- after any re-voice;
- after Step 5's `fetch-sfx`, which rebuilds `audio_meta.json` and can drop voices.

**On failure:** stop before building. Say: "These scenes have no voice or word timings: <frame list>. Voice source: <Qwen3-TTS | your own engine>." Then offer to switch the whole run to the other voice source. On yes: record the new source in `RUN.md`, delete `audio_meta.json`, `audio_engine_meta.json`, `voice-in/` and `assets/voice/`, and continue from the voicing step with the new source. A run never mixes sources.

## Other storyboard settings

The storyboard sets `music: none`. Captions stay on (faceless-explainer's default).

## After render

1. Sync check. Sum `duration_s` over the `audio_meta.json` voices. Add the storyboard padding (the total storyboard duration minus the total voice duration). Read the MP4 length:

   ```bash
   ffprobe -v error -show_entries format=duration -of csv=p=0 renders/video.mp4
   ```

   Record both numbers and their difference in `RUN.md`. A difference above 2 seconds is reported to the user before the run is marked `done`.
2. Set `RUN.md` stage to `done`.
3. Report: the MP4 path, its length, the sync difference, and the frame ids, so the user can ask for a single-scene change.

## Step 6 change requests

A change request at the preview rebuilds only the frames the user names, plus any frame whose length changes. Apply delta 5. Then run faceless-explainer's Step 6 checks again before the render.
