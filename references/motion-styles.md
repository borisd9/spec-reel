# Motion styles

Styles adapted from Awesome Claude (https://awesomeclaude.ai/claude-motion-graphics, github.com/webfuse-com/awesome-claude, CC0-1.0; site footer says MIT).

Gate 3 (`SKILL.md` § Look (gate 3)) builds each of its three looks from one style on this page. A style is numbers: a palette, bundled fonts, a runtime, eases, timings, rules, an avoid list and a style prompt. A look copies them and changes only what `## Picking three` allows.

Conventions:

- Output is 1920x1080 at 30 fps. Frame counts are written as `N f (S s)` at 30 fps.
- `runtime: gsap`: every effect is a GSAP `fromTo` of DOM or SVG elements. No CSS filters, no `onUpdate:`. A counter is a strip of digit elements moved with `y`, not a tween that rewrites text.
- `runtime: hf-seek`: a `<canvas>` drawn from `e.detail.time` in an `hf-seek` listener (`<hyperframes dir>/references/runtimes.md`, `<hyperframes dir>/references/types/3d.md`). `render(t)` is a pure function of `t`. Anything simulated is computed once at load into arrays. Heavy setup registers `window.__hf.buildReady["<style id>"]`. Seed every random choice with `fx.rand(seed)`; never `Math.random()`.
- Three.js is `https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js`.
- Cubic-bezier eases load as `CustomEase` (`https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/CustomEase.min.js`, already in `assets/index.template.html`): `CustomEase.create("snap", "M0,0 C0.7,0 0.2,1 1,1")`.
- Rates that are not 30 fps: on twos at 24 fps draws `floor(t * 12)`. 12 fps steps are `fx.stepped(d)` in `gsap` and `floor(t * 12)` in `hf-seek`.
- Fonts are only the bundled families (`SKILL.md` § Look (gate 3)). Inter, Space Grotesk and JetBrains Mono are never the display face.

## swiss — Swiss grid & kinetic type
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
- group: graphic
- fits: topic-to-topic stories, a concept that turns into another, brand narratives
- palette: ground #0d1b2a · accent #f72585 · shade #7209b7 · shade #4cc9f0
- fonts: display League Gothic 400 · body Lato 400
- runtime: gsap + hf-seek
- motion: SVG morphs are `fromTo` tweens of paths with the same number of points, 18 to 30 f (0.6 to 1.0 s) each, through a readable in-between shape. Hold every finished shape at least 30 f (1.0 s). Liquid moments are a canvas of metaballs drawn from `e.detail.time` in `hf-seek` with smooth-min blending, the ball paths computed once at load. No cuts, and the camera stays still.
- rules: There are no cuts. Every new idea grows out of the previous shape. Each morph takes 18 to 30 frames and passes through a readable in-between shape. Hold each finished shape at least 1 second so it reads. Liquid joins use smooth-min blending, never a hard overlap.
- avoid: Morphs that pass through a shapeless blob, constant motion with no holds
- prompt: Style: continuous shape morph. Dark #0d1b2a field, shapes in #f72585, #7209b7, #4cc9f0. No cuts: each idea grows out of the previous shape through a readable in-between form over 18 to 30 frames, then holds for at least 1 second. Liquid moments use metaball blending so drops merge smoothly. Camera stays still; the shapes do the moving. Type: League Gothic 400 for display, Lato 400 for body.

## line-draw — Single line & live drawing
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
- group: drawn
- fits: stories, places, culture and people topics, soft explainers with little text
- palette: ground #f4efe6 · ink #2f3e46 · accent #bc4749 · shade #6a994e · shade #a7c4d2
- fonts: display EB Garamond 500 · body Lato 400
- runtime: hf-seek
- motion: a plain Canvas 2D brush engine (strokes with a width profile, no p5). Washes spread over 15 to 25 f (0.5 to 0.83 s) and bleed 4 to 8 px past the ink line. Linework is re-seeded 12 times a second: seed = `floor(t * 12)` into `fx.rand`, so it wobbles on twos without flicker. The paper grain is drawn once from a fixed seed. Pure white and pure black never appear.
- rules: Everything is painted with strokes. No plain vector shapes. Washes reveal over 15 to 25 frames and bleed 4 to 8px past the ink line. Paper texture is always visible; pure white and pure black never appear. Linework re-randomises 12 times a second from a seed, so it lives without flickering.
- avoid: Perfect geometric shapes, digital gradients, text labels on everything
- prompt: Style: watercolour and ink on paper. Warm paper #f4efe6 with visible grain, ink #2f3e46, washes in #bc4749, #6a994e, #a7c4d2. Paint every element with brush strokes, never plain shapes. Washes spread over 15 to 25 frames and bleed slightly past the ink. Linework wobbles on twos (re-seeded 12 times per second from a fixed seed). No pure white, no pure black, very little text. Type: EB Garamond 500 for display, Lato 400 for body.

## print — Risograph & halftone print
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
- group: drawn
- fits: playful explainers, diagrams, arrows and icons that feel drawn by hand
- palette: ground #fffaf0 · ink #1c1c1c · accent #ff595e · shade #1982c4 · shade #ffca3a
- fonts: display Outfit 800 · body Nunito 600
- runtime: hf-seek
- motion: Canvas 2D variable-width strokes, on twos at 24 fps: the drawing index is `floor(t * 12)`. Three jitter variants of every line, variant = `floor(t * 12) % 3`, each from a fixed `fx.rand` seed, so lines boil without strobing. A fast move gets one smear frame (the shape stretched along its path for one drawing) instead of motion blur. Anticipation before every big action: a small move the other way for 4 to 6 f (0.13 to 0.2 s).
- rules: Animate on twos: the drawing changes every 2 frames at 24fps. Cycle 3 jitter variants of every line so it boils without strobing. Fast moves get a smear frame instead of motion blur. Anticipation before every big action: a small move the other way for 4 to 6 frames.
- avoid: Tweened vector motion at 60fps, perfect circles, text standing in for acting
- prompt: Style: hand-drawn cartoon with line boil. Off-white #fffaf0, ink #1c1c1c, flat fills #ff595e, #1982c4, #ffca3a. 24fps animated on twos. Every line has 3 jitter variants cycled so it boils. Fast moves use a smear frame, every big action gets 4 to 6 frames of anticipation, faces act. Variable-width ink lines, no perfect geometric shapes, almost no text. Type: Outfit 800 for display, Nunito 600 for body. No characters unless a source has one: the linework boils on diagrams, arrows and icons.

## pixel — Pixel art & retro game
- group: retro
- fits: nostalgia and game-like stories, year in review, step-by-step levels
- palette: ground #1a1c2c · shade #5d275d · shade #b13e53 · accent #ef7d57 · shade #ffcd75 · shade #a7f070 · shade #38b764 · shade #41a6f6
- fonts: display Space Mono 700 · body Space Mono 400
- runtime: hf-seek
- motion: draw on a 320x180 canvas and scale it 6x to 1920x1080 with `imageSmoothingEnabled = false`. Sprites animate at 8 to 12 fps: frame = `floor(t * 12)` or `floor(t * 8)`. The camera moves in whole pixels (`Math.round`). Shading is dithering. Text is Space Mono drawn with `fillText` on the small canvas, typed out in a bordered box one character per beat. Text may look soft; the fix is a 5x7 bitmap font table.
- rules: Draw at 320x180 and scale by 6 with image smoothing off. Never draw at full resolution. One fixed palette of 16 to 32 colours. Shading uses dithering, not blending. Sprites animate at 8 to 12fps; the camera snaps to whole pixels. Text uses a pixel font and types out in dialogue boxes.
- avoid: Mixed pixel sizes, blurry scaling, anti-aliased edges, smooth sub-pixel motion
- prompt: Style: 16-bit pixel art. Render to a 320x180 canvas and scale 6x with imageSmoothingEnabled = false. Use one fixed palette (#1a1c2c, #5d275d, #b13e53, #ef7d57, #ffcd75, #a7f070, #38b764, #41a6f6 plus greys). Shading by dithering only. Sprites animate at 8 to 12fps, camera moves in whole pixels, dialogue in a pixel font that types out in a bordered box. Type: Space Mono 700 for display, Space Mono 400 for body.

## tape — VHS, film & CRT eras
- group: retro
- fits: throwback and teaser pieces, mood over data, a title with one clear message
- palette: ground #120f1d · accent #ff3fa4 · shade #00e5ff · shade #ffd166
- fonts: display Archivo Black 400 · body Space Mono 400
- runtime: hf-seek
- motion: one era per video: 1920s film, 1980s VHS or 1990s camcorder. A clear composition drawn on a canvas, then a post pass drawn over it. Grain is seeded by frame index: `fx.rand(Math.round(t * 30))`. Film: gate weave of about 1 px and brightness flicker of about 5%. Tape: chroma shift of 2 to 3 px, scanlines, an occasional tracking line. The effect never covers key text.
- rules: Pick one era and commit: 1920s film, 1980s VHS, or 1990s camcorder. Texture is seeded per frame index, so grain changes every frame but renders the same every time. Gate weave of about 1px and brightness flicker of about 5% for film. Chroma shift of 2 to 3px for tape. Keep it legible: the effect sits on top of a clear composition, it is not the composition.
- avoid: Stacking every retro effect at once, glitch tearing over important text
- prompt: Style: 1980s VHS tape. Scene in deep #120f1d with neon accents #ff3fa4, #00e5ff and warm #ffd166. Post pass: scanlines, 2 to 3px chroma shift, slight tape noise and an occasional tracking line, all seeded by frame index so the render is deterministic. A chrome title moment. Keep the composition clear underneath; the tape texture never covers key text. Type: Archivo Black 400 for display, Space Mono 400 for body.

## toy3d — Toy & material 3D
- group: dimensional
- fits: a product or object as the hero, friendly explainers, brand idents
- palette: ground #f6e6e4 · accent #ff8fab · shade #7bdff2 · shade #b2f7ef · shade #fcbf49
- fonts: display Nunito 800 · body Nunito 600
- runtime: hf-seek
- motion: Three.js (pinned above), drawn from `e.detail.time`, with `buildReady` for the setup. Soft studio light: one large key and a fill. Matte or soft-gloss materials. Shallow depth of field on the hero object. An object lands fast with 2 small settles, computed as a closed-form function of `t`, always with a contact shadow. Every procedural shape uses a fixed `fx.rand` seed.
- rules: Soft studio light from one big key and a fill. Matte or soft-gloss materials. Shallow depth of field keeps attention on one object. Objects arrive with weight: fast in, 2 small settles, no floating. Fixed random seed for every procedural shape.
- avoid: Chrome everything, hard black shadows, objects floating with no contact shadow
- prompt: Style: toy-like 3D. Three.js, soft studio lighting with one large key and a fill, pastel background #f6e6e4, matte and soft-gloss materials in #ff8fab, #7bdff2, #b2f7ef, #fcbf49. Shallow depth of field on the hero object. Objects land with weight and two small settles, always with a contact shadow. Fixed seeds for any procedural geometry. Type: Nunito 800 for display, Nunito 600 for body.

## Not used, and why

`social` is 9:16, while spec-reel renders 1920x1080 only (`qc_video.py`). The user chose to skip it on 2026-11-09.

## Default avoid list

Particle bursts, lens flares, neon glow, RGB split, glitch, bouncy easing on everything, decorative gradients, and text that repeats what the picture shows.

## Picking three

Gate 3 picks three styles from this page by these rules, in this order.

1. **Three groups.** The three styles come from three different `group` values (`graphic`, `explain`, `drawn`, `retro`, `dimensional`).
2. **Recent styles.** A style named in the `STYLE:` line of any of the last three runs' `SPEC.md` is not picked. When that leaves fewer than three groups, drop exclusions oldest first until three groups are available. The gate never fails for this.
3. **Recommendation.** The recommended look is the style whose `fits` best matches the approved digest. It goes first, with a one-clause reason.

Worked example of rule 2. Take a catalog trimmed to four styles: `swiss` and `morph` (graphic), `dataviz` (explain), `print` (drawn). The last three runs used, newest first, `dataviz`, `print`, `swiss`. That excludes all of explain and drawn and one of graphic, leaving `morph`: one group. Drop the oldest exclusion, `swiss`: still only graphic. Drop the next oldest, `print`: graphic and drawn, two groups. Drop `dataviz`: three groups, so the pick is `swiss` or `morph`, `dataviz` and `print`. With the 16 styles above this cannot happen yet: taking away three groups needs at least 7 excluded styles, and three runs name at most 3. The rule stays for a smaller catalog.
