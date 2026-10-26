# A new look every run, and 30 words per scene

Date: 2026-10-26. Status: design, not yet approved.

## Why

Every spec-reel video looks the same. Each run copies `assets/scene.template.html` and builds on one fixed look in
`assets/index.template.html`: the `blue-professional` preset (cream `#fdfae7` ground, one cobalt `#1e2bfa` accent,
Space Grotesk and Inter). The four scene jobs (`why`, `change`, `proof`, `next`) then push each video into the same
few layouts. The user's words: the scenes look samey and template-like.

The installed HyperFrames skill (0.8.150, updated 2026-10-26) now says the same thing from its side:

- `<hyperframes dir>/references/look.md` § Presets: the presets are slide-deck looks, "never as the fallback for a film
  without a brand". It also names Inter, Space Grotesk, Instrument Serif, Geist and JetBrains Mono as "where generated
  design lands".
- `<hyperframes dir>/references/spec.md`: a film's look is written as numbers in a `SPEC.md`, with a BANNED line of
  defaults it must avoid.
- `<hyperframes dir>/references/types/explainer.md` § Shapes of information: pick each line's shape first, so similar
  lines get different pictures.

The `faceless-explainer` skill was the first idea for this. It is no longer published upstream and its installed copy
could not run (eight docs it links to were missing), so nothing here depends on it. spec-reel's tests already ban the
name (`scripts/test_skill_structure.py`, `BANNED`).

## Goals

1. **Each run gets a look made for its subject.** After gate 2 the skill writes three looks, each new and different
   from the others and from the last runs. It renders a short sample of the intro scene in each look, and the user
   picks one (gate 3). The picked look is the run's `SPEC.md` and styles every scene.
2. **Each scene shows its line in its own way.** Every frame names the shape of its information, and two frames in a
   row never share a shape.
3. **A scene's spoken text is at most 30 words.** One script line is one scene. The rule replaces the 30-word sentence
   rule in `references/style.md`.
4. **The review catches template frames.** Before the user sees the review stills, the skill checks them for the
   defaults banned in `SPEC.md` and fixes what it finds.

## Non-goals

- No change to sources, digest (gate 1), script writing (gate 2), voice, discussion mode, `facts.json`, the claim
  check, `finish.py --final`, loudness, video QC or the cover.
- No click-through slide deck. That is the next project. It will reuse this one's per-run look.
- No captions work. Config `captions` still does nothing; that belongs with the deck project, which needs subtitles.
- No brand input. A look comes from the subject. A source that brings its own brand (colors, a logo) may still be used,
  but there is no brand config.
- No HeyGen, no cloud voice, no music. `music: none` stays.

## Anti-goals (this fails even if it works)

- The three looks are the presets with new colors, or one look three times with small changes.
- Every run's looks fall into the same few defaults again (`spec.md` § BANNED by default).
- A look breaks fast capture. No CSS filters, no `onUpdate`, the same rules as today (`finish.py` `BLUR`, `CALLBACK`).
- Picking a look costs the user more than a few minutes of waiting.

## Constraints

- The scene runtime stays. `window.fx` (`blur`, `rise`, `slide`, `pop`, `fade`, `grow`, `type`, `exit`, `at`,
  `fact`), `__WORDS`, `__VO`, `__DUR`, `__FACTS`, and every `%PLACEHOLDER%` in `assets/index.template.html` keep their
  names and behavior. `build_index.py` already uses `build/index.template.html` in the run folder when that file
  exists (`build_index.py:109-111`). A look is that file, restyled.
- Fonts are only the families HyperFrames bundles (`<hyperframes dir>/references/format.md` § fonts: Inter, Montserrat,
  Outfit, Nunito, Oswald, League Gothic, Archivo Black, Space Mono, IBM Plex Mono, JetBrains Mono, EB Garamond,
  Playfair Display, Source Code Pro, Noto Sans JP, Roboto, Open Sans, Lato, Poppins), plus Space Grotesk, which
  spec-reel ships in `assets/fonts/`. No downloads. Inter, Space Grotesk and JetBrains Mono may still be the body or code
  face, never the display face.
- No CSS filters and no `onUpdate` anywhere in a look, as today.
- Standard-library Python only in `scripts/`, with every external command behind a function that tests replace (the
  pattern of `finish.py` `run_command` and `adopt_voice.py` `to_wav`).
- The whole suite passes: `cd scripts && python3 -I -m unittest discover -s . -p 'test_*.py'` (156 tests today). There
  is no linter.

## What was decided

### Gate 3: the look

New stage `look`, between `script` and `scenes`. The stage line in `RUN.md` becomes
`sources | digest | script | look | scenes | done`.

1. Right after gate 2, start voicing and adopting in the background as today (`references/handoff.md` § The order).
2. While they run, write **three looks** into `looks/1-<slug>/`, `looks/2-<slug>/` and `looks/3-<slug>/` in the run
   folder. `<slug>` is the look's name in kebab case. Each look folder holds:
   - `LOOK.md`: the look's name, one line on why it fits this subject, and these lines from the `SPEC.md` template
     (`<hyperframes dir>/references/spec.md`), each with numbers, not adjectives:
     - `LOOK:` ground (hex, texture and how much), ink, one accent and where it may appear, display face, weight, size
       in px and tracking, body face the same, the medium, light and depth;
     - `MOTION:` eases by role (enter, move, exit), durations, and how this medium moves (paper is cut and lifted, ink is
       printed);
     - `BANNED:` the defaults in `spec.md` § BANNED by default, plus what this look must not become.
   - `index.template.html`: a copy of `assets/index.template.html`, restyled for the look. The root variables, the
     `@font-face` rules and the shared classes (`.stage`, `.eyebrow`, `.title`, `.card`, `.label`, `.num`, `.tag`...)
     change. The placeholders and `fx.at`, `fx.fact`, `fx.type` stay the same. The look adds the moves its `MOTION`
     line names to `fx`, under new names, each a `fromTo` tween. The old fade moves (`blur`, `rise`, `slide`, `pop`,
     `fade`, `exit`) stay only so older scenes still work; a new scene uses the look's moves, and the review (below)
     flags a scene where every element fades and rises.
   - `compositions/intro.html`: Frame 1 built in this look, with the approved title (the same rules as every scene).
3. **The three looks differ.** Each uses a different medium, a different display face and a ground from a different
   color family. None is one of the 13 presets in `<hyperframes dir>/assets/frame-presets/` or the old
   `blue-professional` look. Each one differs in medium and display face from the `SPEC.md` of the last five runs under
   config `output_root` (newest first, runs without a `SPEC.md` skipped).
4. **The samples.** When `audio_meta.json` exists, `scripts/look_samples.py .` builds a one-frame project per look and
   renders it: `looks/<n>-<slug>/sample/` holds an `index.html` from that look's template with only Frame 1, its voice
   (`assets/voice/01.wav`) and `compositions/intro.html`; the render goes to `looks/<n>-<slug>/intro.mp4`. The three
   renders run one after another. The script writes nothing outside `looks/`.
5. **Show them.** Open the three MP4s for the user (`open` on macOS) and list, for each, its name, the line on why it
   fits, and its path. Put the recommendation first, with the reason in one clause.
6. **The pick.** The user picks a look, or asks for changes to one (rebuild that look and its sample only), or asks
   for three new ones. Then:
   - copy `looks/<pick>/index.template.html` to `build/index.template.html`;
   - copy `looks/<pick>/compositions/intro.html` to `compositions/intro.html`;
   - write `SPEC.md` at the run folder root: the picked `LOOK.md` lines, plus `GOAL`, `OUTPUT` (1920 x 1080, 30 fps)
     and `TIME` from the run answers. `SHOTS` and `QA` are added once `STORYBOARD.md` exists, and the review may add
     to its BANNED line. `SPEC.md` is a working file and is not hashed;
   - record `- gate 3 (look): <time>  <look name>  sha256 <hash of looks/<pick>/LOOK.md>` under `## Approvals` in
     `RUN.md`. The approved file is `LOOK.md`, which nothing edits after the pick.
7. **Resume.** A changed `looks/<pick>/LOOK.md` re-opens gate 3, then rebuilds every scene. A changed
   `user_script.txt` re-opens gate 2 but keeps the picked look: the intro scene is rebuilt in it when line 1 changed,
   and no new samples are made. Gate 3 re-opens after that only when the user asks for another look.
8. **Yolo.** Write the three looks, skip the samples, take the recommended one, record
   `gate 3 (look): auto (yolo) <time> <look name> sha256 <hash>`, and name the other two in the report's
   **Decided without you** section, one line each.

### Shapes per scene

- Every frame except the intro and the Demo frames gets `- shape:` in `STORYBOARD.md`, next to its `scene_job`. The
  shapes come from `explainer.md` § Shapes of information: `number`, `myth`, `before-after`, `converge`, `network`,
  `chosen`, `steps`, `screenshot`, `quote`, `chapter`.
- `adopt_voice.py --check-script` fails when such a frame has no `shape`, the value is not on that list, or two frames
  in a row have the same shape (frames compared in order, the intro and Demo frames skipped).
- A `change` frame still needs `before` and `after`. `scene_job` stays as it is; the claim check uses it.

### 30 words per scene

- `adopt_voice.py`: a new `MAX_LINE_WORDS = 30`. `check_script` fails a line whose spoken text is longer than that,
  counted the way the intro is counted today (written words, `unrespell`, so "P R" is one word). In a discussion, the
  turns of a line are joined and counted together. The message names the frame and its count.
- `references/style.md` § For the voice: replace "A sentence has at most 30 words." with "A line (one scene) has at
  most 30 spoken words."
- In a discussion the cap is on the whole scene, all its turns joined (the user's decision). `references/style.md`
  § Discussion lines changes to fit: "2 to 6 turns per topic line, each turn 1 to 3 sentences" becomes "2 or 3 turns
  per topic line, alternating A and B, the turns together at most 30 words". A topic that needs more becomes two
  lines, so two scenes.
- `SKILL.md` § Script and `references/yolo.md` (the gate 2 row) name the 30-word line limit next to the 20-word intro
  limit.

### Review for template frames

In `references/handoff.md` § Review and render, before the stills of `finish.py --review` are shown: look at each still
against the BANNED line of `SPEC.md` and the "Tells for this type" in `explainer.md` (a slide of bullets, icons in
circles, three cards in a row, the whole diagram at once, the narrator's sentence on screen word for word). Fix every
one found, run `--review` again, then show the stills. At most two rounds. Name what was fixed when showing the stills.

### Files that change

| File | Change |
|---|---|
| `SKILL.md` | Stages list, `RUN.md` template (stage line, gate 3 approval line), new § Look (gate 3) between Script and Scenes, resume rule, the 30-word line rule. |
| `references/handoff.md` | The order with gate 3; `STORYBOARD.md` example and rules gain `shape`; § Scenes points at `build/index.template.html` and `SPEC.md`, not at the `blue-professional` look; the review pass above. |
| `references/style.md` | The 30-word line rule. |
| `references/yolo.md` | The gate 2 row (30 words), a gate 3 row. |
| `README.md` | One paragraph on the per-run look and its samples. |
| `assets/index.template.html` | Stays the skeleton every look copies. Its comment says the look in it is a placeholder and never shipped as is. |
| `assets/scene.template.html` | Cut to a bare skeleton: the `<template>`, `#root`, one `.stage`, the timeline and its registration. No eyebrow, no title, no `f.blur`/`f.exit` calls. |
| `config.example.json`, `README.md` config table, `SKILL.md` § Setup | Remove `style_preset`. The look is picked per run, so a fixed preset would skip gate 3. The user's own `config.json` keeps the key; nothing reads it. |
| `scripts/adopt_voice.py` | `MAX_LINE_WORDS`, the line check, `shape` parsing in `scene_cards` (`CARD_RE` gains `shape`), the shape checks in `check_script`. |
| `scripts/look_samples.py` | New. Builds and renders the samples (step 4). Uses `build_index.build` on each sample folder. |
| `scripts/test_adopt_voice.py`, `scripts/test_look_samples.py` | Tests for every new check and for the sample build (render replaced by a fake). |

## Left to the builder

- How `look_samples.py` gives `build_index.build` a one-frame project (copying files into `sample/`, or a small
  argument on `build`), as long as `build_index.py`'s current behavior and tests stay the same.
- The wording of the new `SKILL.md` and `handoff.md` sections, in the style of the files around them.
- How the last five runs' `SPEC.md` files are found and compared (the agent reads them; no script is required).

## My calls (not yet confirmed by the user)

- Three looks, matching HyperFrames' three storylines.
- The samples wait for the adopted voice. Voicing and writing the three looks run at the same time, so the wait is
  mostly the three short renders.
- Yolo skips the sample renders.
- Bundled font families only, so no `.woff2` files are added to a run. Any weight is allowed: the HyperFrames
  compiler fetches missing weights from Google Fonts and caches them in `~/.cache/hyperframes/fonts`. Ceiling: 19
  families; add downloaded `.woff2` files when looks start to repeat.
- With the user's own engine and no `tts_command`, the samples wait until the user has dropped every line's audio.
- `style_preset` is removed (see Files that change).
- Uniqueness is checked against the last five runs.
- Shapes are checked only for frames in a row; a shape may come back later in the video.
