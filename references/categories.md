# Video categories

A category is the kind of video a run makes: it sets the script's arc, the job of each scene, the digest's headings, the narrator's tone and the looks gate 3 prefers. The user picks one at gate 1 (`SKILL.md` § Digest), and the run records it as `category:` in `RUN.md`. The job lists below live in `scripts/adopt_voice.py` (`CATEGORY_JOBS`), where `--check-script` enforces them; a test keeps the `jobs` lines here equal to that code. A run with no `category:` line is a legacy run and keeps the older jobs (`why`, `change`, `proof`, `next`).

What does not change with the category: the sources, the digest as the only source of facts, status tags and tense, plain A2 English, the 20-word intro, 30 spoken words per scene, the banned patterns in `references/style.md`, the shape list and the no-repeat shape rule, the claim check, voices and discussion mode (both speakers follow the category's line rule), `finish.py` and QC.

## A · Concept Map

- intent: How a system or change works
- for: code architecture, feature overviews, workflows and pull-request reviews.
- arc: Question → Mechanism → (Change) → Edge case → What to remember
- jobs: `question` (required), `mechanism` (required), `change` needs `before` and `after`, `edge`, `remember` (required)
- line rule: every line names a part and what it does to another part ("the queue retries the upload").
- screen: a diagram that grows; every arrow carries a verb; a number gets a picture (a bar, a dimension line), not only digits.
- delivery: precise, steady.
- digest: headings **The question**, **How it works**, **What to remember**. The tagged points go under **How it works**, in today's forms ("You can now ...", or "You will be able to ..." for `[planned]`). **The question** states the problem the viewer arrives with as a fact; **What to remember** holds one concrete fact or action.
- demo: a `mechanism` or `change` frame.
- instruct: "Precise, steady engineer explaining a system: even pace, clear stress on the names of parts."
- looks: `line-draw`, `isometric`, `hud`, `continuous-action`, `white-catalog`, `swiss`
- rules: one claim per scene, and draw the mechanism rather than its name. A `change` frame (a PR or a diff) needs `before` and `after`. The `question` frame states the problem as a fact ("A failed upload had to be restarted by hand"), never as a question the next sentence answers; the last frame answers it in one line. `remember` ends on one concrete fact or action, never on a summary or a moral. Cases are drawn side by side as small multiples.
- source: nicobailon/visual-explainer (MIT, © 2025 Nico Bailon), https://github.com/nicobailon/visual-explainer

## B · Analogous Storyboard

- intent: A new idea, for newcomers
- for: onboarding, topic summaries and non-technical viewers.
- arc: Why you care → The everyday picture → How it maps → Takeaway
- jobs: `why` (required), `picture` (required), `mapping` (required) needs `picture` and `real`, `takeaway` (required)
- line rule: each line is in the picture's world or in the real system's; a `mapping` line links one part of the picture to one real part.
- screen: scenes and simple characters, almost no on-screen text.
- delivery: warm, unhurried.
- digest: headings **Why you care**, **What it is**, **What comes next**. The tagged points go under **What it is**, in today's forms ("You can now ...", or "You will be able to ..." for `[planned]`).
- demo: a `mapping` frame.
- instruct: "Warm, unhurried teacher talking to a newcomer: friendly, patient, short gentle pauses."
- looks: `cartoon-stage`, `cartoon-collage`, `flat-vector`, `papercut`, `painterly`, `cel`
- rules: choose the everyday picture once per video (a toll booth for a firewall). Every `mapping` frame needs `- picture:` (the part of the picture) and `- real:` (the digest's name for the real part). The video says once where the picture stops matching the real thing; the agent checks this, code does not. The picture adds no claim: anything it implies about the real system must be a digest point, or that part is drawn outside the picture. Ground everything in why this viewer cares, use at most 3 new terms in the video, give one tangible takeaway, and use one name per concept from start to end. Drawn scenes still name the shape of their information (a toll booth sorting cars is `chosen`; cars flowing through gates is `steps`). `takeaway` ends on one concrete fact or action, never on a summary or a moral. No raster characters or generated images: `cartoon-stage` uses its vector heads.
- source: mattpocock/skills teach (MIT, © 2026 Matt Pocock), https://github.com/mattpocock/skills/tree/main/skills/productivity/teach; the picture-and-mapping method is spec-reel's own

## C · Analytical Report

- intent: Where the numbers stand
- for: executive summaries, metrics and status updates.
- arc: Progress → Plans → Problems
- jobs: `progress` (required) needs `number`, `plans` (required), `problems`
- line rule: every line carries a number or a status from the digest.
- screen: one number or one chart per scene, never a bullet list. Keep shapes varied among `number`, `before-after`, `chosen`, `steps` and `converge`, with only one big number per scene.
- delivery: formal, even.
- digest: headings **Progress**, **Plans**, **Problems**, and every point under all three carries a status tag. Line forms: Progress `<what>: <number or status> [shipped|in progress]`; Plans `<what> [planned|in progress]`; Problems `Blocked: <what> by <cause> [in progress]`.
- demo: a `progress` frame.
- instruct: "Formal, even analyst briefing leadership: measured and articulate, every number said clearly."
- looks: `dataviz`, `dark-keynote`, `swiss`, `claim-how-result`, `saas-ui-tour`
- rules: number first: every `progress` frame needs `- number:`, a number or status taken word for word from the digest, and each section leads with its number. State problems plainly: what is blocked and by what. A run with no problem is valid, so `problems` is optional. Readable in under a minute per section. No emoji header and no team or date header: `references/style.md` bans emoji in the caption, and this skill has no use for the header.
- source: anthropics/skills internal-comms 3P updates (Apache-2.0, © 2026 Anthropic, PBC), https://github.com/anthropics/skills/tree/main/skills/internal-comms; adapted, wording rewritten

## Voice and tone

Each category's `instruct` is passed to Qwen3-TTS (`references/handoff.md` § Qwen3-TTS) when config `qwen_instruct` is empty; a `qwen_instruct` the user set always wins. A cloned voice and the user's own engine take no instruct, so they sound the same in every category. The script's `**Delivery:**` line stays a note for the writer, and its default is the category's `delivery`.

## Suggesting a category

The agent judges this from the digest and the run answers; no script decides it. Mostly components, flows and mechanisms: A. An audience the run answers call new, non-technical or onboarding: B. Mostly metrics and statuses: C. A tie goes to A. The suggestion is shown with one clause on why, beside the three intents. An invocation that names a category (`--category A|B|C`, or plain words such as "for onboarding" or "exec summary") skips the suggestion and shows that category as chosen.
