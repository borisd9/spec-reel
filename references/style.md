# Style rules for the script and the caption

Read before showing the script at gate 2 and before writing `renders/share-copy.txt`. Check the text against every rule here and fix what fails. The viewer is a colleague who chose to watch, so the text states facts and does not sell them.

## Banned patterns

Each one has a short bad and good version.

- **Contrast reveal.** Do not set up a claim only to knock it down.
  - Bad: "It is not a new queue, it is a new way to retry."
  - Good: "Failed uploads now retry on their own."
- **Negation list.** Do not list what a thing is not before saying what it is.
  - Bad: "No new screens, no new settings, no new steps."
  - Good: "Uploads work as before, and a failed one retries."
- **Self-narration.** Do not announce what the next sentence does.
  - Bad: "Here is why this matters."
  - Good: Say the reason itself.
- **Tidy closer.** Do not end on a summary or a moral. End on the last fact, or on what comes next.
  - Bad: "In the end, it is all about trust."
  - Good: "Next, the team adds retry limits."
- **Fake-profound kicker.** Do not end a line on a short weighty phrase that adds no fact.
  - Bad: "Simple. Reliable. Done."
  - Good: "Retries stop after three tries."
- **Self-answered question.** Do not ask a question only to answer it.
  - Bad: "So what changes? Retries."
  - Good: "Retries are now automatic."

## For the scenes

- **Name what you explain.** A concept named on a `next` frame (a job, a check, a flag, a component) gets one sentence on what it will do, or it is not named. "Next comes the slow check job" tells the viewer nothing; "Next, a slow check will run every eval on drafts" does. The claim check flags a named concept with no explanation.

## For the voice

- A sentence has at most 25 words. Long sentences hurt Qwen3-TTS pacing and are hard to follow by ear.
- Read each line aloud in your head. Rewrite a line that has a tongue-twister, a run of consonants or a string of numbers.
- Spell out symbols and units the way a person says them ("about 40 percent", not "~40%").

## For the caption

- `share-copy.txt` stands alone: a reader who never opens the video learns what changes and what comes next.
- No emoji, no emoji bullets, no hashtags, no "Thoughts?", no call to action.
- The banned patterns above apply to it too.
