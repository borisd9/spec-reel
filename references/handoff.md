# Build, voice and render

After gate 2 (the approved script), this skill voices the script, plans the frames, builds one scene per line with the installed HyperFrames explainer route, and renders. Everything that can be a command is one (`scripts/`); this file says when to run which.

Do not invoke the `hyperframes` skill through the Skill tool; it may be disabled for model invocation. Read its files directly. Its folder is `~/.claude/skills/hyperframes/`; the explainer route is `~/.claude/skills/hyperframes/references/types/explainer.md`, and `format.md`, `film.md` and `sound.md` in the same `references/` folder hold the render contract, the pacing and the sound rules.

When resuming at stage `scenes`, read this file and the explainer route again, then continue from `STORYBOARD.md`'s `status` lines.

## Files this skill needs

At `init`, before anything else, check these exist, and stop naming each one that does not (the fix is `npx hyperframes skills`):

```bash
for f in SKILL.md references/types/explainer.md references/film.md references/format.md references/sound.md; do
  test -f ~/.claude/skills/hyperframes/$f || echo "missing: ~/.claude/skills/hyperframes/$f"
done
```

Also stop when `npx hyperframes check --help` fails: the layout check and the stills need a CLI that has `check` and `snapshot --at`.

## The order, with what overlaps

1. Gate 2 approves `user_script.txt`. Run the script check (below), then start voicing and adopting **in the background** (`run_in_background`): Qwen3-TTS and the transcription take minutes and nothing below needs them until the build.
2. Meanwhile write `STORYBOARD.md`, get the frame plan reviewed (interactive mode), and write the scenes. Cues need `audio_meta.json` only when `build_index.py` runs.
3. When the voice is adopted: speech check, voice check, then `finish.py --review` and look at the stills.
4. After approval, `finish.py --final`.

## STORYBOARD.md

Write it into the run folder after `init`. Shape per `~/.claude/skills/hyperframes/references/storyboard-format.md`. One frame per line of `user_script.txt`, in the same order, with the same spoken words (`voiceover`). Labels, `Time` and `Delivery` may change, except that Line 1 stays labeled `Intro`.

```markdown
---
format: 1920x1080
duration: <target length from the run answers, e.g. 75s>
message: "<one sentence from the run answers: the one thing the video must say>"
arc: Intro → Why → Change → Proof → Next
audience: "<from the run answers>"
mode: collaborative        # autonomous in yolo mode
music: none
captions: <config captions>
---

## Frame 1 — Intro
- on_screen_title: "<the digest's Title, word for word>"
- src: compositions/intro.html
- voiceover: "<Line 1's spoken text>"
```

- Frame 1 is the intro: the approved title as the dominant on-screen text, nothing competing with it, and the intro line as the narration. The title is on screen from frame 0, because it becomes the cover.
- Every frame has `src: compositions/<id>.html`, `<id>` a short readable name (`intro`, `rules`, `leak`). `build_index.py` reads the scene ids from these lines.
- Every other frame gets a scene card: `- scene_job:` one of `why`, `change`, `proof` or `next`; for a `change` frame also `- before:` and `- after:` (what was true, what is true now). Demo frames need no `scene_job`.

  ```markdown
  ## Frame 3 — Retries
  - scene_job: change
  - before: "A failed upload had to be restarted by hand."
  - after: "A failed upload retries on its own."
  ```

- The screen and the voice do two jobs. The screen shows the noun or the number; the voice carries the sentence. They never show the same sentence.
- Each Demo frame names its demo file and builds around it, per `references/demo.md` § In the script and the scenes.

### Script check

Run it right after gate 2 and again once `STORYBOARD.md` exists:

```bash
python3 -I <this skill's directory>/scripts/adopt_voice.py . --check-script
```

It regenerates `SCRIPT.md` from `user_script.txt` (see Facts below), then fails when the script does not open with `## Line 1 — Intro (Frame 1)`, when that line is longer than 20 written words, when a `public/demo-*` file has no Demo line, and, once `STORYBOARD.md` exists, when Frame 1 has no `on_screen_title`, a demo file has no frame naming it, or a frame other than the intro and the Demo frames has no `scene_job` (or a `change` frame has no `before` and `after`). It also **warns** (it does not fail) about words the voice may misread: identifiers with `_` or a hyphen and a digit, digits stuck to letters, lowercase acronyms. For each warning, reword the line or add a respelling (below). When it fails:

- a missing or empty `on_screen_title` is fixed by writing the approved title into Frame 1;
- a demo file with no frame naming it is fixed by adding its `asset_candidates` line to its Demo frame; a missing Demo line re-opens gate 2;
- a wording change the user asked for at the plan review is applied to `user_script.txt` first, gate 2 is re-approved and its new SHA-256 recorded in `RUN.md`;
- a missing `scene_job`, `before` or `after` is fixed by adding the line to that frame, taken from the approved digest.

### Facts

One owner per fact. `user_script.txt` is the only script file you edit: `adopt_voice.py` and `qwen_voice.py` write `SCRIPT.md` from it, so never edit `SCRIPT.md`. A fact that appears in several places (a ticket number, a branch, a title) lives in `facts.json` at the run folder root, a flat `{"key": "text"}` object:

- the script and the caption write `{{key}}`; the script's is filled in when `SCRIPT.md` is generated (an unknown key fails, naming it), the caption's when `finish.py --final` writes `renders/share-copy.txt` from `renders/share-copy.template.txt` (when that file exists);
- scenes read it with `f.fact("key")`; `build_index.py` also declares each key as a composition variable;
- how it is spoken comes from the respellings (below), not from a second copy.

Changing a fact changes every scene on the next `finish.py` run. A spoken fact also needs its lines re-voiced: `qwen_voice.py --frames-with <word>`.

## Scenes

Read `~/.claude/skills/hyperframes/references/types/explainer.md` first: one idea, one concrete example worked through, a diagram that grows, the voice as the clock. Then build one scene per frame:

1. Copy `assets/scene.template.html` to `compositions/<id>.html` and replace `SCENE_ID`. The shared vocabulary (`.stage`, `.eyebrow`, `.title`, `.card`, `.label`, `.num`, `.tag`...) and the `window.fx` helpers (`blur`, `rise`, `slide`, `pop`, `fade`, `grow`, `type`, `exit`, `at`, `fact`) live in the run's `index.html`, which `build_index.py` writes from `assets/index.template.html`. The template is the `blue-professional` preset with Space Grotesk (bundled in `assets/fonts/`, copied into the run by the build). For another preset, copy the template to `build/index.template.html` in the run and restyle it; `build_index.py` prefers that copy.
2. **Cue by word text.** `at("feed")` is the start of the first "feed" in the line, `at("draft", 2)` of the second. It survives edits to the words before it. `w(i)` (by word index) still works but breaks when words are added. `build_index.py` checks every `at()` against the line's words and fails the build for a word that is not there.
3. **Nothing that stops fast capture.** No CSS filters (`blur`, `drop-shadow`, `backdrop-filter`): one makes the renderer fall back from fast capture to screenshot capture. `fx.blur` is a fade with a small rise and `fx.exit` a fade with a lift; use opacity and `y`. And every effect is a tween of elements, never a callback that edits the page (`onUpdate` writing `textContent`): callbacks do not run on a seek, so a frame captured by a jump differs from the sequential one, fast capture's self-check fails and the whole render restarts the slow way. `fx.type` types with one span per character for that reason. `finish.py` fails on a `blur(` with a size and on `onUpdate:`.
4. Every name, number, date, status or capability on screen comes from the approved digest or `sources/`, and the tense matches the point's status tag (claim check, below). A concept a `next` scene names gets one sentence on what it will do (`references/style.md`).
5. Text stays inside the 90% action-safe box and is at least 28 px at 1080.

Do not hand-edit `index.html`: `scripts/build_index.py` (run by `finish.py`; by hand: `python3 -I <this skill's directory>/scripts/build_index.py .`) writes it from `audio_meta.json`, `STORYBOARD.md` and `facts.json` (one host and one voice clip per frame, each slot the line's measured voice plus the pause).

### Claim check

Before the preview review, read every built scene (`compositions/<id>.html`) and list the text a viewer sees, including text that scripts type or reveal.

- **Must be grounded:** names, numbers, dates, statuses, capabilities and quotes. Each must appear in the approved digest (`capture/extracted/visible-text.txt`) or in `sources/`. Re-cased, shortened or split across elements is fine; invented is not.
- **Tense must match status:** a line about a `[planned]` or `[in progress]` point must read as future or ongoing ("will", "coming"), never as done. A "shipped" look (a done check mark, "now live", "released") on such a point is ungrounded.
- **A named concept needs its sentence:** a `next` scene that names a job, check, flag or component the video never explained (and the voice does not explain either) is flagged. Add one sentence on what it will do, or stop naming it.
- **Free to invent:** framing and connective text that asserts nothing, such as "Here's what changes" or "Next up".
- **Fix an ungrounded line** with the cheapest edit to that scene's HTML, using the digest's own wording.

Record `claim check: <lines checked> lines, fixed <frame ids | none>` under `## Render` in `RUN.md`. Run it again, on the changed scenes, after any change request.

## Voicing

Both voice sources end the same way: one audio file per script line in `voice-in/`, then `adopt_voice.py`.

### Pronunciation

`qwen_voice.py` always respells these for the voice only (the script and captions keep the written form): `id` as `I-D`, `ids` as `I-Ds`, `PR` as `P R`, `v8` as `V-eight`. Config `pronunciations` adds to them or replaces one: pass `--say <written>=<spoken>` for each entry. So write `PR 12` in the script, not "P R twelve". A word the voice still gets wrong is fixed with one more `pronunciations` entry, never by respelling the written script.

### Qwen3-TTS (default)

Runs on this Mac (Apple Silicon) with Qwen3-TTS through MLX-Audio. The script text does not leave the machine. From the project folder:

```bash
uv run -q --python 3.11 --with mlx-audio==0.6.1 --with soundfile \
  python <this skill's directory>/scripts/qwen_voice.py . --speaker <config qwen_speaker>
```

When the run's voice source is `clone`, add `--clone-audio "<config qwen_clone_audio>" --clone-transcript "<config qwen_clone_transcript>"` (then `--speaker` and `--instruct` are not needed): the lines are voiced in the speaker of that recording, one sentence at a time with a short pause between them. Add `--tempo <config qwen_tempo>` when it is not `1.0`: it slows (below 1) or speeds the voice after generation, without changing pitch.

Append `--say <written>=<spoken>` for each entry of config `pronunciations`. Add `--instruct "<config qwen_instruct>"` when that value is set; when it is empty the script uses a calm, conversational narrator. The first run downloads the model (about 4 GB) into the Hugging Face cache; later runs load it in seconds. It writes `voice-in/NN.wav` for every line, or only the lines named with `--frames <N...>` or `--frames-with <word>` (the frames whose spoken text has that word or its plural; pick frames by word, never by grep line numbers).

Before it replaces a file it copies it into `voice-takes/<timestamp>/`. `--restore <timestamp> --frames <N...>` puts a take back (without `--frames`, every file in it); the file it replaces is saved too. Never delete `voice-takes/`.

When it fails because the Mac is not Apple Silicon or MLX-Audio cannot load, stop, say so, and offer the user's own engine instead (switch per the voice check below).

### The user's own engine

1. Parse the final `SCRIPT.md` and show the user each line as: frame number, spoken text, target file `voice-in/NN.<ext>` (`NN` is the two-digit frame number; `<ext>` is `wav`, `mp3`, `m4a` or `aiff`).
2. Get the audio.
   - **The user names a TTS command** (or the config `tts_command` is set; a command named at run time overrides it for that run): write each line's text to a temp file and run the command once per line, one line at a time. `{text_file}` becomes that temp file and `{out}` becomes `voice-in/NN` with no extension; the command supplies its own extension, for example `say -v Samantha -f {text_file} -o {out}.aiff`. Spoken text reaches the command only through `{text_file}`, never inline. A command without both placeholders is completed by asking the user, never by putting the text inline. A command never contains a credential: it reads any key itself from an environment variable or a file outside the skill folder. Record in `RUN.md` only that a command was used, never its text.
   - **Otherwise** wait for the user to drop one file per line into `voice-in/`.

### Adopt (both sources)

From the project folder run:

```bash
python3 -I <this skill's directory>/scripts/adopt_voice.py . --pause <config slide_pause_s>
```

It writes `SCRIPT.md` from `user_script.txt`, converts each file to `assets/voice/NN.wav` (44.1 kHz mono), reads its length, gets word timings with `npx hyperframes transcribe`, and writes `audio_meta.json` and `audio_engine_meta.json`. A transcript is remembered by the converted WAV's SHA-256 in `voice-cache/<sha>.json`, so a re-run transcribes only the files that changed. It exits non-zero and lists the lines with a missing file, several files, an unreadable file, or no words; no meta file is written then. A re-run keeps any `bgm`, `sfx` and host entries already in the meta files and replaces only `voices`. It writes the script's own words onto the transcript timings, so captions and cues read as scripted, and lists any line where the transcript differs in a way a listener would hear (the transcript is saved in `voice_heard.json`).

## Speech check (Qwen3-TTS)

Run `python3 -I <this skill's directory>/scripts/adopt_voice.py . --check-speech`. It lists real differences only: case, spaces and hyphens inside a word, digits for number words, and the respellings are not differences. It applies to the cloned voice exactly as to the built-in speaker. For each listed frame, re-voice it with `qwen_voice.py --frames <N...>` and re-run `adopt_voice.py . --pause <s>`; at most two retake rounds. If a frame still differs, open its `voice-in/NN.wav` for the user and ask once: keep it, reword the line (re-opens gate 2), or add a `pronunciations` entry and retake. For the own engine, show the list and let the user decide.

## Voice check

```bash
python3 -I <this skill's directory>/scripts/adopt_voice.py . --check
```

It confirms that every frame whose storyboard `voiceover` is non-empty has a voice entry in `audio_meta.json` with an existing WAV and a non-empty `words` list. Silent frames are skipped. `finish.py` runs it; run it by hand after any re-voice.

**On failure:** stop before building. Say: "These scenes have no voice or word timings: <frame list>. Voice source: <Qwen3-TTS | cloned voice | your own engine>." Then offer the other voice source: the default Qwen3-TTS speaker when the clone failed, the user's own engine when Qwen3-TTS failed. On yes: record the new source in `RUN.md`, delete `audio_meta.json`, `audio_engine_meta.json`, `voice-in/`, `voice-cache/` and `assets/voice/`, and continue from the voicing step with the new source. A run never mixes sources.

## Review and render: `finish.py`

Each is one command from the project folder; it stops at the first failing step, names it, and prints each step's run time.

```bash
python3 -I <this skill's directory>/scripts/finish.py . --review
python3 -I <this skill's directory>/scripts/finish.py . --final
```

- `--review` (seconds): adopt, voice check, `build_index.py`, the blur lint, then `npx hyperframes check --at <times>` and `npx hyperframes snapshot --at <times> --no-end` on the scenes that changed since the last finish run. The times are the last 0.5 s of each changed scene. A scene counts as changed when its WAV hash or its `compositions/<id>.html` modification time differs from the state recorded under `## Finish state` in `RUN.md`, or when `facts.json` changed. An overflow, a lint error or a contrast failure fails the step. The stills are in `review/snapshots/`: show them to the user. This is the review loop: no full render.
- `--final` (one render): adopt, voice check, build, the blur lint, `npx hyperframes render . -o renders/video.raw.mp4`, then `renders/video.mp4` from it with the loudness normalized to -16 LUFS (`scripts/qc_video.py --normalize`), the video QC (`qc_video.py --check <target>`: H.264 `yuv420p` at 1920x1080, an audio stream, no black span of 0.5 s or more, length within 12% of the target), the cover, and the sync, QC and cover lines appended to `RUN.md`. The target comes from `- target:` under Answers in `RUN.md` (seconds, or a range like `60-90`; yolo: `75`), or `--target`.

The cover: chat apps and most players show a video's first frame as the thumbnail, and a raw render starts on a fade. `--final` pulls a frame about 60% through Frame 1's voice (the title fully on screen) into `renders/cover.jpg` and overlays it on frame 0 only; the length and the audio stay the same. Look at `renders/cover.jpg`; when the title is still animating in or a transition shows, move the time by 0.3 seconds and make it again by hand with `ffmpeg -ss <s> -i renders/video.raw.mp4 -frames:v 1 -q:v 2 renders/cover.jpg` and the same overlay filter.

Speed, measured on a 3-minute, 17-scene video: with CSS blur filters the render took 3 m 30 s to 3 m 54 s (screenshot capture); without them, fast capture takes 1 m 55 s on one worker, and 45 s with `HF_DE_PARALLEL_ROUTER=true`, which `finish.py` sets for the render (same frames, PSNR 72 dB). The render log must not hold a `falling back to screenshot` line; when it does, a scene breaks fast capture: look for a callback that edits the page. Transcription uses Whisper `medium.en` explicitly (`--engine whisper`): Parakeet was no faster on this video (42 s against 43 s for 17 files) and misheard more words. Segmented capture (`HF_SEGMENTED_CAPTURE`, `--resume`) failed on this video (`suspect small frame`), so it is not used.

A sync difference above 2 seconds (voice total against the MP4's length) is written to `RUN.md` with a note; report it to the user before marking the run `done`. A QC failure does not stop `--final`: it records `qc: fail` in `RUN.md`, still adds the cover, and exits non-zero at the end. Report it to the user before marking the run `done`. Any other failing step stops the command; `SKILL.md` § Scenes says which failures to fix without asking.

## After the render

1. Write `renders/share-copy.txt`: one to three sentences to post with the video in a team channel, for the run's audience and intent. Every claim in it comes from the approved digest; it names no customer or person and carries no personal data, link to an internal page or credential. Plain words, no "excited to share". Check it against `references/style.md` and fix what fails. A fact in it that lives in `facts.json` is written `{{key}}` in `renders/share-copy.template.txt` instead, so `finish.py --final` keeps it in step.
2. Set `RUN.md` stage to `done`.
3. Report: the MP4 path, its length, the sync difference, the QC result, the cover time, the caption text, and the frame ids, so the user can ask for a single-scene change or a caption edit.

## Change requests

A change request at the preview rebuilds only the scenes the user names, plus any scene whose length changes. It never starts a full render.

1. Edit the named `compositions/<id>.html`. When a scene's spoken text changed: update that line in `user_script.txt` only, record its new SHA-256 and the change time in `RUN.md` as the user's approval of that edit, re-voice it (Qwen3-TTS: `--frames <N>`, or `--frames-with <word>` for a pronunciation fix; own engine: replace `voice-in/NN.<ext>`).
2. Run `finish.py . --review`. Show the stills of the changed scenes. A length change moves every later scene; the cues follow the words, so only a scene whose own words changed needs editing.
3. Run the claim check on the changed scenes.
4. Render with `finish.py . --final` only after the user approves, or once at the end in yolo mode.

**A change that brings a new source** (a link or file the digest did not use):

1. Save it under `sources/` per `references/sources.md` (next number, same format).
2. Add its points to the digest (`capture/extracted/visible-text.txt`) with their status tags; a fact it lacks is `[NEED: ...]`.
3. Record the re-opened gate 1 in `RUN.md` under `## Approvals`: the time and the new SHA-256 (interactive: the user approves the extended digest; yolo: `auto (yolo)`).
4. Rewrite the affected script lines (gate 2 re-opens for them), re-voice them, rebuild the scenes, run the claim check on the changed frames.

Every voice generation in a run, including re-voicing, goes through the run's chosen voice source. A run never mixes the two sources.
