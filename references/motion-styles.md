# Motion styles

Styles adapted from Awesome Claude (https://awesomeclaude.ai/claude-motion-graphics, github.com/webfuse-com/awesome-claude, CC0-1.0; site footer says MIT) and from bang-motion (https://github.com/bangtutorial/bang-motion, MIT, © 2026 Bang Tutorial). The licenses and the list of adapted styles are in `THIRD_PARTY_NOTICES.md`. Each section's `source` line names where it came from.

Gate 3 (`SKILL.md` § Look (gate 3)) builds each of its three looks from one style on this page. A style is numbers: a palette, fonts, a runtime, eases, timings, rules, an avoid list and a style prompt. A look copies them and changes only what `## Picking three` allows.

Conventions:

- Output is 1920x1080 at 30 fps. Frame counts are written as `N f (S s)` at 30 fps.
- `runtime: gsap`: every effect is a GSAP `fromTo` of DOM or SVG elements. No CSS filters, no `onUpdate:`. A counter is a strip of digit elements moved with `y`, not a tween that rewrites text.
- `runtime: hf-seek`: a `<canvas>` drawn with Canvas 2D only (`getContext("2d")`), or SVG attributes and transforms written, from `e.detail.time` in an `hf-seek` listener (`<hyperframes dir>/references/runtimes.md`, `<hyperframes dir>/references/types/3d.md`). `render(t)` is a pure function of `t`. Anything simulated is computed once at load into arrays. Heavy setup registers `window.__hf.buildReady["<style id>"]`. Seed every random choice with `fx.rand(seed)`; never `Math.random()`. WebGL fails the fast-capture lint, because it always forces screenshot capture.
- Cubic-bezier eases load as `CustomEase` (`https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/CustomEase.min.js`, already in `assets/index.template.html`): `CustomEase.create("snap", "M0,0 C0.7,0 0.2,1 1,1")`.
- Rates that are not 30 fps: on twos at 24 fps draws `floor(t * 12)`. 12 fps steps are `fx.stepped(d)` in `gsap` and `floor(t * 12)` in `hf-seek`.
- Fonts are any Google Fonts family. A family outside the HyperFrames bundle is downloaded with `scripts/fetch_font.py` (`SKILL.md` § Look (gate 3)). Inter, Space Grotesk and JetBrains Mono are never the display face.

## swiss — Swiss grid & kinetic type
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#swiss
- group: graphic
- fits: brand and event openers, titles, one-subject statements
- palette: ground #f5f2ea · ink #111111 · accent #e63323
- fonts: display Roboto 900 · body Roboto 500
- runtime: gsap
- motion: every snap uses `CustomEase.create("snap", "M0,0 C0.7,0 0.2,1 1,1")`; lines being drawn use `ease: "none"`. Entrances are wipes: `clipPath` `inset()` from closed to open. Deletions are hard cuts: `tl.set(sel, { opacity: 0 }, t)` on the beat. Grid: 12 columns, 4% margins of each axis (76.8 px left and right, 43.2 px top and bottom), 147.2 px per column.
- rules: One easing curve for snaps, cubic-bezier(.7,0,.2,1). Linear only for lines being drawn. Entrances are wipes or clip reveals, never fades. Deletions are hard cuts. Exactly one element carries the signal colour per shot. That element is the subject. Every position lands on a 12-column grid with 4% margins.
- avoid: Overshoot, springs, drop shadows, more than one typeface, centred-everything layouts
- prompt: Style: Swiss International motion design. Off-white #f5f2ea, black #111, one signal red #e63323 used on a single element per shot. One grotesk typeface in two weights. A visible 12-column grid with 4% margins; every element snaps to it. Snaps use cubic-bezier(.7,0,.2,1), lines draw at linear speed. Entrances are wipes and clip reveals, never fades; exits are hard cuts on the beat. No overshoot, no shadows, no gradients. Type: Roboto 900 for display, Roboto 500 for body.

## flat-vector — Flat vector explainer
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#flat-vector
- group: explain
- fits: product and process explainers, onboarding steps, how-it-works
- palette: ground #fdf6ec · ink #2b2d42 · accent #ff6b35 · shade #4ecdc4 · shade #ffd23f
- fonts: display Poppins 700 · body Nunito 600
- runtime: gsap
- motion: entrances use `CustomEase.create("pop", "M0,0 C0.34,1.56 0.64,1 1,1")` and settle within 12 f (0.4 s). Stagger groups by 2 to 4 f (0.07 to 0.13 s), 3 f (0.1 s) by default. A scene change is a shape that scales up to fill the frame (`scale` `fromTo`) and becomes the next ground. Outlines are at least 3 px at 1080p.
- rules: Entrances overshoot with cubic-bezier(0.34,1.56,0.64,1) and settle within 12 frames. Stagger groups by 2 to 4 frames, never all at once. Transitions are carried by an element: a shape grows to fill the frame and becomes the next background. Four to five flat colours, no gradients, no outlines thinner than 3px at 1080p.
- avoid: Stock-illustration people with tiny heads, gradients, crossfades between scenes
- prompt: Style: flat vector explainer. Palette #fdf6ec background, #2b2d42 ink, accents #ff6b35, #4ecdc4, #ffd23f. Geometric shapes and simple characters built from circles and rounded rectangles, no gradients. Entrances overshoot with cubic-bezier(0.34,1.56,0.64,1) and settle within 12 frames, groups stagger by 3 frames. Scene changes are carried by a shape that grows to fill the frame and becomes the next background. No crossfades. Type: Poppins 700 for display, Nunito 600 for body.

## morph — Shape morph & liquid
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#morph
- group: graphic
- fits: topic-to-topic stories, a concept that turns into another, brand narratives
- palette: ground #0d1b2a · accent #f72585 · shade #7209b7 · shade #4cc9f0
- fonts: display League Gothic 400 · body Lato 400
- runtime: gsap + hf-seek
- motion: SVG morphs are `fromTo` tweens of paths with the same number of points, 18 to 30 f (0.6 to 1.0 s) each, through a readable in-between shape. Hold every finished shape at least 30 f (1.0 s). Liquid moments are a Canvas 2D drawing of metaballs drawn from `e.detail.time` in `hf-seek` with smooth-min blending, the ball paths computed once at load. No cuts, and the camera stays still.
- rules: There are no cuts. Every new idea grows out of the previous shape. Each morph takes 18 to 30 frames and passes through a readable in-between shape. Hold each finished shape at least 1 second so it reads. Liquid joins use smooth-min blending, never a hard overlap.
- avoid: Morphs that pass through a shapeless blob, constant motion with no holds
- prompt: Style: continuous shape morph. Dark #0d1b2a field, shapes in #f72585, #7209b7, #4cc9f0. No cuts: each idea grows out of the previous shape through a readable in-between form over 18 to 30 frames, then holds for at least 1 second. Liquid moments use metaball blending so drops merge smoothly. Camera stays still; the shapes do the moving. Type: League Gothic 400 for display, Lato 400 for body.

## line-draw — Single line & live drawing
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#line-draw
- group: drawn
- fits: minimal explainers, a path or journey, whiteboard-style steps
- palette: ground #faf7f0 · ink #1a1a1a · accent #c1121f
- fonts: display Playfair Display 600 · body EB Garamond 400
- runtime: gsap
- motion: the line draws with `stroke-dashoffset` at `ease: "none"`, about 800 px per second at 1080p (26.7 px per frame). Stroke is 4 px, `stroke-linecap: round`, constant. The camera is a `x` and `y` tween of the whole drawing that keeps the pen tip in the middle third of the frame (640 to 1280 px across). One fill moment: a closed shape floods with the accent on a downbeat word cue.
- rules: The line draws at a steady speed, linear easing, about 800px per second at 1080p. The camera pans to keep the pen tip in the middle third of the frame. One fill moment: the closed line floods with colour on a downbeat. Constant stroke width, round caps.
- avoid: Many lines drawing at once, fades in, text typed letter by letter
- prompt: Style: single continuous line drawing. Warm paper #faf7f0, ink #1a1a1a, one accent #c1121f. One line, round caps, constant 4px width, draws itself at a steady linear speed of about 800px/s and never lifts; each picture becomes the next by continuing the line. The camera pans to keep the pen tip in the middle third. One moment where a closed shape floods with the accent colour on a beat. Type: Playfair Display 600 for display, EB Garamond 400 for body.

## dataviz — Data story
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#dataviz
- group: explain
- fits: numbers, metrics, before and after, reports
- palette: ground #fffdf7 · ink #222222 · accent #d62828 · shade #457b9d
- fonts: display Playfair Display 700 · body Lato 400 (numbers in IBM Plex Mono 500)
- runtime: gsap
- motion: bars and lines grow from the baseline in 20 f (0.67 s) with `ease: "power3.out"`. Counters are digit strips moved with `y` to the exact value over the same 20 f, with the same ease; they stop dead. One chart per screen. Axis labels at least 28 px at 1080p. One annotation per chart.
- rules: One reading per screen. Never show two charts at once. Bars grow from the baseline in 20 frames with ease-out; counters roll to the exact value and stop. Every number on screen comes from the data you were given. Axis labels at least 28px at 1080p so they read on a phone.
- avoid: 3D charts, rainbow palettes, decorative gridlines, numbers that are not in the source
- prompt: Style: editorial data storytelling. Cream #fffdf7, ink #222, one highlight red #d62828 for the series that matters, muted blue #457b9d for the rest. One reading per screen. Bars and lines grow from the baseline over 20 frames with ease-out, counters roll to the exact value and stop dead. One handwritten-style annotation per chart says why the change matters. Labels at least 28px. Use only numbers from the data provided. Type: Playfair Display 700 for display, Lato 400 for body, IBM Plex Mono 500 for numbers.

## isometric — Isometric miniature world
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#isometric
- group: dimensional
- fits: architecture and system diagrams, flows between parts, feature maps
- palette: ground #eef2f3 · ink #2d3142 · accent #ef8354 · shade #4f5d75 · shade #bfc0c0
- fonts: display Montserrat 700 · body Open Sans 500
- runtime: gsap
- motion: SVG polygons in a true isometric projection (30 degrees). Objects drop in from 40 px above (`y` `fromTo`) with `ease: "back.out(1.4)"`, staggered by 3 f (0.1 s). The camera slides: an `x` and `y` tween of the whole world, never a perspective rotation. A reveal lifts a roof off (`y` and `opacity`) to show the inside. Three tones per material: top light, left mid, right dark. Labels have thin leader lines.
- rules: True isometric angles. The camera slides, it never rotates in perspective. Objects drop in from 40px above with a small bounce, staggered by 3 frames. Three tones per material: top light, left mid, right dark. Things open to reveal their insides instead of cutting to a new scene.
- avoid: Perspective cameras, realistic textures, labels floating without leader lines
- prompt: Style: isometric miniature world. Orthographic camera at true isometric angles; it slides but never rotates into perspective. Background #eef2f3, ink #2d3142, accent #ef8354, shades #4f5d75 and #bfc0c0. Every block has three flat tones: light top, mid left, dark right. Pieces drop in from 40px above with a small bounce, staggered by 3 frames. To explain a step, lift the roof off a building and show the process inside. Labels use thin leader lines. Type: Montserrat 700 for display, Open Sans 500 for body.

## dark-keynote — Dark tech keynote
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#dark-keynote
- group: explain
- fits: launches, feature reveals, one big number, AI and SaaS topics
- palette: ground #0a0a0a · ink #f5f5f5 · shade #8b8b8b · accent #ff5a1f
- fonts: display Outfit 600 · body Inter 400
- runtime: gsap
- motion: every move uses `CustomEase.create("long-tail", "M0,0 C0.16,1 0.3,1 1,1")`, 30 to 45 f (1.0 to 1.5 s). One giant number per piece at 30% of frame height (324 px), a digit strip that counts to the exact value with the same ease. A reveal is a soft sweep: a gradient band moved with `x` across the object (no glow, no filter). A hairline grid sits under everything. The accent is on one element.
- rules: Slow, long-tail easing, cubic-bezier(.16,1,.3,1), 30 to 45 frames per move. One giant number per piece, 30% of frame height, counted up to its exact value. Reveals come from light: a soft sweep passes and leaves the object lit. The accent colour appears on one thing only.
- avoid: Lens flares, neon glow, particle bursts, more than one accent colour
- prompt: Style: dark tech keynote. Near-black #0a0a0a stage with a faint hairline grid, white #f5f5f5 type, grey #8b8b8b secondary, one accent #ff5a1f on a single element. Slow long-tail easing cubic-bezier(.16,1,.3,1), 30 to 45 frames per move. Objects are revealed by a soft light sweep rather than fades. One giant number at 30% of frame height counts up to its exact value. No lens flares, no glow, no particles. Type: Outfit 600 for display, Inter 400 for body.

## screencast — Living UI screencast
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#screencast
- group: explain
- fits: product tutorials, how a tool is used, changelogs, UI walkthroughs
- palette: ground #ffffff · shade #f3f4f6 · ink #111827 · accent #2563eb
- fonts: display Roboto 700 · body Inter 400
- runtime: gsap
- motion: the UI is HTML and CSS with its real copy. The cursor is an `x` and `y` tween of 20 to 30 f (0.67 to 1.0 s) with `ease: "power2.inOut"`, then a pause of 8 f (0.27 s) before each click, then a small ripple (a ring that scales and fades). The camera zooms to 1.6x on the detail that matters (`scale` on the UI wrapper), then pulls back. One action every 3 to 4 s (90 to 120 f).
- rules: Rebuild the real UI with real copy and colours. Never use screenshots. The cursor moves on eased curves, 20 to 30 frames per move, and pauses 8 frames before each click. Zoom to 1.6x on the detail that matters, then pull back. One action every 3 to 4 seconds so the viewer can follow.
- avoid: Fake features, cursor teleporting, lorem ipsum, zooming on nothing
- prompt: Style: living screencast. Rebuild the interface in HTML and CSS with its real copy, fonts and colours; no screenshots. A cursor moves on eased curves over 20 to 30 frames, pauses 8 frames, clicks with a small ripple. The camera zooms to 1.6x on each detail that matters, then pulls back. One action every 3 to 4 seconds. Do not show any feature that the product does not have. Type: Roboto 700 for display, Inter 400 for body.

## hud — HUD & terminal
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#hud
- group: retro
- fits: developer tools, specs and pipelines, status and numbers on a dark field
- palette: ground #050b0f · ink #38e8ff · accent #ffb000 · shade #1d3540
- fonts: display Space Mono 700 · body IBM Plex Mono 400
- runtime: gsap
- motion: all text is monospace on a character grid. A number scrambles for 6 to 10 f (0.2 to 0.33 s), one glyph per frame, then locks to the true value: stack the glyph frames as spans (glyphs chosen once with `fx.rand`), each shown for one frame by an `opacity` `fromTo` of `duration: 1/30`, no `onUpdate`. Brackets lock in 3 steps (wide, tighter, locked with a tick), each step a `scale` `fromTo`. Lines are 1.5 px. Two colours on the dark field, plus the dim grid.
- rules: All text is monospace and sits on a character grid. Numbers roll through random glyphs for 6 to 10 frames before settling on the real value. Brackets lock onto a target in 3 steps: wide, tighter, locked with a tick. Two colours max on the dark field, plus dim grid lines.
- avoid: Heavy glow and bloom, glitch tearing, unreadable tiny text
- prompt: Style: technical HUD. Dark #050b0f field, cyan #38e8ff primary, amber #ffb000 for warnings, dim #1d3540 grid. All type monospace on a character grid. Numbers scramble through glyphs for 6 to 10 frames then lock to the true value. Target brackets lock in three steps with a tick. Thin 1.5px lines, no bloom, no glitch tearing, every label readable at 1080p. Type: Space Mono 700 for display, IBM Plex Mono 400 for body.

## painterly — Watercolour & ink
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#painterly
- group: drawn
- fits: stories, places, culture and people topics, soft explainers with little text
- palette: ground #f4efe6 · ink #2f3e46 · accent #bc4749 · shade #6a994e · shade #a7c4d2
- fonts: display Caveat Brush 400 · body Lato 400
- runtime: hf-seek
- motion: a plain Canvas 2D brush engine (strokes with a width profile, no p5). Washes spread over 15 to 25 f (0.5 to 0.83 s) and bleed 4 to 8 px past the ink line. Linework is re-seeded 12 times a second: seed = `floor(t * 12)` into `fx.rand`, so it wobbles on twos without flicker. The paper grain is drawn once from a fixed seed. Pure white and pure black never appear.
- rules: Everything is painted with strokes. No plain vector shapes. Washes reveal over 15 to 25 frames and bleed 4 to 8px past the ink line. Paper texture is always visible; pure white and pure black never appear. Linework re-randomises 12 times a second from a seed, so it lives without flickering.
- avoid: Perfect geometric shapes, digital gradients, text labels on everything
- prompt: Style: watercolour and ink on paper. Warm paper #f4efe6 with visible grain, ink #2f3e46, washes in #bc4749, #6a994e, #a7c4d2. Paint every element with brush strokes, never plain shapes. Washes spread over 15 to 25 frames and bleed slightly past the ink. Linework wobbles on twos (re-seeded 12 times per second from a fixed seed). No pure white, no pure black, very little text. Type: EB Garamond 500 for display, Lato 400 for body.

## print — Risograph & halftone print
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#print
- group: drawn
- fits: zines and posters, indie and event announcements, bold two-colour stories
- palette: ground #f3ede2 · accent #ff48b0 · shade #0078bf · shade #ffe800
- fonts: display Archivo Black 400 · body Space Mono 400
- runtime: gsap
- motion: motion steps at 12 fps: every tween on a piece uses `ease: fx.stepped(d)` (12 steps per second); the camera tween stays smooth. Two or three ink plates, each a layer with `mix-blend-mode: multiply`, offset 2 to 4 px from the others for the whole scene. Tones are halftone dots (a repeating radial-gradient or SVG pattern), never a smooth gradient.
- rules: Two or three inks only. Where inks overlap they multiply. Each plate is offset 2 to 4px from the others and stays there. Tones are halftone dots, no smooth gradients. Motion steps at 12fps for a printed, hand-pulled feel.
- avoid: A fourth ink, perfect registration, glossy highlights
- prompt: Style: risograph print. Warm paper #f3ede2. Two spot inks, fluorescent pink #ff48b0 and blue #0078bf (optional yellow #ffe800), overprinted with multiply blending. Each ink plate is misregistered 2 to 4px and stays offset. All tones are halftone dots, never smooth gradients. Animation steps at 12fps while the camera stays smooth. Type: Archivo Black 400 for display, Space Mono 400 for body.

## papercut — Paper cut-out & collage
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#papercut
- group: drawn
- fits: editorial and playful stories, people and objects as pieces, layered scenes
- palette: ground #e9e3d5 · ink #1b1b1b · accent #e76f51 · shade #2a9d8f · shade #f4a261
- fonts: display Oswald 700 · body Nunito 600
- runtime: gsap
- motion: pieces move in stop-motion steps at 12 fps: `ease: fx.stepped(d)`. The camera drifts at 24 fps: `ease: fx.stepped(d, 24)`. 3 to 6 parallax layers moved at different speeds. Each piece has a white cut edge and a small hard shadow (a duplicate dark shape offset a few px, or a `box-shadow` with 0 blur) on the layer below. Joints pivot around a point (`transformOrigin`) and do not bend.
- rules: Every piece has a white or cut edge and a small hard shadow on the layer below. Pieces move in stop-motion steps at 12fps; the camera can move at 24. Depth comes from 3 to 6 parallax layers. Joints pivot like split pins, they do not bend.
- avoid: Soft blurred shadows, smooth 60fps character motion, vector-perfect edges
- prompt: Style: paper cut-out collage. Card colours #e9e3d5, #e76f51, #2a9d8f, #f4a261 with black #1b1b1b details. Every piece has a slightly rough white cut edge and a small hard shadow on the layer below. Characters move in stop-motion steps at 12fps with split-pin joints; the camera drifts smoothly across 3 to 6 parallax layers. Type: Oswald 700 for display, Nunito 600 for body.

## cel — Hand-drawn line boil
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#cel
- group: drawn
- fits: playful explainers, diagrams, arrows and icons that feel drawn by hand
- palette: ground #fffaf0 · ink #1c1c1c · accent #ff595e · shade #1982c4 · shade #ffca3a
- fonts: display Patrick Hand 400 · body Nunito 600
- runtime: hf-seek
- motion: Canvas 2D variable-width strokes, on twos at 24 fps: the drawing index is `floor(t * 12)`. Three jitter variants of every line, variant = `floor(t * 12) % 3`, each from a fixed `fx.rand` seed, so lines boil without strobing. A fast move gets one smear frame (the shape stretched along its path for one drawing) instead of motion blur. Anticipation before every big action: a small move the other way for 4 to 6 f (0.13 to 0.2 s).
- rules: Animate on twos: the drawing changes every 2 frames at 24fps. Cycle 3 jitter variants of every line so it boils without strobing. Fast moves get a smear frame instead of motion blur. Anticipation before every big action: a small move the other way for 4 to 6 frames.
- avoid: Tweened vector motion at 60fps, perfect circles, text standing in for acting
- prompt: Style: hand-drawn cartoon with line boil. Off-white #fffaf0, ink #1c1c1c, flat fills #ff595e, #1982c4, #ffca3a. 24fps animated on twos. Every line has 3 jitter variants cycled so it boils. Fast moves use a smear frame, every big action gets 4 to 6 frames of anticipation, faces act. Variable-width ink lines, no perfect geometric shapes, almost no text. Type: Outfit 800 for display, Nunito 600 for body. No characters unless a source has one: the linework boils on diagrams, arrows and icons.

## pixel — Pixel art & retro game
- source: Awesome Claude, https://awesomeclaude.ai/claude-motion-graphics#pixel
- group: retro
- fits: nostalgia and game-like stories, year in review, step-by-step levels
- palette: ground #1a1c2c · shade #5d275d · shade #b13e53 · accent #ef7d57 · shade #ffcd75 · shade #a7f070 · shade #38b764 · shade #41a6f6
- fonts: display Press Start 2P 400 · body Press Start 2P 400
- runtime: hf-seek
- motion: draw on a 320x180 canvas and scale it 6x to 1920x1080 with `imageSmoothingEnabled = false`. Sprites animate at 8 to 12 fps: frame = `floor(t * 12)` or `floor(t * 8)`. The camera moves in whole pixels (`Math.round`). Shading is dithering. Text is Press Start 2P at 8 px drawn with `fillText` on the small canvas, typed out in a bordered box one character per beat.
- rules: Draw at 320x180 and scale by 6 with image smoothing off. Never draw at full resolution. One fixed palette of 16 to 32 colours. Shading uses dithering, not blending. Sprites animate at 8 to 12fps; the camera snaps to whole pixels. Text uses a pixel font and types out in dialogue boxes.
- avoid: Mixed pixel sizes, blurry scaling, anti-aliased edges, smooth sub-pixel motion
- prompt: Style: 16-bit pixel art. Render to a 320x180 canvas and scale 6x with imageSmoothingEnabled = false. Use one fixed palette (#1a1c2c, #5d275d, #b13e53, #ef7d57, #ffcd75, #a7f070, #38b764, #41a6f6 plus greys). Shading by dithering only. Sprites animate at 8 to 12fps, camera moves in whole pixels, dialogue in a pixel font that types out in a bordered box. Type: Space Mono 700 for display, Space Mono 400 for body.

## continuous-action — Continuous action
- source: bang-motion (MIT, © 2026 Bang Tutorial), https://github.com/bangtutorial/bang-motion, README.md:58,128; bang-motion/references/explainer.md:37-44,86-104,467-579; bang-motion/assets/starter-explainer.html:1-210
- group: explain
- fits: a pipeline or a journey with one thing moving through it
- palette: ground #cfe0f5 (sky) · shade #f5efe3 (warm sky) · shade #a7bedf (far hills) · shade #9cc27e (hills) · shade #7fb06a (near hills) · shade #cfe19c (field) · ink #1c2a4a · accent #d7262c · shade #ffffff (hero body) · shade #dfe3ea (wheel) · shade #2b3346 (tyre) · shade #c9d0da (road) · shade #bcd9ee (map water) · shade #ece6d2 (map land)
- fonts: display Unbounded 900 · body Plus Jakarta Sans 700 (the one world label, 44 px with .18em tracking; the number is 210 px)
- runtime: gsap + hf-seek
- motion: the world is one `hf-seek` listener that writes SVG `transform` attributes from `e.detail.time`. Upstream renders at 60 fps from the timeline time; here every position is a function of `t`, so the frame rate never enters. Speed profile in px/s: `VK = [[0,600],[1.2,900],[15,900],[19,0],[DUR+1,0]]`; the distance `D(t)` is integrated once at load in steps of 1/240 s into an array and read back by `t`. Strips are 2 tiles of 2400 px at factors far .18, hills .38, ground .62, deep objects .8; a world object sits at `x = x0 - (D - d0) * f`. The hero stays at (1380, 700) with a bob of `sin(t * 9) * 2.5` px and a tilt of `sin(t * 3.1) * .25` deg; the wheels turn `(d / 18) * 57.3` deg. The side camera follows `[t, zoom, cx, cy]` keyframes `[0,1,960,540]`, `[2,1.06,900,470]`, `[6,1,960,540]` plus a breathe of `1 + sin(t * .9) * .006`. Map view: route progress `q = smooth((t - 9) / 3.2)`, camera zoom 2.3 to 1 with `e = smooth((t - 9) / 3.4)`; the route is a `stroke-dasharray` of its own length, the marker sits at `getPointAtLength` turned to the tangent, and stations pop from scale 0 to 1 with `back.out(1.4)` in .3 s (ours). A view change (`gsap`, on the view wrapper, so the listener's groups inside it keep one writer): out is y 0 to -120 x dir with opacity 1 to 0 in .28 s `power2.in`, in is y 120 x dir to 0 with opacity 0 to 1 in .36 s `power3.out`; upstream adds `blur(18px)`, which becomes the opacity move over the same times. `fadeUp` is y 30 to 0 with opacity 0 to 1 in .5 s `power3.out` (upstream blur 6 dropped); `fadeOut` is y 0 to -30 with opacity 1 to 0 in .35 s `power2.in` (blur 8 dropped). A changing number is two stacked spans in `overflow:hidden` with a `y` tween, .5 s `power3.out` (ours). An angle whip lasts .25 s with a 60 px shift. A turn rotates the whole world 8 to 15 deg over 1.5 s while the hero tilts 3 to 5 deg further. A palette swap takes .3 s. Sway is 6 to 10 px with a different period per object. The background never stops for reading: it slows to 40%. Upstream's collage view is not used, because it needs cutouts.
- rules: One hero from second 0 to the end: it never leaves the frame, and its silhouette, colour and position stay. Always moving: 2 or 3 parallax layers, speed lines, spark, dust or smoke particles, a wobbling subject, no fully still second. Numbers are scenery: the hero crosses in front of them, and a changing number rolls like an odometer. The viewpoint changes at least every 2 scenes and never shows the same angle three times in a row: side, cab speedometer, route map, elevation profile, map race, head-on, interior. Comparisons happen inside the same world, never in split screens. Text has two levels only, a big number and a world label; no subtitle, kicker, body or badge, and no text under 30 px at 1080. The screen shows the noun or the number and the voice carries the sentence. The whole world is SVG drawn in code. A map is a stylised vector map, and its numbers appear after the zoom-out.
- avoid: A side-view hero with text from start to end, changing the hero's art per scene, stopping the background to read text, hiding an SVG view with `visibility:hidden` while a child has its own `visibility="visible"` (use `removeAttribute('visibility')`), a floating hero (give it a floor or platform), `gsap.set` `transformOrigin` on SVG groups scaled from local (0,0) (write the `transform` attribute directly), split-screen panels
- prompt: Style: continuous action. One hero, drawn in flat SVG at (1380, 700), crosses the whole piece without leaving the frame, and the world flows past it in parallax strips at factors .18, .38 and .62 over a sky #cfe0f5 and hills #9cc27e, with ink #1c2a4a and one red #d7262c on the hero's stripe. Numbers stand inside the world as scenery and the hero sweeps past them; a changing number rolls like an odometer. The view changes at least every 2 scenes, from side to route map to elevation profile, with a 0.28 s whip; the background never stops. Only a big number and a one-word world label are on screen, never a caption. Type: Unbounded 900 for display, Plus Jakarta Sans 700 for body.

## cartoon-stage — Cartoon stage
- source: bang-motion (MIT, © 2026 Bang Tutorial), https://github.com/bangtutorial/bang-motion, README.md:69,133; bang-motion/references/kartun-panggung.md:1-221; bang-motion/assets/starter-explainer-panggung.html:1-190
- group: drawn
- fits: a process and its impact
- palette: ground #fff3dc (cream) · shade #fffdf5 (white) · ink #263746 · shade #345867 (navy) · shade #172e3c (deep) · accent #e0714f (coral) · shade #237c80 (teal) · shade #8dd3c3 (mint) · shade #5aabb8 (blue) · shade #f4bc52 (gold) · shade #c86545 (rust) · shade #b9cd8e (grass) · shade #9db874 (grass 2) · shade #e6d5ac (sand) · shade #d6bf8e (sand 2) · shade #cb895f (skin) · shade #ede6d3 (wall) · shade #dcd3be (wall 2) · shade #a9b5b3 (metal) · shade #f7f4ea (steam) · shade #bfdde3 (sky top) · shade #f6efdd (sky bottom) · shade #cfe0cc (hill); a warm sky runs #edb095 to #f8d8ad over ground #d88560
- fonts: display Nunito 800 · body Nunito 600 (ours; diegetic signs only, upstream loads no font)
- runtime: gsap + hf-seek
- motion: one stage per scene, drawn as SVG built in code. The camera is `{x, y, z}` with the stage transform `translate(960 - (x + ox) * z, 540 - (y + oy) * z) scale(z)`; zoom stays between 1.08 and 1.95, never below 1.08, interpolated logarithmically, `cam()` default 1.6 s `sine.inOut`. A reference plan: 1.95 to 1.08, then 1.65 to 1.14 to 1.18, then 1.90 to 1.12 to 1.36. Pattern: hold .45 to .7 s, one move per voice beat, hold; a push-in runs 1.12 to 1.45. A stage change is a cut, or a slide of d = 96 px horizontal or 72 px vertical: out in .28 s `power2.in` (offset `-d * q^2`), cut, in in .42 s `power3.out` (offset `+d * (1 - q)^3`), with no scale bump and no sweep lines; upstream also blurs the container up to 10 px, which becomes opacity 1 to 0 on the way out and 0 to 1 on the way in over the same times. An accent transition is only for a real change of place (2 of 6 stages in the reference). Joints are written in the `hf-seek` listener through the proxy `J(el, tx, ty)` holding `{tx, ty, x, y, r, sx, sy}` and `apply()`, which writes the `transform` attribute from `t`, so GSAP never touches a joint. Rig: pelvis (0, -214); thigh at (±26, -214) 118 long to the knee, shin 108 to the ankle; torso (0, -214) from -152 to +8, neck -178 to -138; right arm at (50, -126), upper 98 to the elbow, fore 90 to the wrist; head at (0, -160) with its chin overlapping the neck by 14 px; a character is about 520 px tall at scale 1, head 186 px. The head is the vector fallback: a broad rounded head, one solid hair silhouette, two small solid black dot eyes, two tiny brow strokes, no nose, a tiny curved smile; expressions (happy, worried, shocked) swap the brow and mouth paths, and a blink is the eyes' opacity 0 to 1 to 0 in .13 s every 3.5 s, offset per character. Idle: torso ±1.1 deg every 1.7 s, head ±1.7 deg every 2.3 s, arms ±1 to 1.5 deg every 1.9 s. Walk: `step = sin(t * 8)`, thigh `step * 15` deg, shin `max(0, step) * 18` deg, body bob `abs(step) * 3 - 4` px, the foot shadow follows. A jump is one function `jump(t)` for thighs, shins, arms and shadow. Actions: point (upper arm 6 to -72 deg in .7 s), wave, draw water (arm -62 to -10 deg, yoyo .42 s, crank +180 deg), fan the face (forearm -40 to -70 deg, .35 s). A particle is a phase `(t / period) % 1` that sets its motion and a keyframed opacity `[0, .9, .9, 0]`, so one element never has two writers. A fan turns `t * 100` deg; pipe drops follow `getPointAtLength`. Contact shadow: an ellipse of rx 72 x scale, ry 16, opacity .13. The far arm and leg and the dark side of a building are the base colour x .86 to .9. Reference lengths: 39.6 s is 5 stages, 81 s is 7.
- rules: One stage per scene, and the camera is never wide. Inside a stage the action is continuous (a wall lifts, a needle rises, a light turns green, plants grow); a new stage starts only when the place, the scale or the explanation changes. Never fly across the world for 3 s. At least 10 things move on every stage, and each explains a place, an activity or a relation: fan, meter needle, pulsing status light, water along a pipe, river ripples, rising steam or smoke, dust, a bird, laundry, breathing leaves, a walking chicken, blinking rack lights, plants that grow then wilt, cracks, stacking soil layers, a dropping water level. Characters are jointed: a placement group and an animated group are always two different elements, and a joint's transform is only ever written through `J(el, tx, ty).apply()`. Zero captions; only diegetic text (a sign, a label on a machine), and the voice carries the sentences. Bright flat palette, flat fills, no outline, no texture, no vignette; the only shadows are the contact ellipse and a building's dark side. Underground stages: characters at height .85, layers at most 440 px.
- avoid: A miniature world (a huge map at zoom .2 to .7), a frame with zoom below 1.08, paper, grain or watercolour, two repeating opacity tweens on one element (the second overwrites the first, so steam never shows), GSAP `transformOrigin` or `rotation` on SVG joints (the bounding box shifts: the head detaches, a propeller leaves its axis), a GSAP x or y tween on a group that already has `translate()`, sentence captions, 3 s fly-across moves, a scale bump or sweep lines on a transition
- prompt: Style: cartoon stage. Every scene is one bright flat stage in cream #fff3dc, navy #345867, teal #237c80 and coral #e0714f, with the camera held between zoom 1.08 and 1.95 and moving once per voice beat after a hold of .45 to .7 s. At least 10 things move at once on a stage: a fan, a needle, steam, water along a pipe, a blinking light. Jointed characters about 520 px tall, with dot eyes and a small smile, walk, point and wave. Stages change with a cut or a 96 px slide of .28 s out and .42 s in, never a scale bump, and nothing is captioned except signs inside the world. Type: Nunito 800 for display, Nunito 600 for body.

## white-catalog — White catalog
- source: bang-motion (MIT, © 2026 Bang Tutorial), https://github.com/bangtutorial/bang-motion, README.md:62,131; bang-motion/references/explainer.md:37-44,142-188,405-443; bang-motion/assets/starter-explainer-katalog.html:1-200
- group: graphic
- fits: decisions, documents, dates and evidence
- palette: ground #ffffff · ink #141414 · accent #e1251b (stamp, handwritten text) · shade #f7c500 (highlighter, date block) · shade #7a7a7a (muted text) · shade #fffdf3 (handwritten note) · shade #ececec (placeholder); the page grid is rgba(20,20,20,.07) every 120 px
- fonts: display Archivo 900 · body Caveat 600 (mono parts: IBM Plex Mono 500, ours for `ui-monospace`; name labels Archivo 900, ours, upstream used Inter 500)
- runtime: gsap
- motion: the camera, `fly`, `say`, `unsay`, `draw`, `label` and highlighter are the numbers of `cartoon-collage`, with `say` defaulting to mode `scale` (`back.out(1.6)`) and the differences below. `fly` takes a final tilt `rot` of 2 to 5 deg for a document, and its float rotation is `rot + 1.5`. Evidence helpers: `slam` scale 2.2 to 1 with opacity to .92 in .26 s `power4.in`; `block` `clip-path` `inset(0 100% 0 0)` to `inset(0 0 0 0)` in .5 s `power3.out`; `multiply` scale .4 to 1 and rotate -30 to 0 in .4 s `back.out(2)`, stagger .06. A timeline example: `fly` the document from `{x:0, y:400, rotate:6, scale:.9}` in .8 s with `rot: -2`, `slam` its stamp at +.9 s, `block` the date at +1.3 s. A pass through the lens: a large object crosses diagonally in 1.2 to 1.3 s and is gone, 1 or 2 times per scene; upstream's constant horizontal blur becomes an opacity fade at both ends over the same x offset. A dashed circle has a fixed `stroke-dasharray` and is drawn by a `clip-path` `inset()` opening from the left, .7 s `power2.inOut`. A clock is SVG with tweened `rotation` and `svgOrigin`. A world map is an SVG at opacity .16 with a red dot and a dashed route. Shadows: the `drop-shadow()` of upstream's cutouts becomes `box-shadow: 0 24px 30px rgba(20,20,20,.18)` on the wrapper; a document uses `0 30px 34px rgba(20,20,20,.16), 0 6px 8px rgba(20,20,20,.14)` and a border of 2 px rgba(20,20,20,.3).
- rules: Page ground #ffffff with a 120 px grid at rgba(20,20,20,.07), faded to the edge with a radial mask; no grain, no vignette. Every object is HTML or flat SVG: spec-reel has no photos. The evidence objects are a typed `.doc` (white paper, a thin border, monospace, a red `.stamp` tilted 2 to 5 deg), a `.stampblk` date block, a `.pnote` handwritten note and a repeat grid; stamp text is 34 px Archivo 900 with .08em tracking, the date block is 38 px mono, the note is 42 px Caveat, and a document's heading is at least 30 px (upstream 18 px). Each scene holds 3 to 5 elements that accrete with the voice. Text is Caveat for connectors, Archivo 900 for the subject and Archivo 900 italic for the number or claim, at most 2 levels and nothing under 30 px at 1080. The screen shows the noun, the stamp or the date and the voice carries the sentence. A tall object must not collide with body copy: work out its height from its aspect and put the copy above it.
- avoid: A black-and-white or cartoon feel (the colour is red and yellow on white), grain and vignette
- prompt: Style: white catalog. A pure white page #ffffff with a faint 120 px grid, ink #141414, one red #e1251b for stamps and handwriting and one yellow #f7c500 for the highlighter. Evidence is built as objects: a typed document with a tilted red stamp that slams from scale 2.2 in .26 s, a black date block that wipes open in .5 s, a handwritten note, a repeat grid. Objects fly in from below at a tilt in .9 s and the camera pushes to what matters. Script for connectors, heavy sans for the subject, 2 text levels at most. Type: Archivo 900 for display, Caveat 600 for body, IBM Plex Mono 500 for the document.

## cartoon-collage — Cartoon collage
- source: bang-motion (MIT, © 2026 Bang Tutorial), https://github.com/bangtutorial/bang-motion, README.md:66,129; bang-motion/references/explainer.md:9-18,37-44,81-123,190-251,328-365; bang-motion/assets/starter-explainer-kartun.html:1-185
- group: drawn
- fits: friendly explainers of concepts
- palette: ground #f4e9d3 (paper) · ink #221e1b · accent #f26b1d (orange) · shade #1f9e95 (teal) · shade #d63b2f (red) · shade #f2b807 (mustard) · shade #d9c9a8 (placeholder); stains are radial gradients of rgba(242,107,29,.10) at 20% 15% and rgba(31,158,149,.10) at 85% 80%
- fonts: display Bricolage Grotesque 800 · body Caveat 700 (lines 92 px, ghost year 380 px, name labels Bricolage Grotesque 700 at 34 px with .14em tracking, handwriting 56 px)
- runtime: gsap
- motion: the whole scene is one `#world` layer with 1400 px of paper beyond the frame on every side, and the camera is a tween of `#world` with `transformOrigin: "0 0"`: `x = 960 - cx * z`, `y = 540 - cy * z`, `scale = z` (ours: upstream rewrites the same transform in `onUpdate`). `look(at, x, y, z, dur = 1.6)` is `sine.inOut`; `home(at, x = 960, y = 540, dur = 1.2)` goes back to z 1 with `power2.inOut`; `into(cutAt, x, y, z)` lasts .9 s `power2.in` and starts at `cutAt - .9`; `settle(cutAt, x, y, z)` lasts 1.1 s `power3.out` and ends at z x .94; `breath(a, b, z)` is `sine.inOut`, ±4 to 5%. `fly` starts from `{x:0, y:500, rotate:10, scale:.9}` and takes .9 s `power4.out`; upstream's directional blur 34 to 0 over .63 s becomes opacity 0 to 1 over the same .63 s. Then the object floats `y:-25, rotate:1.5, scale:1.03` for `1.5 + ((at * 7) % 1) * .3` s, `sine.inOut`, yoyo; a finite `repeat: Math.max(0, Math.floor(duration / cycle) - 1)` replaces upstream's `repeat:-1`. `flyOut` takes .45 s `power2.in` to `{y:-700, rotate:-8, scale:1.1}` with opacity 1 to 0 in place of blur 0 to 50. `say` lifts each word `yPercent 60 to 0`, `scaleY 1.25 to 1`, .55 s `power4.out`, stagger .08, with opacity 0 to 1 instead of blur 22 to 0; mode `scale` is scale .7 to 1 and rotate -3 to 0 with `back.out(1.6)`. The highlighter pill is `scaleX` 0 to 1 in .4 s `power3.out`, starting `at + stagger * n + .2 + i * .2`. `unsay` takes .3 s `power2.in`, stagger .02, `yPercent -50` and opacity 1 to 0. `draw` is a `clip-path` inset reveal in .7 s `power2.inOut`; `label` is y 14 to 0 in .4 s `power3.out`, `unlabel` takes .25 s. Scene pattern: born in a close-up of object 1 (z about 1.4, settling to 1.32), glide to object 2, zoom out to home as the title appears, hold still until the transition. The transition is a push-through of .9 s before the cut (`power2.in`); the new scene is born at that framing and settles with `power3.out`. Object 1 is in within .1 s of the cut, the zoom-out is 1.0 to 1.2 s and ends before the text starts (text at least .1 s after `home()`), a panorama pan takes 2.5 to 3 s at z 1.3 to 1.5. Cutouts are flat SVG shapes with a flat offset shadow shape (upstream's `drop-shadow()` is `0 30px 40px rgba(34,30,27,.30)`). Grain is a 256 px noise tile, drawn once on a canvas with `fx.rand`, as a repeating `background-image` at opacity .28 with `mix-blend-mode: multiply`; the vignette sits outside the world: radial, rgba(34,30,27,.18) at the edge. The ghost year is rgba(34,30,27,.07).
- rules: Every cutout is a flat SVG shape drawn with one outline weight and one style, never a photo. An object enters from below with overshoot (`back.out(1.4)`) and its shadow goes on the wrapper. Text is one `.wd` span per word; a phrase that must wrap is not one `nowrap` span. The highlighter scales in after the words. Each scene holds 3 to 5 elements that accrete with the voice. One ghost-year style per video. Text has 2 levels at most and nothing under 30 px at 1080; the screen shows the noun and the voice carries the sentence.
- avoid: One cutout and one sentence per scene, stacked scale tweens on the camera, text that starts with or before the zoom-out
- prompt: Style: cartoon collage. A cream paper #f4e9d3 with soft orange and teal stains and fine grain, flat SVG cutouts in orange #f26b1d, teal #1f9e95, red #d63b2f and mustard #f2b807, ink #221e1b. Cutouts fly in from below at a tilt in .9 s and then float 25 px; words rise one by one at .08 s apart and a coloured pill highlights the key word after them. The camera glides between objects at z 1.4 and returns home as the title appears, and each cut is a .9 s push-through. Every scene has 3 to 5 elements and a big ghost year behind them. Type: Bricolage Grotesque 800 for display, Caveat 700 for body.

## saas-ui-tour — Product tour with claims
- source: bang-motion (MIT, © 2026 Bang Tutorial), https://github.com/bangtutorial/bang-motion, README.md:53,117; bang-motion/references/opener-konsep.md:75,387-438,801; bang-motion/references/techniques.md:555-602
- group: explain
- fits: a UI feature, best with a demo file
- palette: ground #faf7f2 (warm white, about 40% of the time) · shade #eef3ff (pale brand tint, about 15%) · accent #2f5bea (brand: buttons, actions, claim field) · shade #14246b (darkest brand: the closing field) · ink #1b1f2a (ours; a source brand replaces them). The claim field is a gradient from #14246b at the bottom to #2f5bea, about 45% of the time (ours)
- fonts: display Manrope 600 · body Manrope 400 (ours)
- runtime: gsap
- motion: 10 to 11 beats of 2 to 5 s with only 1 or 2 cuts; the UI carries the rest. One energy hit at the start: upstream's hammer zoom with a strong radial blur for about .5 s becomes a `scale` push of 1 to 1.3 and back to the same composition in .5 s, with no blur (ours: the 1.3). Everything else is calm: ease in-out 0.8 to 1.2 s (`sine.inOut`, ours). Claim words rise one by one at .12 to .15 s apart (opacity 0 to 1 and y 24 to 0, ours, where upstream rises from blur), hold 1.5 to 2 s and leave by fading to 50% first, then to 0. The order is UI, claim, UI, claim, UI, claim, logo, never two claims in a row. A split screen is 50/50 or 55/45, text on the colour side and UI on the light side. UI comes in two sizes: the full-screen tour and a detached card 25 to 40% of the frame width (480 to 768 px). A diagram has the parent top-centre, 3 children aligned below and thin connector lines. Camera follow: scale 1.4 to 2.2, `power2.inOut`, .6 to .9 s, starting .3 to .5 s before the cursor arrives; `camTo(ui, target, at, {s: 1.8, dur: .8, fy: .45})` and `camWide(ui, at, dur: .9)` are `x`, `y` and `scale` tweens of the UI wrapper. A click is scale .92 to 1 and the cursor holds about .2 s. Bars fill in sequence, stagger about .08 s; typing is `fx.type`, and counters are two stacked spans with a `y` tween. Cards are white, rounded, with a wide soft `box-shadow` and no border line.
- rules: Rebuild the UI as simplified DOM or SVG parts; a demo file from the run (`public/demo-*`) may stand in for a screenshot. Use the product's own font and colours when the source has them. One screen is one task. Data is always alive: bars fill, progress moves, counters roll. Transitions are carried by the UI (a dimming, a card lifted out, a split), not by a cut. A claim is 1 or 2 lines of 2 to 4 words, with a line height of 65 to 86 px (6 to 8% of 1080); an intro line is 32 px (3%). Text never sits on the UI: it goes beside the object. 2 text levels at most, nothing under 30 px at 1080, and the claim is a noun phrase or a number that the voice does not say word for word.
- avoid: Zooming and panning a still screenshot, text stacked on the UI, two claims in a row
- prompt: Style: product tour with claims. The real interface, rebuilt in DOM, tours across a warm white #faf7f2 ground; every few seconds it stops and one short claim of 2 to 4 words stands on a brand field that runs from #14246b to #2f5bea, then the UI returns. The camera zooms 1.4 to 2.2x to what is clicked, .6 to .9 s, starting .3 s before the cursor arrives. Cards are white and rounded with a wide soft shadow, data is always moving, and the diagram has one parent over 3 children. One quick zoom hit at the start, calm everywhere else, and never two claims in a row. Type: Manrope 600 for display, Manrope 400 for body.

## claim-how-result — Claim, how, result
- source: bang-motion (MIT, © 2026 Bang Tutorial), https://github.com/bangtutorial/bang-motion, bang-motion/references/opener-konsep.md:71,158-202,793; README.md:113
- group: explain
- fits: a UI feature, best with a demo file
- palette: ground #f6f3ec (warm white, about 80%) · shade #fffdf8 (the brighter light at the centre) · shade #d6d6d3 (neutral grey, about 15%: UI and shadows) · ink #3b3b3d (dark grey text) · accent #e8590c (about 5%, only in the product's work output) (ours; a source brand replaces them)
- fonts: display IBM Plex Sans 500 · body IBM Plex Sans 400 (ours; the product's own UI font replaces it when the source has one)
- runtime: gsap
- motion: no cuts, calm, ease in-out .8 to 1.2 s (`sine.inOut`, ours). A cycle is claim 1 to 2.5 s, how 2 to 6 s, result 4 to 6 s, repeated 2 or 3 times, then a closing of 4 to 5 s. Claim words appear one by one from neutral grey to ink (a colour tween with opacity 0 to 1, where upstream goes from blurred grey to sharp dark); the sentence leaves by dimming to grey first. The UI floats with no device frame, rounded corners, a wide soft `box-shadow`, zoomed to about 80% of the frame width (1536 px). The result card peaks at 75 to 90% of the frame width and height, its content always moving; it then shrinks while its content keeps cropping in, to a pill and then a dot (`width`, `height` and `border-radius` tweens), and the next claim appears exactly at the dot. Closing: a quality claim, a site address typed with `fx.type`, the address erased by fading its character spans out in reverse order (ours), the product name typed and held 2 to 3 s, then a fade to the background. The cursor is large and moves on `power2.inOut`.
- rules: Show the client's UI as the product, or a demo file from the run (`public/demo-*`). Use this style only for a product whose result is coloured; otherwise pick another. Colour appears only in the product's work output; the logo and the UI are monochrome. The background has layers even when it is near white: warm white, a brighter radial light at the centre, and one hairline curve that sometimes crosses behind the text. Text is sentence case in dark grey, at most 2 lines, a line height of about 86 px (8% of 1080), a block 30 to 65% of the width (576 to 1248 px), and nothing under 30 px. The screen shows the claim's noun and the voice carries the sentence.
- avoid: Decoration, high colour, fast motion
- prompt: Style: claim, how, result. A calm feature announcement on warm white #f6f3ec with a brighter radial light at the centre, about 80% warm white, 15% neutral grey and 5% colour. A short claim fades from grey to dark word by word, the real UI floats at 80% of the frame width and a large cursor drives it, then a result card blooms to 75 to 90% of the frame and is the only coloured thing. The card shrinks to a pill and a dot, and the next claim appears at the dot. No cuts, ease in-out .8 to 1.2 s, no ornament. Type: IBM Plex Sans 500 for display, IBM Plex Sans 400 for body.

## grainy-gradient — Grainy gradient
- source: bang-motion (MIT, © 2026 Bang Tutorial), https://github.com/bangtutorial/bang-motion, README.md:49,90,116; bang-motion/references/techniques.md:481-530; bang-motion/references/opener-konsep.md:74,204-239,799
- group: graphic
- fits: an AI or infra launch with few words
- palette: ground #0b1026 (deep base, 60 to 70% of the area) · shade #2b59ff (blue) · shade #ff7a2f (orange) · accent #ffe9c7 (the light accent: only the guide orb and the portal core) · ink #f4f1ea (ours; a source brand replaces them). A shape's gradient is `radial-gradient(60% 60% at 50% 30%, <palette colour>, <half-way mix> 45%, #0b1026 100%)`
- fonts: display Sora 600 · body Sora 400
- runtime: gsap + hf-seek
- motion: calm, no cuts. Moves are ease in-out 1 to 2 s; the camera enters each layer in .8 to 1.2 s, and the peak is the pass through the portal. The `hf-seek` listener writes the layers' rotation from `t` at 10 to 20 deg per second, each layer in its own direction, and the grain jump. Layers are 80 to 120% of the frame height (864 to 1296 px), cropped by the edges, with the centre a little above or below the middle. The guide orb is 3 to 6% of the frame height (32 to 65 px) and is the only sharp, fast-moving object. Beats: a dark frame with one light dot, blooming into rotating gradient layers (petals, rings, arcs), the orb bouncing in, the camera following it through thin layers like a tunnel, small shapes orbiting, the portal opening on a glowing symbol, the camera entering the hole into the dark. Text is very little: small beside the object, or none until the logo. Grain: a 256 px monochrome noise tile drawn once on a canvas with `fx.rand` (it registers `window.__hf.buildReady["grainy-gradient"]`) and used as a repeating `background-image` of a layer `inset: -60px` with `mix-blend-mode: overlay` at opacity .22 (upstream draws it with an SVG filter, dropped); on a dark ground overlay or soft-light at .15 to .3, on a light ground `multiply` at .08 to .15. The grain layer jumps 12 times per second (every 2 or 3 f): with `k = floor(t * 12)`, translate `(k * 37 % 60 - 30)` px, `(k * 61 % 60 - 30)` px.
- rules: The gradient sits on the shapes (circle, arc, hole, petal, concentric layer): edges sharp, interior soft. Fine monochrome grain covers the whole frame, background and objects, at the same strength on light and dark; it is not big specks or dust, and it also dithers the gradient against banding. The palette is 2 or 3 colours far apart over a deep base. The light accent appears only on the orb and the portal core. Small text sits above the grain layer so the letters stay clean; the text pocket still passes a contrast check, and nothing is under 30 px at 1080. The grain is a skin, not a skeleton: the structure and transitions come from the digest.
- avoid: Banding, big grain, treating it as a structure, a second light accent
- prompt: Style: grainy gradient. A deep base #0b1026 covers about 65% of the frame; layered shapes glow from blue #2b59ff against orange #ff7a2f, sharp at the edge and soft inside, 80 to 120% of the frame height and turning 10 to 20 degrees per second. A fine monochrome grain covers everything and jumps 12 times per second. One small light orb in #ffe9c7 leads the camera through the layers, .8 to 1.2 s per layer, to a portal. No cuts, ease in-out, and almost no text. Type: Sora 600 for display, Sora 400 for body.

## Not used, and why

`social` is 9:16, while spec-reel renders 1920x1080 only (`qc_video.py`). The user chose to skip it on 2026-11-09.

`toy3d` and `tape`: both need WebGL, which always forces screenshot capture (`webgl-context detected`), about twice the render time. Dropped by the user on 2026-11-09.

bang-motion entries left out (the 7 taken are in the catalog above):

- `visual-journalism`, `vintage-sketch` and `flat-pop-photo` need real or generated photos, and spec-reel has no photo pipeline.
- `editorial-light`, `paper-and-print`, `retro-analog`, `brutalist-mono`, `pastel-playful`, `luxury-dark` and `poster-color-block`: upstream gives no numbers for them, and `swiss`, `print`, `hud`, `dark-keynote` and `flat-vector` cover them.
- `cinematic-dark` is WebGL.
- `kinetic-typography` puts the narrator's sentence on screen.
- `living-ui-ecosystem` is music-driven with no voice-over, and its UI moves are covered by `screencast` and `saas-ui-tour`.
- `flat-vector` is already in the catalog.
- `bumper-ident`, `opener-concepts-1-13`, `render-families` and `video-footage-layer` are structures and techniques, not looks.

## Default avoid list

Particle bursts, lens flares, neon glow, RGB split, glitch, bouncy easing on everything, decorative gradients, and text that repeats what the picture shows.

## Picking three

Gate 3 picks three styles from this page by these rules, in this order.

1. **Three groups.** The three styles come from three different `group` values (`graphic`, `explain`, `drawn`, `retro`, `dimensional`).
2. **Recent styles.** A style named in the `STYLE:` line of any of the last three runs' `SPEC.md` is not picked. When that leaves fewer than three groups, drop exclusions oldest first until three groups are available. The gate never fails for this.
3. **Recommendation.** The recommended look is the style whose `fits` best matches the approved digest. It goes first, with a one-clause reason.

Worked example of rule 2. Take a catalog trimmed to four styles: `swiss` and `morph` (graphic), `dataviz` (explain), `print` (drawn). The last three runs used, newest first, `dataviz`, `print`, `swiss`. That excludes all of explain and drawn and one of graphic, leaving `morph`: one group. Drop the oldest exclusion, `swiss`: still only graphic. Drop the next oldest, `print`: graphic and drawn, two groups. Drop `dataviz`: three groups, so the pick is `swiss` or `morph`, `dataviz` and `print`. With the 21 styles above this cannot happen yet: taking away three groups needs at least 7 excluded styles, and three runs name at most 3. The rule stays for a smaller catalog.
