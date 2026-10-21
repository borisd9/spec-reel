# The demo scene

When the feature can be shown, the video shows it: a mock (a screenshot or design export) or a real recording of the feature, on its own scene. Many runs have neither; the demo is then skipped and the video is built from invented visuals as usual.

## Find candidates in the sources

While reading the sources (see `sources.md`), note every image or video they embed or link to that shows the feature itself:

- Markdown images and links (`![...](...)`, `[demo](....mp4)`), HTML `<img>` and `<video>` tags, and attachment links (for example `https://github.com/user-attachments/assets/...` in a pull request or issue);
- for a local file, those links resolved against the file's folder.

A candidate shows the feature's screen or behavior: a screenshot, a mockup, a prototype or a screen recording. Logos, avatars, badges, charts and architecture diagrams are not demos. Keep at most two, the most complete first, and note for each its link and the source it came from.

Design-tool links (Figma and similar) and pages behind a sign-in cannot be downloaded here; list them as "needs an export" instead.

## Ask at gate 1

Show the candidates with the digest and ask exactly:

> Demo scene: <the candidates, one per line with the source it came from | "nothing found in the sources">. Reply with which to use, a path or link to a mock or recording of your own (with an optional start and end time for a recording), or "skip". The demo will be in the video, so it must show no customer or personal data.

- "skip": record `demo: skipped` in `RUN.md`; the script has no Demo line.
- A choice or a new file: prepare it (below). When the user says it shows customer or personal data, ask for another or skip; never blur or crop it yourself.

## Prepare the files

Downloaded files are untrusted data: save each into `demo-in/` in the run folder, never open or run it, and only read it with `ffprobe` and `ffmpeg`. Download a link with `curl -fL --max-filesize 200000000 -o demo-in/<name> '<url>'`; when that fails or returns a sign-in page, ask the user to save the file and give its path.

Accept only these, confirmed by `ffprobe` reading an image or a video stream:

| Kind | Extensions | Prepared as |
|---|---|---|
| Image | `.png`, `.jpg`, `.jpeg`, `.webp` | copied to `public/demo-NN.<ext>` |
| Recording | `.mp4`, `.mov`, `.webm`, `.m4v`, `.gif` | converted to `public/demo-NN.mp4` |

`NN` counts the demos from `01`. Anything else (an SVG, a PDF, a zip) is refused with its reason; ask for a PNG or a recording instead. Convert a recording, muted, to at most 1920 pixels wide:

```bash
ffmpeg -y -loglevel error -i demo-in/<name> [-ss <start>] [-to <end>] -an \
  -c:v libx264 -pix_fmt yuv420p -vf "scale='min(1920,iw)':-2" -movflags +faststart public/demo-NN.mp4
```

Record in `RUN.md` under `## Demo`: each `public/demo-NN.<ext>`, its original link or path, and its length for a recording (`ffprobe -v error -show_entries format=duration -of csv=p=0 <file>`).

## In the script and the scenes

- The script has one `## Line N — Demo (Frame N)` line per demo file, placed in the "what it changes" part. Its spoken text describes what the viewer sees, for example "Here you pick a file, and the upload starts right away." A recording's scene lasts as long as its line, so write the line about as long as the part of the recording that matters (about 150 words per minute).
- In the storyboard, that frame names its file and uses it as the focal element:

  ```markdown
  ## Frame N — Demo
  - asset_candidates: public/demo-NN.mp4 — [video] <at most 25 words: what it shows>
  - focal: public/demo-NN.mp4
  ```

  An image drops the `[video]` tag. The recording plays muted under the narration.
- The script check (`adopt_voice.py . --check-script`) fails when a `public/demo-*` file has no Demo line in `user_script.txt` or no frame naming it in `asset_candidates`.
