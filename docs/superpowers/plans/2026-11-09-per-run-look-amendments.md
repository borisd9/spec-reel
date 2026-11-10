# Per-Run Look Amendments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the user's 2026-11-09 decisions on three of the per-run-look spec's unconfirmed calls:
1. Recent-run uniqueness counts the last **3** runs.
2. Yolo renders the **recommended look's sample only**.
3. A look may use **any Google Fonts family**, fetched into the run at gate 3.

**Architecture:**
- Decisions 1 and 2 are doc edits in `SKILL.md` and `references/yolo.md`.
- Decision 3 adds `scripts/fetch_font.py`. It downloads a family's Latin `.woff2` files from Google Fonts into the run's `assets/fonts/` and prints the `@font-face` rules, which go into the look's `index.template.html`.
- `look_samples.py` copies the run's `assets/fonts/` into each sample, so the sample renders with those fonts.

**Tech Stack:** Python 3 standard library (`urllib.request`, `unittest`), HyperFrames CLI, Markdown docs.

**Spec:** `docs/superpowers/specs/2026-10-26-per-run-look-design.md`, plus these decisions. Facts that come from outside the spec are pinned below.

**Branch:** `per-run-look-impl` (PR #14). Commit on it. Do not push.

**Test command:** `cd scripts && python3 -I -m unittest discover -s . -p 'test_*.py'`. Baseline: 179 tests, OK. With `-I`, run one file as `python3 -I -m unittest discover -s . -p test_fetch_font.py`.

## Global Constraints

- **Why a download is needed.** `<hyperframes dir>/references/format.md` § Fonts says the 19 bundled families (Inter, Montserrat, Outfit, Nunito, Oswald, League Gothic, Archivo Black, Space Mono, IBM Plex Mono, JetBrains Mono, EB Garamond, Playfair Display, Source Code Pro, Noto Sans JP, Roboto, Open Sans, Lato, Poppins) resolve by name. Any other family needs `@font-face` with `src: url('assets/fonts/x.woff2')` in the file that uses it, or lint fails `font_family_without_font_face`. Space Grotesk ships in this skill's `assets/fonts/`.
- **Display faces.** Inter, Space Grotesk and JetBrains Mono are still never the display face.
- **Standard library only.** Every network call goes through one function that tests replace.
- **Fonts live in the run.** Downloaded fonts go into the run folder, never into the skill's `assets/fonts/`. `test_skill_structure.py` still pins exactly 3 `.woff2` files there.
- **The request.** Google Fonts returns `.woff2` only to a browser User-Agent. Send exactly `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36` and nothing that identifies the user.
- **Comments.** Write a comment only for a non-obvious *why*.

## Review Focus

1. **The response has many subsets.** Google returns one `@font-face` per subset (`/* cyrillic */`, `/* latin-ext */`, `/* latin */`...). Expected: only the `/* latin */` block of each weight is downloaded. Test `test_only_latin_blocks_are_downloaded`.
2. **Unknown family or weight.** Google answers HTTP 400. Expected: exit 1 with `Google Fonts has no family "<F>" at weights <w...>`, and no file written. Test `test_unknown_family_fails_cleanly`.
3. **No network.** Expected: exit 1 with `could not reach Google Fonts (<reason>); use a bundled family instead`. Test `test_network_error_suggests_a_bundled_family`.
4. **A re-run or a resume.** Expected: files that already exist are not fetched again, and the printed rules are the same. Test `test_existing_files_are_not_fetched_again`.
5. **A sample of a look that uses a fetched font.** Expected: the sample has the run's fetched `.woff2` files under `sample/assets/fonts/`. Test `test_sample_gets_the_runs_fetched_fonts` in `test_look_samples.py`.

---

### Task 1: `scripts/fetch_font.py`

**Files:**
- Create: `scripts/fetch_font.py`
- Test: `scripts/test_fetch_font.py`

**Interfaces:**
- Produces: `main(argv, fetch=http_get) -> int`
  - CLI: `python3 -I fetch_font.py <project_dir> "<Family>" <weight> [<weight>...]`
  - `http_get(url, headers) -> bytes` raises `urllib.error.HTTPError` or `urllib.error.URLError`.
  - `slug(family) -> str` is lowercase with runs of non-alphanumerics turned into `-`, for example `"Press Start 2P"` becomes `"press-start-2p"`.
  - Files land at `<p>/assets/fonts/<slug>-<weight>.woff2`.
  - Stdout gets one rule per weight, exactly: `@font-face { font-family: "<Family>"; src: url("assets/fonts/<slug>-<weight>.woff2") format("woff2"); font-weight: <weight>; }`.

**Behavior:**
- **Bundled family** (the 19 above, or `Space Grotesk`): print `"<Family>" is bundled; no download needed` and exit 0. Fetch nothing and print no rules.
- **The CSS request:** `https://fonts.googleapis.com/css2?family=<Family with spaces as +>:wght@<weights joined by ;>&display=swap`, with the pinned User-Agent.
- **Parsing:** split the CSS into `(comment, block)` pairs on `/* <subset> */`. For each block whose subset is `latin`, read `font-weight: N` and the first `url(...)`. Download it when the target file is missing. A weight with no `latin` block fails: `no latin file for weight <w>`.
- **Errors:** HTTP 400 and network errors give the messages in Review Focus 2 and 3, and exit 1. Anything else propagates.
- **Usage:** with fewer than 3 arguments, print `usage: fetch_font.py <project_dir> "<Family>" <weight> [<weight>...]` and exit 1.

- [ ] **Step 1: Write the failing tests** in `scripts/test_fetch_font.py`, each with a fake `fetch` that records URLs:
  - `test_only_latin_blocks_are_downloaded`: the CSS has `/* cyrillic */` and `/* latin */` blocks for weights 400 and 700. Assert 1 CSS call plus 2 font calls, that the two files exist with the fake bytes, and that the two printed rules match the format exactly.
  - `test_css_request_uses_the_browser_user_agent`: assert that the first call's URL contains `family=Press+Start+2P:wght@400` and that `headers["User-Agent"]` equals the pinned string.
  - `test_bundled_family_needs_no_download`: `Lato` gives exit 0, no calls, and the "is bundled" message.
  - `test_unknown_family_fails_cleanly`: the fake raises `HTTPError(code=400)`. Assert exit 1, the message, and that `assets/fonts/` has no new file.
  - `test_network_error_suggests_a_bundled_family`: the fake raises `URLError("offline")`. Assert exit 1 and that the message contains `offline` and `bundled family`.
  - `test_existing_files_are_not_fetched_again`: run twice. Assert the second run makes only the CSS call and prints the same rules.
  - `test_slug`: `"Press Start 2P"` gives `"press-start-2p"`, and `"Noto Serif JP"` gives `"noto-serif-jp"`.
- [ ] **Step 2: Run.** Expected: everything fails with an import error.
- [ ] **Step 3: Implement** `scripts/fetch_font.py`, with a module docstring in the style of `look_samples.py`.
- [ ] **Step 4: Run the whole suite.** Expected: everything passes.
- [ ] **Step 5: Commit** with the message "Add fetch_font.py: any Google Fonts family, downloaded into the run".

### Task 2: Samples carry the run's fonts

**Files:**
- Modify: `scripts/look_samples.py`, `build_sample`
- Test: `scripts/test_look_samples.py`

- [ ] **Step 1: Write the failing test** `test_sample_gets_the_runs_fetched_fonts`. Put `assets/fonts/press-start-2p-400.woff2` in the fake run. Build the samples with the fake runner. Assert that `looks/<n>-<slug>/sample/assets/fonts/press-start-2p-400.woff2` exists with the same bytes.
- [ ] **Step 2: Run it.** Expected: FAIL.
- [ ] **Step 3: Implement.** In `build_sample`, before `build_index.build(sample)`, copy every file in `p / "assets/fonts"` (when it exists) into `sample / "assets/fonts"`. `build_index.build` already skips the bundled fonts that are present.
- [ ] **Step 4: Run the whole suite.** Expected: everything passes.
- [ ] **Step 5: Commit** with the message "look_samples: a sample carries the run's fetched fonts".

### Task 3: Docs for the three decisions

**Files:**
- Modify: `SKILL.md` § Look (gate 3), steps 3 and 4
- Modify: `references/yolo.md`, the `Gate 3: the look` row
- Modify: `README.md`, the gate 3 paragraph
- Modify: `docs/superpowers/specs/2026-10-26-per-run-look-design.md` § My calls
- Test: `scripts/test_skill_structure.py`

**Edits:**
- **`SKILL.md` step 3:** "the last five runs" becomes "the last three runs".
- **`SKILL.md` step 4:** replace it with these two points.
  - A look may use any Google Fonts family, in any weight. The bundled families resolve by name; name them. For any other family, run the fetch command below before writing the look, and paste its printed rules into the look's `index.template.html` next to the existing `@font-face` rules. Inter, Space Grotesk and JetBrains Mono are never the display face. Fetching sends only the family name and the weights to Google; the script text never leaves the machine. When the fetch fails, use a bundled family.

    ```bash
    python3 -I <this skill's directory>/scripts/fetch_font.py . "<Family>" <weights>
    ```
- **`yolo.md` gate 3 row, yolo column:** "Write the three looks, then render only the recommended one's sample: `look_samples.py . --look <its folder>`. If the sample still fails after the three fixes `SKILL.md` allows, try the next look the same way. When none renders, stop. Take the look whose sample rendered, and record `gate 3 (look): auto (yolo) <time> <look name> sha256 <hash>`. A failed font fetch means a bundled family, listed in the report."
- **`README.md`:** add one sentence: "A look can use any Google Fonts family; the skill downloads it into the run folder."
- **Spec § My calls:** add a line at the top: "Confirmed by the user on 2026-11-09, with changes: uniqueness counts the last 3 runs, yolo renders the recommended look's sample, and fonts can be any Google Fonts family fetched by `scripts/fetch_font.py`. The other calls stand." Then edit the three affected bullets to match.

- [ ] **Step 1: Write the failing test** `test_gate_3_decisions_2026_11_09`:

```python
def test_gate_3_decisions_2026_11_09(self):
    skill = (ROOT / "SKILL.md").read_text()
    self.assertIn("last three runs", skill)
    self.assertNotIn("last five runs", skill)
    self.assertIn("scripts/fetch_font.py", skill)
    yolo = (ROOT / "references/yolo.md").read_text()
    self.assertIn("--look", yolo)
    self.assertNotIn("skip look_samples.py", yolo)
```

- [ ] **Step 2: Run it.** Expected: FAIL.
- [ ] **Step 3: Make the edits** above.
- [ ] **Step 4: Run the whole suite.** Expected: everything passes.
- [ ] **Step 5: Commit** with the message "Gate 3: last three runs, a yolo sample, any Google Fonts family".
- [ ] **Step 6: Manual check.** In a temp folder under the scratchpad, run `python3 -I scripts/fetch_font.py <tmp> "Press Start 2P" 400`. Expected: exit 0, one `.woff2` file of more than 1 KB, and one printed rule. Delete the temp folder afterwards. If there is no network, say so in the report.
