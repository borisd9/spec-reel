#!/usr/bin/env python3
"""Adopt the user's own narration files into a HyperFrames faceless-explainer project.

    python3 -I adopt_voice.py <project_dir>                 # voice-in/NN.<ext> -> assets/voice/NN.wav + meta
    python3 -I adopt_voice.py <project_dir> --check         # every narrated frame has a voice, a WAV and words
    python3 -I adopt_voice.py <project_dir> --check-script  # SCRIPT.md words == user_script.txt words, line by line,
                                                            # the script and storyboard open with the title intro,
                                                            # and every public/demo-* file has its Demo line and frame

Standard library only. ffmpeg, ffprobe and `npx hyperframes transcribe` are reached through
three small functions that tests replace.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EXTS = (".wav", ".mp3", ".m4a", ".aiff")
# Same rules as parseScript / runSyncDurations in faceless-explainer's scripts/audio.mjs.
SCRIPT_HEADING = re.compile(r"^#{2,3}\s+.*?\(frame\s+(\d+)\)", re.I)
SCRIPT_TEXT = re.compile(r"^(?: {4,}|\t)(.+)$")
FRAME_RE = re.compile(r"^#{2,3}\s+(?:frame|beat|scene)\b.*?(\d+)", re.I)
VOICEOVER_RE = re.compile(r"^\s*[-*]\s+(?:voiceover|vo|voice_over|narration)\s*:\s*(.+?)\s*$", re.I)
INTRO_HEADING = re.compile(r"^#{2,3}\s+line\s+1\s+\W+\s*intro\s*\(frame\s+1\)", re.I | re.M)
TITLE_RE = re.compile(r"^\s*[-*]\s+on_screen_title\s*:\s*(.+?)\s*$", re.I)
MAX_INTRO_WORDS = 20
DEMO_HEADING = re.compile(r"^#{2,3}\s+line\s+\d+\s+\W+\s*demo\s*\(frame\s+\d+\)", re.I | re.M)
ASSETS_RE = re.compile(r"^\s*[-*]\s+asset_candidates\s*:\s*(.+?)\s*$", re.I)


def parse_script(md):
    """SCRIPT.md or user_script.txt -> [(frame, spoken text)], one entry per heading (text may be empty)."""
    out = []
    for line in md.splitlines():
        h = SCRIPT_HEADING.match(line)
        if h:
            out.append([int(h.group(1)), ""])
            continue
        if not out or re.match(r"^\s*\*\*", line):
            continue
        m = SCRIPT_TEXT.match(line)
        if m:
            out[-1][1] = (out[-1][1] + " " + m.group(1).strip()).strip()
    return [(f, t) for f, t in out]


def narrated_frames(storyboard_md):
    """STORYBOARD.md -> sorted frame numbers whose voiceover is non-empty."""
    frames, cur = {}, None
    for line in storyboard_md.splitlines():
        h = FRAME_RE.match(line)
        if h:
            cur = int(h.group(1))
            frames.setdefault(cur, False)
            continue
        m = VOICEOVER_RE.match(line)
        if cur is not None and m and m.group(1).strip().strip("\"'").strip():
            frames[cur] = True
    return sorted(f for f, narrated in frames.items() if narrated)


def intro_title(storyboard_md):
    """STORYBOARD.md -> frame 1's `on_screen_title`, or "" when it has none."""
    cur = None
    for line in storyboard_md.splitlines():
        h = FRAME_RE.match(line)
        if h:
            cur = int(h.group(1))
            continue
        m = TITLE_RE.match(line)
        if cur == 1 and m and m.group(1).strip("\"'").strip():
            return m.group(1).strip("\"'").strip()
    return ""


def named_assets(storyboard_md):
    """STORYBOARD.md -> basenames named in any frame's asset_candidates ("public/a.mp4 — desc; ...")."""
    names = set()
    for line in storyboard_md.splitlines():
        m = ASSETS_RE.match(line)
        if m:
            names.update(Path(re.split(r"\s+[—–-]\s+", seg)[0].strip()).name for seg in m.group(1).split(";"))
    return names


def words_of(text):
    return re.sub(r"[^\w\s]", " ", text.lower().replace("'", "")).split()


# --- the three replaceable external calls -------------------------------------------------

def to_wav(src, dst):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ar", "44100", "-ac", "1", str(dst)],
                   check=True, capture_output=True, text=True)


def probe_duration(wav):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(wav)],
                       check=True, capture_output=True, text=True)
    return float(r.stdout.strip())


def transcribe(wav):
    """Word timings through the same call the HyperFrames audio engine makes. [{text, start, end}]"""
    wav = Path(wav).resolve()
    with tempfile.TemporaryDirectory(prefix="hf-trans-") as td:
        # wav sits at <project>/assets/voice/NN.wav
        subprocess.run(["npx", "hyperframes", "transcribe", str(wav), "--model", "small.en", "--dir", td],
                       check=True, capture_output=True, text=True, cwd=wav.parents[2])
        arr = json.loads((Path(td) / "transcript.json").read_text())
    return [{"text": w.get("text", w.get("word", "")), "start": w["start"], "end": w["end"]} for w in arr]


# --- modes ---------------------------------------------------------------------------------

def fail(lines):
    print("\n".join(lines), file=sys.stderr)
    return 1


def adopt(p, to_wav, probe_duration, transcribe):
    script = p / "SCRIPT.md"
    if not script.exists():
        return fail([f"SCRIPT.md not found in {p}"])
    lines = parse_script(script.read_text())
    if not lines:
        return fail(["SCRIPT.md has no '(Frame N)' headings"])
    problems, voices = [], []
    (p / "assets/voice").mkdir(parents=True, exist_ok=True)
    for frame, text in lines:
        nn = f"{frame:02d}"
        if not text:
            problems.append(f"frame {frame}: heading has no spoken text")
            continue
        found = [f for f in (p / "voice-in").glob(f"{nn}.*") if f.suffix.lower() in EXTS] \
            if (p / "voice-in").is_dir() else []
        if len(found) != 1:
            why = "several files" if found else "missing"
            names = ", ".join(sorted(f.name for f in found)) or "|".join(f"voice-in/{nn}{e}" for e in EXTS)
            problems.append(f"frame {frame}: {why} ({names})")
            continue
        dst = p / "assets/voice" / f"{nn}.wav"
        try:
            to_wav(found[0], dst)
            duration = probe_duration(dst)
            words = transcribe(dst)
        except Exception as e:  # ffmpeg, ffprobe or transcribe failed on this file
            problems.append(f"frame {frame}: unreadable ({found[0].name}): {e}")
            continue
        if not words:
            problems.append(f"frame {frame}: no words found in {found[0].name}")
            continue
        voices.append({"frame": frame, "path": f"assets/voice/{nn}.wav", "duration_s": round(duration, 3),
                       "words": [{"id": f"w{i}", "text": w["text"], "start": round(w["start"], 3),
                                  "end": round(w["end"], 3)} for i, w in enumerate(words)]})
    if problems:
        return fail(problems)
    # Both files, one pass; an existing file keeps everything except `voices`.
    for name, key in (("audio_meta.json", "frame"), ("audio_engine_meta.json", "id")):
        f = p / name
        meta = json.loads(f.read_text()) if f.exists() else {"bgm": None, "bgm_pending": False, "voices": [], "sfx": []}
        # audio_meta.json keys a voice by `frame` (int); the engine sidecar by `id` ("NN")
        meta["voices"] = [{key: v["frame"] if key == "frame" else f"{v['frame']:02d}",
                           **{k: x for k, x in v.items() if k != "frame"}} for v in voices]
        f.write_text(json.dumps(meta, indent=2))
    print(f"adopted {len(voices)} voice file(s) -> audio_meta.json, audio_engine_meta.json")
    return 0


def check(p):
    sb = p / "STORYBOARD.md"
    if not sb.exists():
        return fail([f"STORYBOARD.md not found in {p}"])
    meta_file = p / "audio_meta.json"
    meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
    by_frame = {int(v["frame"]): v for v in meta.get("voices", [])}
    problems = []
    for frame in narrated_frames(sb.read_text()):
        v = by_frame.get(frame)
        if not v:
            problems.append(f"frame {frame}: no voice entry in audio_meta.json")
        elif not (p / v.get("path", "")).is_file():
            problems.append(f"frame {frame}: voice file {v.get('path')} does not exist")
        elif not v.get("words"):
            problems.append(f"frame {frame}: voice has no words")
    return fail(problems) if problems else 0


def check_script(p):
    scripts = {n: (p / n) for n in ("SCRIPT.md", "user_script.txt", "STORYBOARD.md")}
    absent = [n for n, f in scripts.items() if not f.exists()]
    if absent:
        return fail([f"{n} not found in {p}" for n in absent])
    actual, approved = (parse_script(scripts[n].read_text()) for n in ("SCRIPT.md", "user_script.txt"))
    problems = []
    if not INTRO_HEADING.search(scripts["user_script.txt"].read_text()) or not approved or approved[0][0] != 1:
        problems.append("user_script.txt must open with '## Line 1 — Intro (Frame 1)'")
    elif not 0 < len(words_of(approved[0][1])) <= MAX_INTRO_WORDS:
        problems.append(f"frame 1: the intro is one short sentence of at most {MAX_INTRO_WORDS} words")
    storyboard = scripts["STORYBOARD.md"].read_text()
    if not intro_title(storyboard):
        problems.append("frame 1: STORYBOARD.md has no on_screen_title for the intro")
    demos = sorted(f.name for f in (p / "public").glob("demo-*"))
    demo_lines = len(DEMO_HEADING.findall(scripts["user_script.txt"].read_text()))
    if demo_lines < len(demos):
        problems.append(f"user_script.txt has {demo_lines} Demo line(s) for {len(demos)} demo file(s)")
    problems += [f"{d}: no STORYBOARD.md frame names public/{d} in asset_candidates"
                 for d in demos if d not in named_assets(storyboard)]
    if len(actual) != len(approved):
        problems.append(f"SCRIPT.md has {len(actual)} lines, user_script.txt has {len(approved)} lines")
    for (_, got), (frame, want) in zip(actual, approved):
        if words_of(got) != words_of(want):
            problems.append(f"frame {frame}: approved {words_of(want)} but SCRIPT.md has {words_of(got)}")
    return fail(problems) if problems else 0


def main(argv, to_wav=to_wav, probe_duration=probe_duration, transcribe=transcribe):
    args = [a for a in argv if not a.startswith("--")]
    modes = [a for a in argv if a.startswith("--")]
    if len(args) != 1 or modes not in ([], ["--check"], ["--check-script"]):
        return fail(["usage: adopt_voice.py <project_dir> [--check | --check-script]"])
    p = Path(args[0])
    if modes == ["--check"]:
        return check(p)
    if modes == ["--check-script"]:
        return check_script(p)
    return adopt(p, to_wav, probe_duration, transcribe)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
