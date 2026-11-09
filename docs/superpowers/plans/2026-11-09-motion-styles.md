# Motion Styles Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gate 3 builds its three looks from a catalog of tested motion styles, written as numbers, instead of making each look up from nothing.

**Architecture:** A new reference, `references/motion-styles.md`, holds 16 motion styles adapted from awesomeclaude.ai. That is all 17 on the page except `social`, which is 9:16; the user decided to skip it. Each style has a palette, bundled fonts, a runtime, eases, timings, rules, an avoid list and a style prompt. Gate 3 (from the per-run-look plan) picks three styles from three different groups and turns each one into a look. DOM and SVG styles animate with GSAP `fromTo`. Canvas, WebGL and Three.js styles draw each frame from timeline time in HyperFrames' `hf-seek` listener (`<hyperframes dir>/references/runtimes.md`). Two small helpers, `fx.rand` and `fx.stepped`, plus GSAP `CustomEase`, let a look follow its style's numbers and stay seek-safe. A new lint fails on unseeded `Math.random(`.

**Tech Stack:** Python 3 standard library (`unittest`), GSAP 3.14.2 with `CustomEase` from the same CDN, HyperFrames CLI through `npx hyperframes`, Markdown skill docs.

**Spec:** this plan and `docs/superpowers/specs/2026-10-26-per-run-look-design.md`. The source material is <https://awesomeclaude.ai/claude-motion-graphics> (updated 2026-10-21). The 17 style objects, extracted verbatim, are in Appendix A.

**Depends on:** `docs/superpowers/plans/2026-10-26-per-run-look.md`, which is implemented on branch `per-run-look-impl`. This plan edits the `§ Look (gate 3)` section, `LOOK.md` and `scripts/look_samples.py` that the earlier plan creates.

**Branch:** `motion-styles`, created from `per-run-look-impl`. This plan file is the branch's first commit. Before starting, read the per-run-look code as built (`scripts/look_samples.py`, `SKILL.md` § Look) and use its real names. Where this plan guesses at that code, for example "wherever it checks `BLUR` and `CALLBACK`" or the `slow_capture` result field, follow the code's shape. Keep the behavior this plan names.

**Test command (whole suite):** `cd scripts && python3 -I -m unittest discover -s . -p 'test_*.py'`. There is no linter.

## Global Constraints

- Everything from the per-run-look plan's Global Constraints still holds: no CSS filters (`finish.BLUR`), no `onUpdate:` (`finish.CALLBACK`), bundled fonts only, and the `fx.at`, `fx.fact`, `fx.type` and `%PLACEHOLDER%` names do not change.
- Output stays at 1920x1080, 30 fps. All frame counts in the catalog are converted at 30 fps and written as `N f (S s)`.
- Fonts come only from the bundled families: Inter, Montserrat, Outfit, Nunito, Oswald, League Gothic, Archivo Black, Space Mono, IBM Plex Mono, JetBrains Mono, EB Garamond, Playfair Display, Source Code Pro, Noto Sans JP, Roboto, Open Sans, Lato, Poppins, Space Grotesk. Inter, Space Grotesk and JetBrains Mono are never the display face.
- **Runtimes.** A style's `runtime` is `gsap`, `hf-seek` or `gsap + hf-seek`.
  - `gsap`: every effect is a GSAP `fromTo` of DOM or SVG elements.
  - `hf-seek`: a `<canvas>` drawn from `e.detail.time` in an `hf-seek` listener, per `<hyperframes dir>/references/runtimes.md` and `<hyperframes dir>/references/types/3d.md`. `render(t)` is a pure function. Anything simulated is computed once at load into arrays. Heavy setup registers `window.__hf.buildReady["<style id>"]`.
  - Three.js is pinned to `https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js`.
  - The brush engine for `painterly` is plain Canvas 2D: no p5 and no new dependency.
  - Pixel text for `pixel` is Space Mono drawn with `fillText` on the 320x180 canvas, then scaled 6x with `imageSmoothingEnabled = false`. Add a `ponytail:` comment: text may look soft; the fix is a 5x7 bitmap font table.
- Cubic-bezier eases load as `CustomEase` from `https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/CustomEase.min.js`. Example: `CustomEase.create("snap", "M0,0 C0.7,0 0.2,1 1,1")`.
- Attribution: the top of `references/motion-styles.md` and the README credit section both say: "Styles adapted from Awesome Claude (https://awesomeclaude.ai/claude-motion-graphics, github.com/webfuse-com/awesome-claude, CC0-1.0; site footer says MIT)."
- Commit after each task with a plain one-line message. Do not push.

## Review Focus

1. **Recent styles leave fewer than three groups.** The last five runs used styles that, once excluded, leave only one or two groups. Expected: drop the oldest exclusions one at a time until three groups are available, and never fail the gate. Goes in Task 2 (doc rule) with a worked example in `references/motion-styles.md` § Picking three.
2. **A look template seeds its noise with `Math.random()`.** Expected: `finish.py --review` fails with the file and line, and `look_samples.py` fails before any render. Tests are in Task 3.
3. **`fx.rand` is used in a comment or a string.** `// do not use Math.random()` must not trip the lint. Expected: only a call outside a `//` comment fails. Test in Task 3.
4. **A catalog font is outside the bundled list, or Inter is used as the display face.** Expected: the structure test fails and names the style. Test in Task 1.
5. **`fx.stepped(0.05)` on a very short tween.** Expected: `steps(1)`, never `steps(0)`, which GSAP treats as a fault. Test in Task 3.
6. **An `hf-seek` look makes the renderer fall back to screenshot capture.** Expected: `look_samples.py` reports it from the sample's render log (`falling back to screenshot`), and gate 3 shows it next to that look as "slower render". Never a silent 2x slowdown. Test in Task 3.

---

### Task 1: The catalog, `references/motion-styles.md`

**Files:**
- Create: `references/motion-styles.md`
- Modify: `README.md` (add a `## Credits` section before `## License`, or at the end if there is no License section)
- Test: `scripts/test_skill_structure.py`

**Interfaces:**
- Produces: `references/motion-styles.md`, with one `## <id> — <name>` section per style. Each section has exactly these bullets, in this order: `- group:`, `- fits:`, `- palette:`, `- fonts:`, `- runtime:`, `- motion:`, `- rules:`, `- avoid:`, `- prompt:`. Task 2 reads the ids and groups.

**What goes in.** These 16 styles, with ids from Appendix A: `swiss`, `flat-vector`, `morph`, `line-draw`, `dataviz`, `isometric`, `dark-keynote`, `screencast`, `hud`, `print`, `papercut`, `painterly`, `tape`, `toy3d`, `pixel`, `cel`.

- **group:** the page's group, one of `graphic`, `explain`, `drawn`, `retro`, `dimensional`.
- **palette:** the page's hex values, each labeled with its role (`ground`, `ink`, `accent`, and `shade` for any extra).
- **runtime:**
  - `hf-seek` for `painterly`, `tape`, `toy3d`, `pixel` and `cel`.
  - `gsap + hf-seek` for `morph`: SVG morphs, plus canvas metaballs for the liquid moments.
  - `gsap` for every other style.
- **motion:** the page's numbers, converted at 30 fps, with every cubic-bezier as a `CustomEase` name and path. Rates that are not 30 fps are stated with the helper that produces them:
  - On twos at 24 fps: draw `floor(t * 12)`.
  - 12 fps steps: `fx.stepped(d)`, or `floor(t * 12)` in `hf-seek`.
- **rules:** and **avoid:** the page's text, unchanged.
- **prompt:** the page's prompt, unchanged, plus one sentence that names the fonts from `fonts:`. For `cel`, add: "No characters unless a source has one: the linework boils on diagrams, arrows and icons."
- **fits:** which spec-reel content the style suits, for example "numbers, metrics, before and after" for `dataviz`.
- **fonts:** these pairs:

| id | display | body |
|---|---|---|
| swiss | Roboto 900 | Roboto 500 |
| flat-vector | Poppins 700 | Nunito 600 |
| morph | League Gothic 400 | Lato 400 |
| line-draw | Playfair Display 600 | EB Garamond 400 |
| dataviz | Playfair Display 700 | Lato 400 (numbers in IBM Plex Mono 500) |
| isometric | Montserrat 700 | Open Sans 500 |
| dark-keynote | Outfit 600 | Inter 400 |
| screencast | Roboto 700 | Inter 400 |
| hud | Space Mono 700 | IBM Plex Mono 400 |
| print | Archivo Black 400 | Space Mono 400 |
| papercut | Oswald 700 | Nunito 600 |
| painterly | EB Garamond 500 | Lato 400 |
| tape | Archivo Black 400 | Space Mono 400 |
| toy3d | Nunito 800 | Nunito 600 |
| pixel | Space Mono 700 | Space Mono 400 |
| cel | Outfit 800 | Nunito 600 |

After the 16 sections, add two more:

- `## Not used, and why`, with one line: `social` is 9:16, while spec-reel renders 1920x1080 only (`qc_video.py`). The user chose to skip it on 2026-11-09.
- `## Default avoid list`, copied from the page's skill: particle bursts, lens flares, neon glow, RGB split, glitch, bouncy easing on everything, decorative gradients, and text that repeats what the picture shows.

- [ ] **Step 1: Write the failing test** `test_motion_styles_catalog` in `scripts/test_skill_structure.py`:

```python
FONTS = {"Inter", "Montserrat", "Outfit", "Nunito", "Oswald", "League Gothic", "Archivo Black", "Space Mono",
         "IBM Plex Mono", "JetBrains Mono", "EB Garamond", "Playfair Display", "Source Code Pro", "Noto Sans JP",
         "Roboto", "Open Sans", "Lato", "Poppins", "Space Grotesk"}
STYLE_KEYS = ["group", "fits", "palette", "fonts", "runtime", "motion", "rules", "avoid", "prompt"]
HF_SEEK = {"painterly", "tape", "toy3d", "pixel", "cel"}

def test_motion_styles_catalog(self):
    text = (ROOT / "references/motion-styles.md").read_text()
    sections = dict(re.findall(r"^## ([a-z-]+) — .+?\n(.*?)(?=^## |\Z)", text, re.S | re.M))
    self.assertEqual(set(sections), {"swiss", "flat-vector", "morph", "line-draw", "dataviz", "isometric",
                                     "dark-keynote", "screencast", "hud", "print", "papercut", *HF_SEEK})
    for sid, body in sections.items():
        self.assertEqual(re.findall(r"^- (\w+):", body, re.M), STYLE_KEYS, sid)
        fonts = re.search(r"^- fonts: (.+)$", body, re.M).group(1)
        display = re.match(r"display ([A-Za-z ]+?) \d", fonts).group(1)
        self.assertNotIn(display, {"Inter", "Space Grotesk", "JetBrains Mono"}, sid)
        for family in re.findall(r"([A-Z][A-Za-z ]+?) \d{3}", fonts):
            self.assertIn(family, FONTS, f"{sid}: {family}")
        self.assertRegex(re.search(r"^- palette: (.+)$", body, re.M).group(1), r"#[0-9a-f]{6}")
        runtime = re.search(r"^- runtime: (.+)$", body, re.M).group(1)
        self.assertIn(runtime, {"gsap", "hf-seek", "gsap + hf-seek"}, sid)
        if sid in HF_SEEK:
            self.assertEqual(runtime, "hf-seek", sid)
    self.assertIn("## Not used, and why", text)
    self.assertIn("## Default avoid list", text)
    self.assertIn("awesomeclaude.ai", text)
```

The `- fonts:` line format is `display <Family> <weight> · body <Family> <weight>`.

- [ ] **Step 2: Run** `cd scripts && python3 -I -m unittest test_skill_structure -v`. Expected: `test_motion_styles_catalog` fails with `FileNotFoundError`.
- [ ] **Step 3: Write** `references/motion-styles.md` and the README `## Credits` section, both with the attribution line from Global Constraints.
- [ ] **Step 4: Run the whole suite.** Expected: everything passes.
- [ ] **Step 5: Commit** with the message "Add a motion styles catalog adapted from awesomeclaude.ai".

### Task 2: Gate 3 builds its looks from the catalog

**Files:**
- Modify: `SKILL.md` § Look (gate 3)
- Modify: `references/handoff.md` § Scenes and § Review and render (the template-frame review pass)
- Modify: `references/yolo.md`, the gate 3 row
- Modify: `references/motion-styles.md`, adding a `## Picking three` section
- Test: `scripts/test_skill_structure.py`

**Interfaces:**
- Consumes: the catalog ids and groups from Task 1.
- Produces: a `LOOK.md` line `STYLE: <id>`, which `SPEC.md` copies at the pick, and which the last-five-runs rule reads.

**Decisions to write in. These replace step 3 of the spec's "Gate 3" list.**

1. **One style per look.** Each of the three looks starts from one catalog style. Its `LOOK:` and `MOTION:` lines take that style's numbers unchanged. The look may change only the accent's hue, to fit a source brand, and only when a source brings one.
2. **Three groups.** The three styles come from three different `group` values.
3. **Recent styles.** A style named in the `STYLE:` line of any of the last five runs' `SPEC.md` is not picked. When that leaves fewer than three groups, drop exclusions oldest first until three groups are available.
4. **Recommendation.** The recommended look is the style whose `fits` best matches the approved digest. Put it first, with a one-clause reason. In yolo it is the one picked.
5. **BANNED.** A look's `BANNED:` line is its style's `avoid`, plus `§ Default avoid list`, plus the spec's own BANNED defaults.
6. **The page's review checks.** Add these to the template-frame review pass in `handoff.md`:
   - Every text block stays on screen at least max(1 s, 0.3 s per word).
   - No still shows a fallback font.
   - The last frame holds the final scene with nothing animating.
7. **`## Picking three`.** This section in `motion-styles.md` holds rules 2 to 4, plus one worked example of the fallback in rule 3.
8. **Dependency check.** Add `references/runtimes.md` and `references/types/3d.md` to the `for f in ...; do` loop in `handoff.md` § Files this skill needs. That loop already lists `references/spec.md`. Add `references/runtimes.md` to `EXTERNAL` in `scripts/test_skill_structure.py`; `types/` paths are already skipped. `handoff.md` § Scenes says that an `hf-seek` look's scenes follow those two files.

- [ ] **Step 1: Write the failing test** `test_gate_3_uses_the_catalog`:

```python
def test_gate_3_uses_the_catalog(self):
    skill = (ROOT / "SKILL.md").read_text()
    self.assertIn("references/motion-styles.md", skill)
    self.assertIn("STYLE:", skill)
    self.assertIn("three different", (ROOT / "references/motion-styles.md").read_text())
    self.assertIn("references/motion-styles.md", (ROOT / "references/yolo.md").read_text())
    loop = re.search(r"^for f in (.+?); do$", (ROOT / "references/handoff.md").read_text(), re.M).group(1).split()
    self.assertIn("references/runtimes.md", loop)
    self.assertIn("references/types/3d.md", loop)
```

- [ ] **Step 2: Run it.** Expected: FAIL on the first `assertIn`.
- [ ] **Step 3: Edit the four docs** per the decisions above, in the style of the text around each edit.
- [ ] **Step 4: Run the whole suite.** Expected: PASS. `test_named_skill_files_exist` covers the new path.
- [ ] **Step 5: Commit** with the message "Build the three looks from the motion styles catalog".

### Task 3: Seek-safe helpers for catalog motion

**Files:**
- Modify: `assets/index.template.html`, the `window.fx` block and the `<head>` scripts
- Modify: `scripts/finish.py`, which gets `RANDOM` and `lint_fast_capture`
- Modify: `scripts/look_samples.py`, adding `render_command` and the fallback note. The `RANDOM` lint comes for free through `finish.fast_capture_problems`.
- Test: `scripts/test_finish.py`, `scripts/test_look_samples.py`, `scripts/test_build_index.py`

**Interfaces:**
- Produces:
  - `fx.rand(seed) -> () => number`: mulberry32, returns values in `[0, 1)`, and gives the same sequence for the same seed.
  - `fx.stepped(d, fps = 12) -> string`: returns `"steps(" + Math.max(1, Math.round(d * fps)) + ")"`, for the 12 fps styles `print` and `papercut`.
  - The `CustomEase` script tag goes right after the `gsap.min.js` tag, plus `gsap.registerPlugin(CustomEase)`.
  - `finish.RANDOM = re.compile(r"^(?!\s*//).*\bMath\.random\s*\(")`.

- [ ] **Step 1: Write the failing tests:**
  - `test_finish.py::test_lint_fails_unseeded_random`. Write `compositions/feed.html` as `"// no Math.random() here\nconst r = Math.random();"`. Assert that `--review` exits with 1, that the error has `"Math.random is not seek-safe"` and `"compositions/feed.html:2"`, and that it has no `"feed.html:1"`.
  - `test_look_samples.py::test_random_in_look_template_fails_before_render`. Copy the existing blur test in that file, but put `Math.random()` in the look's `index.template.html`. Assert that the fake runner got no render command.
  - `test_look_samples.py::test_screenshot_fallback_is_reported`. A fake `render` returns `(0, "... falling back to screenshot ...")`. Assert that stdout has `slower render` for that look, and that the exit code is 0.
  - `test_build_index.py::test_template_has_seek_safe_helpers`. Assert that the shipped template contains `CustomEase.min.js`, `rand(seed)`, `stepped(d, fps = 12)` and `Math.max(1, Math.round(d * fps))`, and has no `Math.random(`.
- [ ] **Step 2: Run them.** Expected: all three fail.
- [ ] **Step 3: Implement.**
  - Add `RANDOM` next to `CALLBACK` in `finish.py`. Its comment says that a seek re-runs nothing, so random values differ between capture passes.
  - Add a third clause to `lint_fast_capture`: `"Math.random is not seek-safe; use fx.rand(seed): " + locations`.
  - Add the two `fx` helpers and the `CustomEase` tag to the template.
  - Put the `RANDOM` check inside `finish.fast_capture_problems(files, root)`. `look_samples.py` already calls that function, so its check needs no change.
  - Fast-capture fallback detection:
    - `finish.run_command` returns only the exit code and does not capture output. Leave it unchanged.
    - Add `render_command(cmd, cwd) -> tuple[int, str]` to `look_samples.py`. It runs with the same `HF_DE_PARALLEL_ROUTER` env as `finish.run_command`, captures stdout and stderr together, prints them through, and returns `(returncode, output)`.
    - `look_samples.main` gets a parameter `render=render_command`, used for the render call. The existing `runner` parameter stays, so current tests keep working.
    - When the output contains `falling back to screenshot`, the success line for that look becomes `"<look>: <out>  (slower render: fast capture fell back to screenshots)"`.
    - In the test, assert on that printed line. There is no `slow_capture` field.
- [ ] **Step 4: Run the whole suite.** Expected: everything passes.
- [ ] **Step 5: Commit** with the message "Lint unseeded randomness and add seeded and stepped motion helpers".
- [ ] **Step 6: Manual check, one `hf-seek` sample.** In a scratch run folder, build a look from `toy3d` and run `look_samples.py .` on it. Expected:
  - `intro.mp4` renders.
  - Two renders give byte-identical frame 30 (`ffmpeg -ss 1 -i intro.mp4 -frames:v 1 a.png`, and the same for the second render, then compare with `cmp`).
  - The log line about fast capture is recorded in the commit message.

---

## Appendix A: Source styles, verbatim

Extracted on 2026-11-09 from `https://awesomeclaude.ai/_nuxt/DbsnR_9q.js`, the page's style data. The page FAQ says: "Can I use these style prompts commercially? Yes. We wrote them and you can paste them into any prompt or skill."

### swiss — Swiss grid & kinetic type [graphic] stack=Canvas 2D or SVG
palette: ['#f5f2ea', '#111111', '#e63323']
useFor: ['Brand identity', 'Event openers', 'Conference titles']
 -  One easing curve for snaps, cubic-bezier(.7,0,.2,1). Linear only for lines being drawn.
 -  Entrances are wipes or clip reveals, never fades. Deletions are hard cuts.
 -  Exactly one element carries the signal colour per shot. That element is the subject.
 -  Every position lands on a 12-column grid with 4% margins.
avoid: Overshoot, springs, drop shadows, more than one typeface, centred-everything layouts
PROMPT: Style: Swiss International motion design. Off-white #f5f2ea, black #111, one signal red #e63323 used on a single element per shot. One grotesk typeface in two weights. A visible 12-column grid with 4% margins; every element snaps to it. Snaps use cubic-bezier(.7,0,.2,1), lines draw at linear speed. Entrances are wipes and clip reveals, never fades; exits are hard cuts on the beat. No overshoot, no shadows, no gradients.

### flat-vector — Flat vector explainer [explain] stack=SVG + GSAP
palette: ['#fdf6ec', '#2b2d42', '#ff6b35', '#4ecdc4', '#ffd23f']
useFor: ['SaaS promos', 'Onboarding', 'Science explainers']
 -  Entrances overshoot with cubic-bezier(0.34,1.56,0.64,1) and settle within 12 frames.
 -  Stagger groups by 2 to 4 frames, never all at once.
 -  Transitions are carried by an element: a shape grows to fill the frame and becomes the next background.
 -  Four to five flat colours, no gradients, no outlines thinner than 3px at 1080p.
avoid: Stock-illustration people with tiny heads, gradients, crossfades between scenes
PROMPT: Style: flat vector explainer. Palette #fdf6ec background, #2b2d42 ink, accents #ff6b35, #4ecdc4, #ffd23f. Geometric shapes and simple characters built from circles and rounded rectangles, no gradients. Entrances overshoot with cubic-bezier(0.34,1.56,0.64,1) and settle within 12 frames, groups stagger by 3 frames. Scene changes are carried by a shape that grows to fill the frame and becomes the next background. No crossfades.

### morph — Shape morph & liquid [graphic] stack=SVG path morphing, or WebGL metaballs for liquid
palette: ['#0d1b2a', '#f72585', '#7209b7', '#4cc9f0']
useFor: ['Music videos', 'Brand stories', 'Transitions between topics']
 -  There are no cuts. Every new idea grows out of the previous shape.
 -  Each morph takes 18 to 30 frames and passes through a readable in-between shape.
 -  Hold each finished shape at least 1 second so it reads.
 -  Liquid joins use smooth-min blending, never a hard overlap.
avoid: Morphs that pass through a shapeless blob, constant motion with no holds
PROMPT: Style: continuous shape morph. Dark #0d1b2a field, shapes in #f72585, #7209b7, #4cc9f0. No cuts: each idea grows out of the previous shape through a readable in-between form over 18 to 30 frames, then holds for at least 1 second. Liquid moments use metaball blending so drops merge smoothly. Camera stays still; the shapes do the moving.

### line-draw — Single line & live drawing [drawn] stack=SVG stroke-dashoffset or Canvas path sampling
palette: ['#faf7f0', '#1a1a1a', '#c1121f']
useFor: ['Minimal ads', 'Luxury brands', 'Whiteboard explainers']
 -  The line draws at a steady speed, linear easing, about 800px per second at 1080p.
 -  The camera pans to keep the pen tip in the middle third of the frame.
 -  One fill moment: the closed line floods with colour on a downbeat.
 -  Constant stroke width, round caps.
avoid: Many lines drawing at once, fades in, text typed letter by letter
PROMPT: Style: single continuous line drawing. Warm paper #faf7f0, ink #1a1a1a, one accent #c1121f. One line, round caps, constant 4px width, draws itself at a steady linear speed of about 800px/s and never lifts; each picture becomes the next by continuing the line. The camera pans to keep the pen tip in the middle third. One moment where a closed shape floods with the accent colour on a beat.

### dataviz — Data story [explain] stack=Canvas 2D or SVG + d3 scales
palette: ['#fffdf7', '#222222', '#d62828', '#457b9d']
useFor: ['Reports', 'Data journalism', 'Investor updates']
 -  One reading per screen. Never show two charts at once.
 -  Bars grow from the baseline in 20 frames with ease-out; counters roll to the exact value and stop.
 -  Every number on screen comes from the data you were given.
 -  Axis labels at least 28px at 1080p so they read on a phone.
avoid: 3D charts, rainbow palettes, decorative gridlines, numbers that are not in the source
PROMPT: Style: editorial data storytelling. Cream #fffdf7, ink #222, one highlight red #d62828 for the series that matters, muted blue #457b9d for the rest. One reading per screen. Bars and lines grow from the baseline over 20 frames with ease-out, counters roll to the exact value and stop dead. One handwritten-style annotation per chart says why the change matters. Labels at least 28px. Use only numbers from the data provided.

### isometric — Isometric miniature world [dimensional] stack=Three.js orthographic camera, or Canvas with an iso projection
palette: ['#eef2f3', '#2d3142', '#ef8354', '#4f5d75', '#bfc0c0']
useFor: ['Architecture diagrams', 'Supply chains', 'App feature demos']
 -  True isometric angles. The camera slides, it never rotates in perspective.
 -  Objects drop in from 40px above with a small bounce, staggered by 3 frames.
 -  Three tones per material: top light, left mid, right dark.
 -  Things open to reveal their insides instead of cutting to a new scene.
avoid: Perspective cameras, realistic textures, labels floating without leader lines
PROMPT: Style: isometric miniature world. Orthographic camera at true isometric angles; it slides but never rotates into perspective. Background #eef2f3, ink #2d3142, accent #ef8354, shades #4f5d75 and #bfc0c0. Every block has three flat tones: light top, mid left, dark right. Pieces drop in from 40px above with a small bounce, staggered by 3 frames. To explain a step, lift the roof off a building and show the process inside. Labels use thin leader lines.

### dark-keynote — Dark tech keynote [explain] stack=Canvas 2D, or Three.js for a product model
palette: ['#0a0a0a', '#f5f5f5', '#8b8b8b', '#ff5a1f']
useFor: ['Product launches', 'AI and SaaS', 'Feature reveals']
 -  Slow, long-tail easing, cubic-bezier(.16,1,.3,1), 30 to 45 frames per move.
 -  One giant number per piece, 30% of frame height, counted up to its exact value.
 -  Reveals come from light: a soft sweep passes and leaves the object lit.
 -  The accent colour appears on one thing only.
avoid: Lens flares, neon glow, particle bursts, more than one accent colour
PROMPT: Style: dark tech keynote. Near-black #0a0a0a stage with a faint hairline grid, white #f5f5f5 type, grey #8b8b8b secondary, one accent #ff5a1f on a single element. Slow long-tail easing cubic-bezier(.16,1,.3,1), 30 to 45 frames per move. Objects are revealed by a soft light sweep rather than fades. One giant number at 30% of frame height counts up to its exact value. No lens flares, no glow, no particles.

### screencast — Living UI screencast [explain] stack=HTML + CSS + SVG, driven by a timeline seeked to t
palette: ['#ffffff', '#f3f4f6', '#111827', '#2563eb']
useFor: ['Product tutorials', 'Feature launches', 'Changelogs']
 -  Rebuild the real UI with real copy and colours. Never use screenshots.
 -  The cursor moves on eased curves, 20 to 30 frames per move, and pauses 8 frames before each click.
 -  Zoom to 1.6x on the detail that matters, then pull back.
 -  One action every 3 to 4 seconds so the viewer can follow.
avoid: Fake features, cursor teleporting, lorem ipsum, zooming on nothing
PROMPT: Style: living screencast. Rebuild the interface in HTML and CSS with its real copy, fonts and colours; no screenshots. A cursor moves on eased curves over 20 to 30 frames, pauses 8 frames, clicks with a small ripple. The camera zooms to 1.6x on each detail that matters, then pulls back. One action every 3 to 4 seconds. Do not show any feature that the product does not have.

### hud — HUD & terminal [retro] stack=Canvas 2D glyph grid, SVG overlays, optional Three.js wireframe
palette: ['#050b0f', '#38e8ff', '#ffb000', '#1d3540']
useFor: ['Developer tools', 'Spec walkthroughs', 'Sci-fi and AI demos']
 -  All text is monospace and sits on a character grid.
 -  Numbers roll through random glyphs for 6 to 10 frames before settling on the real value.
 -  Brackets lock onto a target in 3 steps: wide, tighter, locked with a tick.
 -  Two colours max on the dark field, plus dim grid lines.
avoid: Heavy glow and bloom, glitch tearing, unreadable tiny text
PROMPT: Style: technical HUD. Dark #050b0f field, cyan #38e8ff primary, amber #ffb000 for warnings, dim #1d3540 grid. All type monospace on a character grid. Numbers scramble through glyphs for 6 to 10 frames then lock to the true value. Target brackets lock in three steps with a tick. Thin 1.5px lines, no bloom, no glitch tearing, every label readable at 1080p.

### painterly — Watercolour & ink [drawn] stack=Canvas brush engine or p5.js + p5.brush
palette: ['#f4efe6', '#2f3e46', '#bc4749', '#6a994e', '#a7c4d2']
useFor: ['Storytelling', 'Travel and nature', 'Cultural brands']
 -  Everything is painted with strokes. No plain vector shapes.
 -  Washes reveal over 15 to 25 frames and bleed 4 to 8px past the ink line.
 -  Paper texture is always visible; pure white and pure black never appear.
 -  Linework re-randomises 12 times a second from a seed, so it lives without flickering.
avoid: Perfect geometric shapes, digital gradients, text labels on everything
PROMPT: Style: watercolour and ink on paper. Warm paper #f4efe6 with visible grain, ink #2f3e46, washes in #bc4749, #6a994e, #a7c4d2. Paint every element with brush strokes, never plain shapes. Washes spread over 15 to 25 frames and bleed slightly past the ink. Linework wobbles on twos (re-seeded 12 times per second from a fixed seed). No pure white, no pure black, very little text.

### print — Risograph & halftone print [drawn] stack=Canvas 2D or a WebGL print shader
palette: ['#f3ede2', '#ff48b0', '#0078bf', '#ffe800']
useFor: ['Indie brands', 'Zines', 'Event posters']
 -  Two or three inks only. Where inks overlap they multiply.
 -  Each plate is offset 2 to 4px from the others and stays there.
 -  Tones are halftone dots, no smooth gradients.
 -  Motion steps at 12fps for a printed, hand-pulled feel.
avoid: A fourth ink, perfect registration, glossy highlights
PROMPT: Style: risograph print. Warm paper #f3ede2. Two spot inks, fluorescent pink #ff48b0 and blue #0078bf (optional yellow #ffe800), overprinted with multiply blending. Each ink plate is misregistered 2 to 4px and stays offset. All tones are halftone dots, never smooth gradients. Animation steps at 12fps while the camera stays smooth.

### papercut — Paper cut-out & collage [drawn] stack=Canvas or DOM layers with drop shadows between them
palette: ['#e9e3d5', '#1b1b1b', '#e76f51', '#2a9d8f', '#f4a261']
useFor: ['Music and fashion', 'Kids stories', 'Editorial pieces']
 -  Every piece has a white or cut edge and a small hard shadow on the layer below.
 -  Pieces move in stop-motion steps at 12fps; the camera can move at 24.
 -  Depth comes from 3 to 6 parallax layers.
 -  Joints pivot like split pins, they do not bend.
avoid: Soft blurred shadows, smooth 60fps character motion, vector-perfect edges
PROMPT: Style: paper cut-out collage. Card colours #e9e3d5, #e76f51, #2a9d8f, #f4a261 with black #1b1b1b details. Every piece has a slightly rough white cut edge and a small hard shadow on the layer below. Characters move in stop-motion steps at 12fps with split-pin joints; the camera drifts smoothly across 3 to 6 parallax layers.

### cel — Hand-drawn line boil [drawn] stack=Canvas 2D variable-width strokes with 3 jitter variants
palette: ['#fffaf0', '#1c1c1c', '#ff595e', '#1982c4', '#ffca3a']
useFor: ['Character shorts', 'Playful brands', 'Social clips']
 -  Animate on twos: the drawing changes every 2 frames at 24fps.
 -  Cycle 3 jitter variants of every line so it boils without strobing.
 -  Fast moves get a smear frame instead of motion blur.
 -  Anticipation before every big action: a small move the other way for 4 to 6 frames.
avoid: Tweened vector motion at 60fps, perfect circles, text standing in for acting
PROMPT: Style: hand-drawn cartoon with line boil. Off-white #fffaf0, ink #1c1c1c, flat fills #ff595e, #1982c4, #ffca3a. 24fps animated on twos. Every line has 3 jitter variants cycled so it boils. Fast moves use a smear frame, every big action gets 4 to 6 frames of anticipation, faces act. Variable-width ink lines, no perfect geometric shapes, almost no text.

### pixel — Pixel art & retro game [retro] stack=Canvas at 320x180, scaled up with nearest-neighbour
palette: ['#1a1c2c', '#5d275d', '#b13e53', '#ef7d57', '#ffcd75', '#a7f070', '#38b764', '#41a6f6']
useFor: ['Game trailers', 'Nostalgia marketing', 'Year-in-review']
 -  Draw at 320x180 and scale by 6 with image smoothing off. Never draw at full resolution.
 -  One fixed palette of 16 to 32 colours. Shading uses dithering, not blending.
 -  Sprites animate at 8 to 12fps; the camera snaps to whole pixels.
 -  Text uses a pixel font and types out in dialogue boxes.
avoid: Mixed pixel sizes, blurry scaling, anti-aliased edges, smooth sub-pixel motion
PROMPT: Style: 16-bit pixel art. Render to a 320x180 canvas and scale 6x with imageSmoothingEnabled = false. Use one fixed palette (#1a1c2c, #5d275d, #b13e53, #ef7d57, #ffcd75, #a7f070, #38b764, #41a6f6 plus greys). Shading by dithering only. Sprites animate at 8 to 12fps, camera moves in whole pixels, dialogue in a pixel font that types out in a bordered box.

### tape — VHS, film & CRT eras [retro] stack=Canvas or Three.js scene plus a WebGL post-processing pass
palette: ['#120f1d', '#ff3fa4', '#00e5ff', '#ffd166']
useFor: ['Music videos', 'Throwback campaigns', 'Mystery teasers']
 -  Pick one era and commit: 1920s film, 1980s VHS, or 1990s camcorder.
 -  Texture is seeded per frame index, so grain changes every frame but renders the same every time.
 -  Gate weave of about 1px and brightness flicker of about 5% for film. Chroma shift of 2 to 3px for tape.
 -  Keep it legible: the effect sits on top of a clear composition, it is not the composition.
avoid: Stacking every retro effect at once, glitch tearing over important text
PROMPT: Style: 1980s VHS tape. Scene in deep #120f1d with neon accents #ff3fa4, #00e5ff and warm #ffd166. Post pass: scanlines, 2 to 3px chroma shift, slight tape noise and an occasional tracking line, all seeded by frame index so the render is deterministic. A chrome title moment. Keep the composition clear underneath; the tape texture never covers key text.

### toy3d — Toy & material 3D [dimensional] stack=Three.js with physical materials and an environment map
palette: ['#f6e6e4', '#ff8fab', '#7bdff2', '#b2f7ef', '#fcbf49']
useFor: ['Product films', 'Brand idents', 'Playful explainers']
 -  Soft studio light from one big key and a fill. Matte or soft-gloss materials.
 -  Shallow depth of field keeps attention on one object.
 -  Objects arrive with weight: fast in, 2 small settles, no floating.
 -  Fixed random seed for every procedural shape.
avoid: Chrome everything, hard black shadows, objects floating with no contact shadow
PROMPT: Style: toy-like 3D. Three.js, soft studio lighting with one large key and a fill, pastel background #f6e6e4, matte and soft-gloss materials in #ff8fab, #7bdff2, #b2f7ef, #fcbf49. Shallow depth of field on the hero object. Objects land with weight and two small settles, always with a contact shadow. Fixed seeds for any procedural geometry.

### social — Vertical social captions [graphic] stack=HTML + CSS text, Canvas for backgrounds
palette: ['#000000', '#ffffff', '#ffe600', '#ff2e63']
useFor: ['Reels, Shorts, TikTok', 'Founder clips', 'Tips and listicles']
 -  1080x1920. Keep everything inside the middle 80% so platform buttons do not cover it.
 -  Captions of 1 to 4 words, each popping in on its spoken beat with a 6 frame scale overshoot.
 -  The first second must hook with the sound off.
 -  Highlight one word per caption in the accent colour.
avoid: Long sentences on screen, text in the bottom 15%, small type
PROMPT: Style: vertical social captions. 1080x1920, all content inside the middle 80% of the frame. Black #000 and white #fff with yellow #ffe600 for the one highlighted word per caption and pink #ff2e63 for emphasis stamps. Captions are 1 to 4 words, chunky with a thick outline, popping in on each beat with a 6 frame scale overshoot. The first second must work with the sound off.
