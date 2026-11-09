# Video categories: a script framework picked per run

Date: 2026-11-09. Status: design, waiting for the user's approval.

## Why

spec-reel writes every script along one arc: `Intro → Why → Change → Proof → Next`. That arc fits a team update, and it fits poorly when the same sources need to explain how a system works, teach a newcomer, or report numbers to leadership. The user wants a better framework for writing the script and its explanations: three categories, each with a clear intent. The skill suggests one, and the user can pick another. The change is to the script and the look. The voice changes only through its existing `**Delivery:**` line.

## The three categories

The user named them and gave each its intent. The arcs, line rules and job lists below are the agreed proposal from the conversation.

| | A · Concept Map | B · Analogous Storyboard | C · Analytical Report |
|---|---|---|---|
| Intent, as shown in the picker | How a system or change works | A new idea, for newcomers | Where the numbers stand |
| For | code architecture, feature overviews, workflows, PR reviews | onboarding, topic summaries, non-technical viewers | executive summaries, metrics, status updates |
| Arc | Question → Mechanism → (Change) → Edge case → What to remember | Why you care → The everyday picture → How it maps → Takeaway | Progress → Plans → Problems |
| `scene_job` values | `question`, `mechanism`, `change`, `edge`, `remember` | `why`, `picture`, `mapping`, `takeaway` | `progress`, `plans`, `problems` |
| Line rule | Every line names a part and what it does to another part ("the queue *retries* the upload") | Each line is in the picture's world or the real system's; a `mapping` line links one picture part to one real part | Every line carries a number or a status from the digest |
| Screen | a diagram that grows; every arrow carries a verb; a number gets a picture (a bar, a dimension line), not just digits | scenes and simple characters, almost no on-screen text | one number or one chart per scene; never a bullet list |
| Delivery line default | precise, steady | warm, unhurried | formal, even |
| Digest headings (gate 1) | **The question** · **How it works** · **What to remember** | **Why you care** · **What it is** · **What comes next** | **Progress** · **Plans** · **Problems** |
| Looks gate 3 prefers | `line-draw`, `isometric`, `hud`, `continuous-action`, `white-catalog`, `swiss` | `cartoon-stage`, `cartoon-collage`, `flat-vector`, `papercut`, `painterly`, `cel` | `dataviz`, `dark-keynote`, `swiss`, `claim-how-result`, `saas-ui-tour` |

### Rules per category

- **A.** A `change` frame (a PR or a diff) needs `before` and `after`, as today. The arc's question is the one the viewer arrives with ("How does a failed upload get retried?"), and the last frame answers it in one line. Adapted from visual-explainer's "Show, don't tell" rules: one claim per scene, draw the mechanism rather than its name, a verb on every arrow, every number gets a picture, and cases as small multiples.
- **B.**
  - **The everyday picture.** It is chosen once per video, for example a toll booth for a firewall.
  - **Mapping frames.** Every `mapping` frame needs `- picture:` (the part of the picture) and `- real:` (the digest's name for the real part).
  - **Where it stops matching.** The video says once where the picture stops matching the real thing. This is a style rule: the agent checks it and code does not.
  - **No claims from the picture.** The picture adds no claim: anything it implies about the real system must be a digest point, or that part is drawn out of the picture.
  - **Teaching rules.** Adapted from mattpocock/skills `teach`: ground everything in why this viewer cares (its "mission"); stay within working memory, at most 3 new terms per video; one tangible takeaway; one name per concept across the whole video (its glossary rule).
  - **Our own part.** teach has no metaphor or character method. B's picture-and-mapping method is ours.
- **C.**
  - **Number first.** Every `progress` frame needs `- number:`, a number or status taken word for word from the digest. Each section leads with its number.
  - **Tags.** Every digest point carries a status tag (`[shipped]`, `[in progress]`, `[planned]`).
  - **Problems.** Problems are stated plainly: what is blocked and by what.
  - **Source.** Adapted from anthropics/skills `internal-comms` 3P updates: Progress, Plans, Problems; data-driven; metrics where possible; readable in under a minute per section.
  - **Not adapted.** The 3P update's emoji header, because `style.md` bans emoji in the caption, and spec-reel has no use for its team and date header.

### What stays the same for every category

Sources; the digest as the only source of facts; status tags and tense; plain A2 English; the 20-word intro; 30 spoken words per scene; the banned patterns in `references/style.md`; facts; the claim check; voices and discussion mode; gate 3 (now preferring the category's looks); `finish.py`; QC. Discussion mode works with any category, and both speakers follow its line rule.

## The picker (gate 1)

- **When.** It appears after the sources are read, beside the digest, because the suggestion needs the sources and the digest's headings depend on the category.
- **What it shows.** First the suggested category with one clause on why, then the three options, each with its intent line from the table.
- **Choosing.**
  - Keeping the suggestion needs no extra step.
  - Picking another category re-heads the digest under that category's headings and shows it again.
  - Gate 1 approves the digest and the category together.
- **How the suggestion is made.** The agent judges this from the digest and the run answers; no script decides it.
  - Mostly components, flows and mechanisms: A.
  - An audience the run answers call new, non-technical or onboarding: B.
  - Mostly metrics and statuses: C.
  - A tie goes to A.
- **Pre-picking.** An invocation that names a category (`--category A|B|C`, or plain words such as "for onboarding" or "exec summary") skips the suggestion, and the picker shows that category as chosen.
- **Yolo.** Yolo takes the suggestion, or the invocation's category, and lists it under **Decided without you**.
- **`RUN.md`.** It gains `- category: A | B | C` under `## Answers`. A run folder without `category:`, made before this change, keeps the old jobs (`why`, `change`, `proof`, `next`) and the old digest headings, so a resume of an old run still works.
- **Resume.** A changed category re-opens gate 1, then gate 2, because the arc and the digest headings depend on it.

## Gate 3 and the category

`references/motion-styles.md` § Picking three gains a rule ahead of the others: the recommended look comes from the category's preferred list (table above). The other two also come from that list where the three-groups rule and the recent-styles rule allow; otherwise they come from any style. The recommendation's one-clause reason names the category.

## Goals

1. The user can see the three categories and their intents at gate 1, with a suggestion and the reason for it.
2. The script for each category follows its arc and its line rule, and `adopt_voice.py --check-script` enforces each category's job list and required fields.
3. Gate 3 recommends looks that suit the category.
4. The sources the categories adapt are credited, and their licenses are honoured.

## Non-goals

- No music. `music: none` stays.
- Nothing interactive: the output is still an MP4.
- No new voice engine or voices.
  - **The tone changes per category** (the user's decision, 2026-11-09). When config `qwen_instruct` is empty, the voicing step passes the category's instruct to `qwen_voice.py --instruct`. A `qwen_instruct` the user set always wins.
  - **The instructs.** They are written once, in `references/categories.md`:
    - A: "Precise, steady engineer explaining a system: even pace, clear stress on the names of parts."
    - B: "Warm, unhurried teacher talking to a newcomer: friendly, patient, short gentle pauses."
    - C: "Formal, even analyst briefing leadership: measured and articulate, every number said clearly."
  - **Clone and own engine.** The cloned voice and the user's own engine take no instruct, so they sound the same in every category. The docs say so.
  - **No code change.** This needs no change to `qwen_voice.py`: `references/handoff.md` § Qwen3-TTS says which `--instruct` to pass, and a resume rebuilds it from `category:` in `RUN.md`.
  - **The Delivery line.** The script's `**Delivery:**` line stays a note for the writer, and its default matches the category's instruct.
- No bullet overlays and no on-screen sentence that repeats the voice; that rule holds for C too.
- No raster characters or generated images for B: `cartoon-stage` uses its vector heads.
- No category beyond these three in this change.

## Anti-goals (this fails even if it works)

- The three categories end up as one arc with three sets of labels.
- B's picture makes a claim no source makes.
- C turns into a slide of bullets.
- The picker adds a question to a run that has nothing to ask, where the suggestion is plainly right. Keeping it must cost nothing extra at gate 1.

## Constraints

- **One owner per fact.**
  - The job lists and required fields live in code, as `CATEGORY_JOBS` in `scripts/adopt_voice.py`.
  - Everything else per category lives in one new reference, `references/categories.md`: intents, arcs, line rules, digest headings, delivery defaults, preferred looks and the suggestion rule.
  - `SKILL.md`, `handoff.md`, `style.md`, `yolo.md` and `motion-styles.md` point to it rather than repeat it.
  - A structure test pins the doc's job lists to `CATEGORY_JOBS`.
- **Code.**
  - Standard-library Python only, with existing patterns: `CARD_RE`, `scene_cards` and `check_script`.
  - `CARD_RE` gains `picture`, `real` and `number`.
  - `check_script` reads `category:` from `RUN.md` (absent means the legacy list) and checks the frames against that category's list. The intro and the Demo frames are skipped as today.
- **Rule that moves.** `style.md` § Name what you explain and `handoff.md`'s claim-check line both talk about the `next` frame. That rule applies to the category's last job (`remember`, `takeaway` or `plans`) and to the legacy `next`.
- **Licenses.** All three sources are permissive, and each gets a section in `THIRD_PARTY_NOTICES.md`, the file added for bang-motion.
  - **nicobailon/visual-explainer:** MIT, `Copyright (c) 2025 Nico Bailon`. Its section holds the full MIT text.
  - **mattpocock/skills:** MIT, `Copyright (c) 2026 Matt Pocock`. Its section holds the full MIT text.
  - **anthropics/skills `internal-comms`:** Apache-2.0, `Copyright 2026 Anthropic, PBC`. Its section holds the full Apache-2.0 license text, copied from `skills/internal-comms/LICENSE.txt`, plus a line stating the change: "Adapted: the 3P update structure (Progress, Plans, Problems) became category C's arc and digest headings; wording rewritten."
  - **No NOTICE file.** The repo has none for that skill, so there is no NOTICE text to carry.
  - **What is adapted.** Only ideas and short rules are adapted, in our own words. No upstream file is copied.
  - **Credit lines.** `references/categories.md` names its source in each category's section, and the README credits all three.
- **Tests.** The whole suite passes: `cd scripts && python3 -I -m unittest discover -s . -p 'test_*.py'`. Every new check gets a test that fails without it.

## Files that change

| File | Change |
|---|---|
| `references/categories.md` | New: the three categories, per the tables and rules above, each with its source credit |
| `SKILL.md` | § Digest (gate 1): the picker, the category's digest headings, the `category:` answer and its resume rule. § Script (gate 2): the arc and line rule come from `references/categories.md`, plus the Delivery default. `--category` in `argument-hint` |
| `references/handoff.md` | § Qwen3-TTS: the category's `--instruct` when config `qwen_instruct` is empty. `STORYBOARD.md`: `arc:` follows the category; scene cards use the category's jobs and fields; the claim-check line for the last job |
| `references/style.md` | § Name what you explain names the category's last job |
| `references/yolo.md` | A gate 1 row for the category: take the suggestion or the invocation's category |
| `references/motion-styles.md` | § Picking three: the category's preferred looks come first |
| `scripts/adopt_voice.py` | `CATEGORY_JOBS`, `CARD_RE` fields, reading `category:` from `RUN.md`, the per-category checks |
| `scripts/test_adopt_voice.py`, `scripts/test_skill_structure.py` | Tests for each category's jobs and required fields, the legacy fallback, and the doc pinned to code |
| `THIRD_PARTY_NOTICES.md`, `README.md` | The three new credits; one README paragraph on the categories |

## Calls made after the builder check (mine, not yet confirmed by the user)

1. **Shapes.**
   - The `shape` list and the "no two frames in a row share a shape" rule stay the same for every category.
   - C keeps variety by picking among `number`, `before-after`, `chosen`, `steps` and `converge`. Only one of those per scene is a big number.
   - B's drawn scenes still name the shape of their information. For example, a toll-booth scene that sorts cars is `chosen`, and a flow of cars through gates is `steps`.
2. **Banned patterns** in `references/style.md` hold for every category, with no exceptions. The arcs are written to avoid them:
   - A's `question` frame states the problem as a fact ("A failed upload had to be restarted by hand"), never as a question that the next sentence answers.
   - A's `remember` and B's `takeaway` end on one concrete fact or action, never on a summary or a moral.
3. **What `--check-script` enforces about the arc.** Jobs must appear in arc order. A job may repeat, and frames with the same job sit next to each other.
   - **A:** `question`, `mechanism` and `remember` are required; `change` and `edge` are optional.
   - **B:** `why`, `picture`, at least one `mapping`, and `takeaway` are required.
   - **C:** `progress` and `plans` are required; `problems` is optional, because no problem is a valid state.
   - `CATEGORY_JOBS` therefore records, per category, the jobs in order, whether each one is required, and the fields each job needs.
4. **Required fields** are checked for presence only: `picture:` and `real:` on B's `mapping` frames, `before:` and `after:` on A's `change` frames, and `number:` on C's `progress` frames only. Matching them against the digest stays with the claim check.
5. **Digest layout.** It keeps one section per source, with the category's three headings in each.
   - **Where the tagged points go:** under A's **How it works**, B's **What it is**, and all three of C's headings.
   - **A and B line forms:** the tagged points keep today's forms ("You can now …", or "You will be able to …" for `[planned]`).
   - **C line forms:**
     - Progress: `<what>: <number or status> [shipped|in progress]`.
     - Plans: `<what> [planned|in progress]`.
     - Problems: `Blocked: <what> by <cause> [in progress]`.
   - **Demo line:** it sits in A's `mechanism` or `change` frames, B's `mapping` frames, or C's `progress` frames. `references/demo.md` and `SKILL.md` say so in place of "the 'what it changes' part".
   - **Files that change:** `references/demo.md` joins the list.
6. **Resume.** The gate 1 approval line records the category: `- gate 1 (digest): <time>  category <A|B|C>  sha256 <hash>`. On resume, a `category:` under Answers that differs from the approval line re-opens gate 1, then gate 2. Asking for another category on resume does the same.

## Left to the builder

- The wording of the new sections and of `references/categories.md`, in the plain style of the files around them.
- Test names.
- How `check_script` finds `RUN.md`: it is in the run folder it already gets.
