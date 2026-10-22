#!/usr/bin/env python3
"""Write index.html for a run: one scene host and one voice clip per frame.

    python3 -I build_index.py <project_dir>

Reads audio_meta.json (the voice, per frame), STORYBOARD.md (each frame's scene id, from its
`- src: compositions/<id>.html` line) and facts.json (optional, flat {key: text}). Each frame's slot is
that line's measured voice (the pause is already in it). Scenes cue on word text, `at("feed")` or
`at("draft", 2)` for the second one, or on word index with `w(i)`; the build fails when an `at()` names a
word the line does not have. Also puts the bundled fonts into assets/fonts/ and the progress strip into
compositions/ when the run has none. Re-run after any re-voice, scene rename or facts change.

Standard library only.
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adopt_voice import FRAME_RE  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
SRC_RE = re.compile(r"^\s*[-*]\s+src\s*:\s*(?:compositions/)?([\w-]+)\.html\s*$", re.I)
AT_RE = re.compile(r"\bat\(\s*\"([^\"]+)\"\s*(?:,\s*(\d+)\s*)?\)")


def scene_ids(storyboard_md):
    """STORYBOARD.md -> {frame: scene id}, from each frame's `- src: compositions/<id>.html`."""
    ids, cur = {}, None
    for line in storyboard_md.splitlines():
        h = FRAME_RE.match(line)
        if h:
            cur = int(h.group(1))
            continue
        m = SRC_RE.match(line)
        if cur is not None and m:
            ids[cur] = m.group(1)
    return ids


def word_key(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def layout(voices, ids):
    """[(scene id, start, duration, voice)] in frame order. Raises ValueError when frames and scenes disagree."""
    voices = sorted(voices, key=lambda v: v["frame"])
    frames = [v["frame"] for v in voices]
    if frames != sorted(ids):
        raise ValueError(f"audio_meta.json has frames {frames}, STORYBOARD.md names scenes for frames {sorted(ids)}")
    out, t = [], 0.0
    for v in voices:
        out.append((ids[v["frame"]], t, v["duration_s"], v))
        t += v["duration_s"]
    return out


def find_word(words, word, n=1):
    """Start of the n-th occurrence of `word` among the line's words, or None. Same rule as fx.at in the template."""
    starts = [w["start"] for w in words if word_key(w["text"]) == word_key(word)]
    return starts[n - 1] if len(starts) >= n else None


def cue_problems(scene_id, source, words):
    """at("word", n) calls in a scene's source that the line's words cannot satisfy."""
    source = re.sub(r"//[^\n]*", "", re.sub(r"<!--.*?-->", "", source, flags=re.S))
    return [f'{scene_id}: at("{word}", {nth or 1}) but the line has no such word' for word, nth in AT_RE.findall(source)
            if find_word(words, word, int(nth or 1)) is None]


def build(p):
    """Write index.html. Returns (total seconds, scene count) or raises ValueError with the problems."""
    for name in ("audio_meta.json", "STORYBOARD.md"):
        if not (p / name).exists():
            raise ValueError(f"{name} not found in {p}")
    ids = scene_ids((p / "STORYBOARD.md").read_text())
    scenes = layout(json.loads((p / "audio_meta.json").read_text())["voices"], ids)
    facts = json.loads((p / "facts.json").read_text()) if (p / "facts.json").exists() else {}
    problems = []
    for sid, _, _, v in scenes:
        src = p / "compositions" / f"{sid}.html"
        if not src.exists():
            problems.append(f"{sid}: compositions/{sid}.html not found")
        else:
            problems += cue_problems(sid, src.read_text(), v["words"])
    if problems:
        raise ValueError("\n".join(problems))

    hosts, audio, words, vo, dur = [], [], {}, {}, {}
    for sid, t, d, v in scenes:
        hosts.append(f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                     f'data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="1" data-track-kind="graphics" '
                     f'data-width="1920" data-height="1080"></div>')
        audio.append(f'      <audio id="vo-{v["frame"]:02d}" class="clip" src="{v["path"]}" data-start="{t:.3f}" '
                     f'data-duration="{d:.3f}" data-track-index="{2 + (v["frame"] + 1) % 2 * 2}" data-volume="1"></audio>')
        words[sid] = [[w["text"], round(w["start"], 3)] for w in v["words"]]
        vo[sid] = [s for _, s in words[sid]]
        dur[sid] = d
    total = round(sum(dur.values()), 3)
    fact_vars = "".join(",\n    " + html.escape(json.dumps({"id": k, "type": "string", "label": k, "default": str(x)}),
                                              quote=True) for k, x in facts.items())

    def js(obj):  # a JSON literal inside <script>: "</" must not end it
        return json.dumps(obj, separators=(",", ":")).replace("</", "<\\/")

    # A run restyled for another preset keeps its own copy of the template.
    template = p / "build/index.template.html"
    out = (template if template.exists() else SKILL / "assets/index.template.html").read_text()
    for key, value in (("%TOTAL%", f"{total:.3f}"), ("%HOSTS%", "\n".join(hosts)), ("%AUDIO%", "\n".join(audio)),
                       ("%WORDS%", js(words)), ("%VO%", js(vo)), ("%DUR%", js(dur)), ("%FACTS%", js(facts)),
                       ("%FACT_VARS%", fact_vars)):
        out = out.replace(key, value)
    (p / "index.html").write_text(out)
    # The shared files a scene expects: fonts (root-relative) and the progress strip. Never overwrite the run's own.
    (p / "assets/fonts").mkdir(parents=True, exist_ok=True)
    for f in (SKILL / "assets/fonts").iterdir():
        if not (p / "assets/fonts" / f.name).exists():
            shutil.copy(f, p / "assets/fonts" / f.name)
    if not (p / "compositions/progress.html").exists():
        shutil.copy(SKILL / "assets/progress.html", p / "compositions/progress.html")
    return total, len(scenes)


def main(argv):
    if len(argv) != 1:
        print("usage: build_index.py <project_dir>", file=sys.stderr)
        return 1
    try:
        total, n = build(Path(argv[0]))
    except (ValueError, KeyError) as e:
        print(e, file=sys.stderr)
        return 1
    print(f"index.html: {n} frames, {total:.3f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
