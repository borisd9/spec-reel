# A New Look Every Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** spec-reel writes three looks per run, renders an intro sample in each, lets the user pick one at a new gate 3, gives every scene a shape, and caps each scene at 30 spoken words.

**Architecture:** A look is a run-local `index.template.html` (the existing `build/index.template.html` hook in `build_index.py`) plus a `LOOK.md` of numbers. A new `scripts/look_samples.py` builds a one-frame project per look with `build_index.build` and renders it. The new rules (30-word line, `shape`) are code checks in `adopt_voice.py --check-script`; the gate, the look writing and the template review are agent instructions in `SKILL.md`, `references/handoff.md`, `references/style.md` and `references/yolo.md`.

**Tech Stack:** Python 3 standard library only (`unittest`), HyperFrames CLI 0.8.150 through `npx hyperframes`, Markdown skill docs.

**Spec:** `docs/superpowers/specs/2026-10-26-per-run-look-design.md` (read it first; this plan argues from it).

**Repo and branch:** a git worktree of this repo outside every skills folder (the spawn prompt names it), branch `per-run-look` (already created, holds the spec and this plan). All paths below are relative to that worktree. Never edit or switch the branch of `~/.agents/skills/spec-reel`: it is the installed skill every spec-reel run uses, and it stays on `main` until this branch merges.

**Test command (whole suite):** `cd scripts && python3 -I -m unittest discover -s . -p 'test_*.py'`. Baseline: 156 tests, all pass. There is no linter.

## Global Constraints

- Standard-library Python only in `scripts/`. Every external command goes through a function that tests replace (`finish.run_command` is the one to reuse).
- No CSS filters (`finish.BLUR`) and no `onUpdate:` (`finish.CALLBACK`) in any look file.
- `window.fx.at`, `window.fx.fact`, `window.fx.type`, `__WORDS`, `__VO`, `__DUR`, `__FACTS` and every `%PLACEHOLDER%` in `assets/index.template.html` keep their names and behavior.
- Fonts: only the families HyperFrames bundles (Inter, Montserrat, Outfit, Nunito, Oswald, League Gothic, Archivo Black, Space Mono, IBM Plex Mono, JetBrains Mono, EB Garamond, Playfair Display, Source Code Pro, Noto Sans JP, Roboto, Open Sans, Lato, Poppins) plus Space Grotesk from `assets/fonts/`. Any weight. Inter, Space Grotesk and JetBrains Mono never as the display face.
- Shapes, exactly these ten values: `number`, `myth`, `before-after`, `converge`, `network`, `chosen`, `steps`, `screenshot`, `quote`, `chapter`.
- `MAX_LINE_WORDS = 30`, counted like the intro today: `len(unrespell(text).split())`. In a discussion the turns of a line are joined and counted together.
- Docs are plain English, short sentences, in the style of the file around them. `scripts/test_skill_structure.py` must keep passing: no `faceless-explainer`, no `Skill tool`, no `run_in_background`, HyperFrames paths only as `<hyperframes dir>/...`, every `references/`, `scripts/`, `assets/` path a doc names must exist, config keys equal the README `## Configure` table.
- Commit after each task with a plain one-line message (the repo's style, e.g. "Cap each scene at 30 spoken words"). No Co-Authored-By trailer is required. Do not push.

## Review Focus

1. A discussion line whose turns are each short but together exceed 30 words must fail, naming the frame and the joined count. (Task 1 test `test_discussion_line_counts_all_turns`.)
2. Respelled words count as written: a line with "P R 12" at exactly 30 written words passes. (Task 1 test `test_line_counts_written_words`.)
3. The adjacent-shape rule skips the intro and Demo frames: a Demo frame between two `steps` frames does not make them pass. (Task 2 test `test_demo_frame_between_same_shapes_still_fails`.)
4. A look whose `index.template.html` adds an `fx` move with `filter: "blur(4px)"` or an `onUpdate:` must fail in `look_samples.py` before any render runs. (Task 4 test `test_blur_in_look_template_fails_before_render`.)
5. `look_samples.py` must never touch the run's own `index.html`, `compositions/` or `build/`. (Task 4 test `test_run_files_untouched`.)

---

### Task 1: 30 spoken words per scene

**Files:**
- Modify: `scripts/adopt_voice.py` (constants near line 42, `check_script` at line 497)
- Modify: `references/style.md` (§ For the voice line 35, § Discussion lines lines 41-47)
- Modify: `SKILL.md` § Script (the intro bullet, line 127, and the discussion bullet, line 134)
- Modify: `references/yolo.md` (the Gate 2 row)
- Modify: `references/handoff.md` § Script check (line 82: the list of what `--check-script` fails on)
- Test: `scripts/test_adopt_voice.py`, class `CheckScriptTests`

**Interfaces:**
- Produces: `adopt_voice.MAX_LINE_WORDS = 30`; `check_script` problem text `f"frame {frame}: {n} spoken words; a scene has at most {MAX_LINE_WORDS}"`.

- [ ] **Step 1: Write the failing tests** in `CheckScriptTests`:

```python
def test_line_longer_than_30_words(self):
    long = " ".join(["word"] * 31) + "."
    script = INTRO_SCRIPT.replace("Shipped the thing.", long)
    code, err = self.check(script)
    self.assertEqual(code, 1)
    self.assertIn("frame 2: 31 spoken words; a scene has at most 30", err)

def test_line_of_exactly_30_words_passes(self):
    script = INTRO_SCRIPT.replace("Shipped the thing.", " ".join(["word"] * 30) + ".")
    self.assertEqual(self.check(script)[0], 0)

def test_line_counts_written_words(self):
    # "P R" is the spoken form of "PR": unrespell counts it as one written word
    text = "We merged P R 12 " + " ".join(["word"] * 26) + "."  # 30 written words
    self.assertEqual(self.check(INTRO_SCRIPT.replace("Shipped the thing.", text))[0], 0)

def test_discussion_line_counts_all_turns(self):
    turns = "".join(f"### Turn — {s}\n    " + " ".join(["word"] * 8) + ".\n" for s in "ABAB")  # 32 words
    body = DISCUSSION.split("## Line 2")[0] + "## Line 2 — Retries (Frame 2)\n" + turns + "## Line 3 — End (Frame 3)\n    Next up is more.\n"
    code, err = self.discussion(body)
    self.assertEqual(code, 1)
    self.assertIn("frame 2: 32 spoken words; a scene has at most 30", err)
```

- [ ] **Step 2: Run them and see them fail**

Run: `cd scripts && python3 -I -m unittest test_adopt_voice.CheckScriptTests -v`
Expected: the two failing-length tests FAIL (no such message); the two passing ones pass already.

- [ ] **Step 3: Implement.** Add `MAX_LINE_WORDS = 30` next to `MAX_INTRO_WORDS`. In `check_script`, after the intro check, for every `(frame, text)` in `approved` (`parse_script` already joins a discussion line's turns into one text), count `len(unrespell(text).split())` and append the problem above when it is over `MAX_LINE_WORDS`. The intro keeps its own 20-word check.

- [ ] **Step 4: Run the whole suite**

Run: `cd scripts && python3 -I -m unittest discover -s . -p 'test_*.py'`
Expected: OK, 160 tests.

- [ ] **Step 5: Docs.**
  - `references/style.md` § For the voice: replace "A sentence has at most 30 words. Long sentences hurt Qwen3-TTS pacing and are hard to follow by ear." with "A line (one scene) has at most 30 spoken words. Long lines hurt Qwen3-TTS pacing and are hard to follow by ear."
  - `references/style.md` § Discussion lines: replace "2 to 6 turns per topic line, alternating A and B, each turn 1 to 3 sentences." with "2 or 3 turns per topic line, alternating A and B, the turns together at most 30 words. A topic that needs more becomes two lines, so two scenes."
  - `SKILL.md` § Script: after the intro bullet's "(at most 20 words)", add a bullet "every other line has at most 30 spoken words; in a discussion its turns count together".
  - `references/yolo.md` Gate 2 row: change "intro of at most 20 words" to "intro of at most 20 words, every other line at most 30 (a discussion line's turns together)".
  - `references/handoff.md` § Script check: add "when any line has more than 30 written words (a discussion line's turns counted together)" to the list of failures, next to the 20-word intro rule.

- [ ] **Step 6: Run the whole suite again** (the structure tests read the docs). Expected: OK.

- [ ] **Step 7: Commit**

```bash
git add scripts/adopt_voice.py scripts/test_adopt_voice.py references/style.md references/yolo.md references/handoff.md SKILL.md
git commit -m "Cap each scene at 30 spoken words"
```

---

### Task 2: A shape per scene

**Files:**
- Modify: `scripts/adopt_voice.py` (`CARD_RE` line 56, new `SHAPES` constant next to `SCENE_JOBS` line 52, `scene_cards` line 160, `check_script`)
- Modify: `references/handoff.md` § STORYBOARD.md (the scene card bullet and its example, lines 62-69) and § Script check (line 82, line 87)
- Modify: `SKILL.md` § Scenes step 2 (line 150)
- Test: `scripts/test_adopt_voice.py` (`INTRO_STORYBOARD` fixture and `CheckScriptTests`)

**Interfaces:**
- Produces: `adopt_voice.SHAPES = ("number", "myth", "before-after", "converge", "network", "chosen", "steps", "screenshot", "quote", "chapter")`; `scene_cards()` now also returns `"shape"` per frame; problem texts `f"frame {frame}: STORYBOARD.md has no shape"` and `f"frame {frame}: same shape as frame {prev} ({shape})"`.

- [ ] **Step 1: Update the fixture.** In `INTRO_STORYBOARD`, add `- shape: before-after` under Frame 2's `scene_job` and `- shape: steps` under Frame 3's. Every existing test keeps passing with it.

- [ ] **Step 2: Write the failing tests** in `CheckScriptTests`:

```python
def test_frame_without_shape_is_named(self):
    code, err = self.check(INTRO_SCRIPT, INTRO_STORYBOARD.replace("- shape: steps\n", ""))
    self.assertEqual(code, 1)
    self.assertIn("frame 3: STORYBOARD.md has no shape", err)

def test_unknown_shape_counts_as_missing(self):
    code, err = self.check(INTRO_SCRIPT, INTRO_STORYBOARD.replace("shape: steps", "shape: bullets"))
    self.assertEqual(code, 1)
    self.assertIn("frame 3: STORYBOARD.md has no shape", err)

def test_two_frames_in_a_row_with_one_shape(self):
    code, err = self.check(INTRO_SCRIPT, INTRO_STORYBOARD.replace("shape: steps", "shape: before-after"))
    self.assertEqual(code, 1)
    self.assertIn("frame 3: same shape as frame 2 (before-after)", err)

def test_demo_frame_between_same_shapes_still_fails(self):
    script = INTRO_SCRIPT + "## Line 4 — Last (Frame 4)\n    The end.\n"
    script = script.replace("End (Frame 3)", "Demo (Frame 3)")
    storyboard = (INTRO_STORYBOARD.replace("## Frame 3 — End\n- scene_job: next\n- shape: steps\n",
                                           "## Frame 3 — Demo\n- asset_candidates: public/demo-01.mp4 — [video] x\n")
                  + "## Frame 4 — Last\n- scene_job: next\n- shape: before-after\n")
    code, err = self.with_demo(script, storyboard)
    self.assertEqual(code, 1)
    self.assertIn("frame 4: same shape as frame 2 (before-after)", err)
```

- [ ] **Step 3: Run them and see them fail**

Run: `cd scripts && python3 -I -m unittest test_adopt_voice.CheckScriptTests -v`
Expected: the four new tests FAIL.

- [ ] **Step 4: Implement.** `CARD_RE` matches `scene_job|before|after|shape`. In `check_script`'s scene-card loop (which already skips frame 1 and demo frames), a frame whose `shape` is not in `SHAPES` gets the "no shape" problem; keep the previous checked frame's shape and add the "same shape" problem when it repeats. Compare only frames that passed the skip, in frame order.

- [ ] **Step 5: Run the whole suite.** Expected: OK, 164 tests.

- [ ] **Step 6: Docs.**
  - `references/handoff.md` § STORYBOARD.md: the scene-card bullet also says "and `- shape:`, the shape of the line's information, one of `number`, `myth`, `before-after`, `converge`, `network`, `chosen`, `steps`, `screenshot`, `quote`, `chapter` (`<hyperframes dir>/references/types/explainer.md` § Shapes of information). Two frames in a row never share a shape; the intro and Demo frames have none." Add `- shape: before-after` to the `## Frame 3 — Retries` example.
  - `references/handoff.md` § Script check: add the two shape failures to the failure list, and a fix bullet "a missing or repeated `shape` is fixed by picking the shape that fits the line and differs from the frame before it".
  - `SKILL.md` § Scenes step 2: "every other frame a `scene_job`" becomes "every other frame a `scene_job` and a `shape`".

- [ ] **Step 7: Run the whole suite again.** Expected: OK.

- [ ] **Step 8: Commit**

```bash
git add scripts/adopt_voice.py scripts/test_adopt_voice.py references/handoff.md SKILL.md
git commit -m "Give every scene a shape; no two in a row share one"
```

---

### Task 3: Shared fast-capture lint

**Files:**
- Modify: `scripts/finish.py` (`Finish.lint_fast_capture`, lines 116-125)
- Test: `scripts/test_finish.py`

**Interfaces:**
- Produces: module-level `finish.fast_capture_problems(files: list[Path], root: Path) -> list[str]`, returning the same two messages `Finish.lint_fast_capture` builds today (one for `BLUR` hits, one for `CALLBACK` hits, each listing `"<path relative to root>:<line>"`), empty when clean. Missing files are skipped.

- [ ] **Step 1: Write the failing test** in `scripts/test_finish.py`:

```python
def test_fast_capture_problems_names_file_and_line(self):
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "a.html").write_text("ok\nfilter: blur(4px)\n")
        (root / "b.html").write_text("tl.to(x, { onUpdate: () => {} })\n")
        problems = finish.fast_capture_problems([root / "a.html", root / "b.html", root / "gone.html"], root)
        self.assertEqual(len(problems), 2)
        self.assertIn("a.html:2", problems[0])
        self.assertIn("b.html:1", problems[1])
        self.assertEqual(finish.fast_capture_problems([root / "gone.html"], root), [])
```

(Use the module alias and imports `test_finish.py` already has; add `tempfile`/`Path` imports only if missing.)

- [ ] **Step 2: Run it and see it fail.** Run: `cd scripts && python3 -I -m unittest test_finish -v`. Expected: FAIL, no attribute `fast_capture_problems`.

- [ ] **Step 3: Implement** `fast_capture_problems` by moving the body of `lint_fast_capture` into it; `lint_fast_capture` becomes `return "; ".join(fast_capture_problems([...same files...], self.p)) or None`.

- [ ] **Step 4: Run the whole suite.** Expected: OK, 165 tests, the existing finish lint tests unchanged.

- [ ] **Step 5: Commit**

```bash
git add scripts/finish.py scripts/test_finish.py
git commit -m "Move the fast-capture lint into a function look samples can share"
```

---

### Task 4: `look_samples.py`

**Files:**
- Create: `scripts/look_samples.py`
- Test: `scripts/test_look_samples.py`

**Interfaces:**
- Consumes: `build_index.build(p: Path) -> (total_s, scene_count)` (raises `ValueError`); `finish.run_command(cmd: list[str], cwd: Path) -> int`; `finish.fast_capture_problems` (Task 3).
- Produces: CLI `python3 -I scripts/look_samples.py <project_dir> [--look <folder name>]`; `main(argv: list[str], runner=run_command) -> int`; `look_dirs(p: Path) -> list[Path]` (the folders under `looks/` whose name matches `^\d+-[\w-]+$`, sorted); `build_sample(p: Path, look: Path) -> Path` (returns the sample folder).

Behavior, all pinned by the spec:
- `--look 2-paper-cut` limits the run to `looks/2-paper-cut`; without it, every folder from `look_dirs`.
- Before anything is written: fail (exit 1, every problem on stderr, nothing rendered) when `audio_meta.json` is missing, it has no voice for frame 1, a look folder lacks `index.template.html` or `compositions/intro.html`, or `fast_capture_problems([look/"index.template.html", look/"compositions/intro.html"], p)` is not empty.
- `build_sample` recreates `look/"sample"` (delete it first if present) holding: `STORYBOARD.md` with exactly `"## Frame 1 — Intro\n- src: compositions/intro.html\n"`; `audio_meta.json` = `{"voices": [<the run's frame-1 voice entry, unchanged>]}`; the WAV that entry's `path` names, copied to the same relative path; `compositions/intro.html` from the look; `build/index.template.html` from the look's `index.template.html`; `facts.json` from the run when it exists; the project files `npx hyperframes init` writes at the run root (`hyperframes.json`, `meta.json`, `package.json`), each when it exists; then `build_index.build(sample)`.
- Render each sample in look order with `runner(["npx", "hyperframes", "render", ".", "-o", str(look / "intro.mp4")], sample)`; a non-zero exit is a problem naming the look. Print `"<look name>: <look>/intro.mp4"` for each success.
- Writes nothing outside `looks/`.

- [ ] **Step 1: Write the failing tests** in `scripts/test_look_samples.py`. Fixture: a temp run folder with `audio_meta.json` holding voices for frames 1 and 2 (use the `voice()` helper shape from `test_build_index.py`, with words `["Meet", "the", "tool."]` for frame 1), `assets/voice/01.wav` (any bytes), `index.html`, `compositions/intro.html` and `build/` marker files at the run root, and two looks `looks/1-paper/` and `looks/2-blueprint/`, each with `index.template.html` (a copy of the repo's `assets/index.template.html`) and `compositions/intro.html` (`<template><script>f.rise(tl, "#a", at("tool"));</script></template>`), and `hyperframes.json` and `meta.json` at the run root (`{}` each; no `package.json`). The fake runner appends `(cmd, cwd)` to `self.calls` and returns `self.result` (default 0). `self.main(*args)` returns the exit code; `self.main_err(*args)` returns `(code, stderr text)`.

```python
def test_builds_one_frame_sample_per_look_and_renders_each(self):
    self.assertEqual(self.main(), 0)
    self.assertEqual([c[1].parent.name for c in self.calls], ["1-paper", "2-blueprint"])
    for name in ("1-paper", "2-blueprint"):
        sample = self.p / "looks" / name / "sample"
        meta = json.loads((sample / "audio_meta.json").read_text())
        self.assertEqual([v["frame"] for v in meta["voices"]], [1])
        self.assertTrue((sample / "assets/voice/01.wav").exists())
        self.assertIn('data-composition-id="intro"', (sample / "index.html").read_text())
        self.assertIn(str(self.p / "looks" / name / "intro.mp4"), self.calls[["1-paper", "2-blueprint"].index(name)][0])

def test_one_look_only(self):
    self.assertEqual(self.main("--look", "2-blueprint"), 0)
    self.assertEqual([c[1].parent.name for c in self.calls], ["2-blueprint"])
    self.assertFalse((self.p / "looks/1-paper/sample").exists())

def test_no_audio_meta_fails_before_render(self):
    (self.p / "audio_meta.json").unlink()
    code, err = self.main_err()
    self.assertEqual(code, 1)
    self.assertIn("audio_meta.json", err)
    self.assertEqual(self.calls, [])

def test_look_missing_intro_is_named(self):
    (self.p / "looks/2-blueprint/compositions/intro.html").unlink()
    code, err = self.main_err()
    self.assertEqual(code, 1)
    self.assertIn("2-blueprint", err)
    self.assertEqual(self.calls, [])

def test_blur_in_look_template_fails_before_render(self):
    t = self.p / "looks/1-paper/index.template.html"
    t.write_text(t.read_text().replace("window.fx = {", 'window.fx = {\n  smear(tl, s, t) { tl.fromTo(s, {filter: "blur(4px)"}, {filter: "blur(0px)"}, t); },'))
    code, err = self.main_err()
    self.assertEqual(code, 1)
    self.assertIn("looks/1-paper/index.template.html", err)
    self.assertEqual(self.calls, [])

def test_cue_on_a_word_the_intro_lacks_fails(self):
    (self.p / "looks/1-paper/compositions/intro.html").write_text('<template><script>at("missing");</script></template>')
    code, err = self.main_err()
    self.assertEqual(code, 1)
    self.assertIn('at("missing"', err)

def test_failed_render_is_named(self):
    self.result = 1
    code, err = self.main_err()
    self.assertEqual(code, 1)
    self.assertIn("1-paper", err)

def test_run_files_untouched(self):
    before = {f: f.read_bytes() for f in (self.p / "index.html", self.p / "compositions/intro.html", self.p / "build/marker")}
    self.main()
    for f, data in before.items():
        self.assertEqual(f.read_bytes(), data)

def test_project_files_are_copied_when_present(self):
    self.main()
    sample = self.p / "looks/1-paper/sample"
    self.assertTrue((sample / "hyperframes.json").exists())
    self.assertTrue((sample / "meta.json").exists())
    self.assertFalse((sample / "package.json").exists())

def test_rerun_replaces_the_sample(self):
    self.main()
    (self.p / "looks/1-paper/sample/stale.txt").write_text("x")
    self.main()
    self.assertFalse((self.p / "looks/1-paper/sample/stale.txt").exists())
```

- [ ] **Step 2: Run them and see them fail.** Run: `cd scripts && python3 -I -m unittest test_look_samples -v`. Expected: ERROR, no module `look_samples`.

- [ ] **Step 3: Implement `scripts/look_samples.py`** with the interfaces above. Module docstring in the style of `build_index.py` (usage lines, what it reads, what it writes, "Standard library only."). Import `build_index` and `finish` the way `finish.py` imports its siblings (`sys.path.insert(0, str(HERE))`).

- [ ] **Step 4: Run the whole suite.** Expected: OK, 175 tests.

- [ ] **Step 5: Commit**

```bash
git add scripts/look_samples.py scripts/test_look_samples.py
git commit -m "Add look_samples.py: one intro render per proposed look"
```

---

### Task 5: Gate 3 in the docs, the bare scene template, no `style_preset`

**Files:**
- Modify: `SKILL.md` (stages line 11, Setup step 2 line 24, `RUN.md` template lines 60-92, Resume line 40, new `## Look (gate 3)` section between `## Script (gate 2)` and `## Scenes`, Scenes step 3 line 151, stop conditions)
- Modify: `references/handoff.md` (§ The order, § Scenes step 1 line 103, § Review and render)
- Modify: `references/yolo.md` (new Gate 3 row after the Gate 2 row; the final report's **Decided without you** list)
- Modify: `README.md` (one paragraph on the per-run look; remove the `style_preset` row from `## Configure`)
- Modify: `config.example.json` (remove `style_preset`)
- Modify: `assets/scene.template.html` (bare skeleton)
- Modify: `assets/index.template.html` (the comment at line 66)
- Test: `scripts/test_skill_structure.py`

**Interfaces:**
- Consumes: `scripts/look_samples.py` CLI (Task 4); `MAX_LINE_WORDS` and `shape` rules (Tasks 1-2).

- [ ] **Step 1: Write the failing structure tests** in `SkillStructureTests`:

```python
def test_look_gate_is_documented(self):
    skill = (ROOT / "SKILL.md").read_text()
    self.assertIn("sources | digest | script | look | scenes | done", skill)
    self.assertIn("gate 3 (look)", skill)
    self.assertIn("scripts/look_samples.py", skill + (ROOT / "references/handoff.md").read_text())
    self.assertIn("gate 3", (ROOT / "references/yolo.md").read_text().lower())

def test_no_fixed_style_preset(self):
    self.assertNotIn("style_preset", json.loads((ROOT / "config.example.json").read_text()))
    for doc in DOCS:
        self.assertNotIn("style_preset", doc.read_text(), doc.name)

def test_scene_template_is_a_bare_skeleton(self):
    t = (ROOT / "assets/scene.template.html").read_text()
    for gone in ("eyebrow", "f.blur(", "f.exit("):
        self.assertNotIn(gone, t)
    for kept in ("<template>", 'data-composition-id="SCENE_ID"', "window.__timelines[S] = tl"):
        self.assertIn(kept, t)
```

Also add `"scripts/look_samples.py"` to the tuple in `test_every_script_and_asset_is_documented_and_present`.

- [ ] **Step 2: Run them and see them fail.** Run: `cd scripts && python3 -I -m unittest test_skill_structure -v`. Expected: the new tests FAIL.

- [ ] **Step 3: `config.example.json`, `README.md`.** Remove the `style_preset` key and its table row. Add to the README, after the paragraph on how scenes are built, one paragraph: after you approve the script, the skill writes three looks made for the subject, renders the intro in each, opens the three clips, and you pick one; it styles every scene.

- [ ] **Step 4: `assets/scene.template.html`.** Keep the `<template>`, the `<style>` with `#root`, `<div id="root" data-composition-id="SCENE_ID" ...>` holding one `<div id="SCENE_ID-stage" class="stage"></div>`, and the script that builds `tl`, defines `S`, `f`, `D`, `at`, and registers `window.__timelines[S] = tl`. Remove the eyebrow, the title and the `f.blur`/`f.exit` calls. The comment says: build the scene from its `shape` in the run's look (`SPEC.md` and the classes and moves in `build/index.template.html`), cue on words with `at()`, read facts with `f.fact()`, no CSS filters, no `onUpdate`.

- [ ] **Step 5: `assets/index.template.html`.** Line 66's comment becomes: "Placeholder look (blue-professional). Every run restyles a copy of this file as its own look (`looks/<n>-<slug>/index.template.html`, then `build/index.template.html`); this look is never shipped as is." Nothing else changes.

- [ ] **Step 6: `SKILL.md`.**
  - Line 11 stages: "sources, digest, title and demo (gate 1), script (gate 2), look (gate 3), frame plan, scenes, review stills, render".
  - Setup step 2: the required values are `output_root` and `voice_source`.
  - `RUN.md` template: stage line `sources | digest | script | look | scenes | done`; under `## Approvals` add `- gate 3 (look): <time>  <look name>  sha256 <hash of looks/<pick>/LOOK.md>`.
  - Resume: "a changed `looks/<pick>/LOOK.md` re-opens gate 3 and then rebuilds every scene; a changed `user_script.txt` re-opens gate 2 and keeps the picked look (the intro scene is rebuilt in it when line 1 changed; no new samples)."
  - New `## Look (gate 3)` section, `Set stage: look.`, then the spec's "Gate 3: the look" steps 1-6 and 8 (`docs/superpowers/specs/2026-10-26-per-run-look-design.md`), written as instructions: the three `looks/<n>-<slug>/` folders and what each holds (`LOOK.md` with `LOOK:`, `MOTION:`, `BANNED:` lines in numbers per `<hyperframes dir>/references/spec.md`; `index.template.html` restyled from `assets/index.template.html`; `compositions/intro.html`); the difference rules (medium, display face, ground color family; not a preset in `<hyperframes dir>/assets/frame-presets/`; differs in medium and display face from the `SPEC.md` of the last five runs under `output_root`); the fonts rule from Global Constraints; the sample command `python3 -I <this skill's directory>/scripts/look_samples.py .` once `audio_meta.json` exists (`--look <folder>` to redo one); `open` the three `intro.mp4` files and list name, why it fits, path, recommendation first; the pick (copy to `build/index.template.html` and `compositions/intro.html`, write `SPEC.md`, record gate 3). Yolo: `references/yolo.md`.
  - Scenes step 3: build each scene from `assets/scene.template.html` in the picked look, from its `shape` (`build/index.template.html` and `SPEC.md`); replace "the explainer route: one concrete example, a diagram that grows, the voice as the clock" wording only if needed to keep it true.
  - Stop conditions: add "`look_samples.py` still fails after three fixes to the look's own files".
  - SKILL.md § Scenes "When a `finish.py` step fails" list: also covers `look_samples.py` failures in a look's own files (a filter, an `onUpdate`, a cue on a word the intro lacks).

- [ ] **Step 7: `references/handoff.md`.**
  - § The order: step 2 becomes "Meanwhile write the three looks (gate 3, `SKILL.md` § Look); when `audio_meta.json` exists run `look_samples.py` and show the samples. After the pick, write `STORYBOARD.md`, get the frame plan reviewed (interactive mode), and write the scenes."
  - § Scenes step 1: replace the sentences about the `blue-professional` preset and restyling with: the run's look is `build/index.template.html` (copied from the picked look) and `SPEC.md`; scenes use its classes and its `MOTION` moves; the old fade moves (`blur`, `rise`, `slide`, `pop`, `fade`, `exit`) stay only so older scenes still work.
  - § Review and render, before "The stills are in `review/snapshots/`: show them to the user": the template review from the spec (check each still against `SPEC.md`'s BANNED line and the "Tells for this type" in `<hyperframes dir>/references/types/explainer.md`: a slide of bullets, icons in circles, three cards in a row, the whole diagram at once, the narrator's sentence on screen word for word, every element fading and rising; fix, run `--review` again, at most two rounds; name what was fixed when showing the stills; a default found goes on `SPEC.md`'s BANNED line).
  - § Change requests: "another look" re-opens gate 3 (three new looks, or changes to one with `look_samples.py --look <folder>`), then every scene is rebuilt.

- [ ] **Step 8: `references/yolo.md`.** New row after Gate 2: `| Gate 3: the look | Show three rendered samples, wait for a pick | Write the three looks, skip look_samples.py, take the recommended one, record gate 3 (look): auto (yolo) <time> <look name> sha256 <hash>. |` In the final report's **Decided without you** list add "the look taken and the other two, one line each".

- [ ] **Step 9: Run the whole suite.** Expected: OK, 178 tests.

- [ ] **Step 10: Commit**

```bash
git add SKILL.md README.md config.example.json references/handoff.md references/yolo.md assets/scene.template.html assets/index.template.html scripts/test_skill_structure.py
git commit -m "Pick a new look every run at gate 3; bare scene template; drop style_preset"
```

---

### Task 6: End-to-end check of a real sample render

No code. Proves `look_samples.py` renders with the real CLI.

- [ ] **Step 1:** In a temp folder outside the repo, `npx hyperframes init <tmp>/run --non-interactive --example=blank --skill=spec-reel`. Put a one-line `audio_meta.json` with a frame-1 voice whose `path` is `assets/voice/01.wav`, make that WAV with `ffmpeg -f lavfi -i "sine=frequency=440:duration=3" -ar 44100 -ac 1 <tmp>/run/assets/voice/01.wav`, and set its `words` to three words spread over 3 s. Make `looks/1-test/` with a copy of `assets/index.template.html` and a `compositions/intro.html` from the new `assets/scene.template.html` with `SCENE_ID` replaced by `intro` and one `.title` element cued with `at()` on one of the three words.
- [ ] **Step 2:** Run `python3 -I <repo>/scripts/look_samples.py <tmp>/run`. Expected: exit 0, `<tmp>/run/looks/1-test/intro.mp4` exists, `ffprobe` reports about 3 s and an audio stream.
- [ ] **Step 3:** If the render fails, stop and report the full error. Do not change the design to work around it.
- [ ] **Step 4:** Report the command output and the `ffprobe` line. Delete the temp folder.
