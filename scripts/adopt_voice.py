#!/usr/bin/env python3
"""Adopt narration files (Qwen3-TTS or the user's own engine) into a HyperFrames project.

    python3 -I adopt_voice.py <project_dir>                 # voice-in/NN.<ext> -> assets/voice/NN.wav + meta
                                                            # (SCRIPT.md is first written from user_script.txt; a file
                                                            # already transcribed is read from voice-cache/)
    python3 -I adopt_voice.py <project_dir> --pause 1.0     # same, with 1.0 s of silence after every line but the last
    python3 -I adopt_voice.py <project_dir> --check-speech  # lines whose transcript differs from SCRIPT.md (voice_heard.json)
    python3 -I adopt_voice.py <project_dir> --check         # every narrated frame has a voice, a WAV and words
    python3 -I adopt_voice.py <project_dir> --check-script  # SCRIPT.md is regenerated from user_script.txt; the script
                                                            # and storyboard open with the title intro,
                                                            # and every public/demo-* file has its Demo line and frame,
                                                            # and every other frame has a scene_job;
                                                            # warns about words the voice may misread

Standard library only. ffmpeg, ffprobe and `npx hyperframes transcribe` are reached through
three small functions that tests replace.
"""
import difflib
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EXTS = (".wav", ".mp3", ".m4a", ".aiff")
WHISPER_MODEL = "medium.en"
# Heading and spoken-text rules of the script files (the HyperFrames audio engine reads the same shape).
SCRIPT_HEADING = re.compile(r"^#{2,3}\s+.*?\(frame\s+(\d+)\)", re.I)
SCRIPT_TEXT = re.compile(r"^(?: {4,}|\t)(.+)$")
FRAME_RE = re.compile(r"^#{2,3}\s+(?:frame|beat|scene)\b.*?(\d+)", re.I)
VOICEOVER_RE = re.compile(r"^\s*[-*]\s+(?:voiceover|vo|voice_over|narration)\s*:\s*(.+?)\s*$", re.I)
INTRO_HEADING = re.compile(r"^#{2,3}\s+line\s+1\s+\W+\s*intro\s*\(frame\s+1\)", re.I | re.M)
TITLE_RE = re.compile(r"^\s*[-*]\s+on_screen_title\s*:\s*(.+?)\s*$", re.I)
MAX_INTRO_WORDS = 20
DEMO_HEADING = re.compile(r"^#{2,3}\s+line\s+\d+\s+\W+\s*demo\s*\(frame\s+\d+\)", re.I | re.M)
ASSETS_RE = re.compile(r"^\s*[-*]\s+asset_candidates\s*:\s*(.+?)\s*$", re.I)
SCENE_JOBS = ("why", "change", "proof", "next")
# Respelled for the voice only (the written script and SCRIPT.md keep the written form). The config `pronunciations`
# setting is merged over this by the caller.
BUILTIN_RESPELLINGS = {"id": "I-D", "ids": "I-Ds", "PR": "P R", "v8": "V-eight"}
CARD_RE = re.compile(r"^\s*[-*]\s+(scene_job|before|after)\s*:\s*(.+?)\s*$", re.I)


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


def scene_cards(storyboard_md):
    """STORYBOARD.md -> {frame: {"scene_job"|"before"|"after": value, "demo": True when it names a public/demo-* file}}."""
    cards, cur = {}, None
    for line in storyboard_md.splitlines():
        h = FRAME_RE.match(line)
        if h:
            cur = cards.setdefault(int(h.group(1)), {})
            continue
        c, a = CARD_RE.match(line), ASSETS_RE.match(line)
        if cur is not None and c and c.group(2).strip("\"'").strip():
            cur[c.group(1).lower()] = c.group(2).strip("\"'").strip().lower()
        if cur is not None and a and re.search(r"public/demo-", a.group(1)):
            cur["demo"] = True
    return cards


def words_of(text):
    return re.sub(r"[^\w\s]", " ", text.lower().replace("'", "")).split()


def respell(text, pairs):
    """Whole-word, case-sensitive WRITTEN -> SPOKEN replacements, for the text sent to the TTS engine only."""
    for written, spoken in dict(pairs).items():
        text = re.sub(r"(?<!\w)" + re.escape(written) + r"(?!\w)", lambda _: spoken, text)
    return text


def unrespell(text, pairs=BUILTIN_RESPELLINGS):
    """The reverse: SPOKEN -> WRITTEN (case-insensitive; a hyphen also matches a space), for the checks."""
    for written, spoken in dict(pairs).items():
        pattern = re.escape(spoken).replace(r"\-", r"[-\s]?")
        text = re.sub(r"(?<!\w)" + pattern + r"(?!\w)", lambda _: written, text, flags=re.I)
    return text


# --- one owner per fact and per script ------------------------------------------------------

def load_facts(p):
    """facts.json (flat {key: text}) or {}."""
    f = Path(p) / "facts.json"
    return json.loads(f.read_text()) if f.exists() else {}


def fill_facts(text, facts):
    """{{key}} -> facts[key]. ValueError names a key facts.json lacks."""
    def one(m):
        if m.group(1) not in facts:
            raise ValueError(f"facts.json has no '{m.group(1)}' (named as {{{{{m.group(1)}}}}})")
        return str(facts[m.group(1)])
    return re.sub(r"\{\{(\w+)\}\}", one, text)


def sync_script(p):
    """SCRIPT.md is generated: user_script.txt with its {{facts}} filled. Nothing to do without user_script.txt."""
    src = Path(p) / "user_script.txt"
    if src.exists():
        (Path(p) / "SCRIPT.md").write_text(fill_facts(src.read_text(), load_facts(p)))


NUMBER_WORDS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen " \
               "sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def number_words(n):
    """45 -> "fortyfive", 318 -> "threehundredeighteen" (one run of letters, so spacing never matters)."""
    if n < 20:
        return NUMBER_WORDS[n]
    if n < 100:
        return TENS[n // 10] + (NUMBER_WORDS[n % 10] if n % 10 else "")
    if n < 1000:
        return NUMBER_WORDS[n // 100] + "hundred" + (number_words(n % 100) if n % 100 else "")
    if n < 1_000_000:
        return number_words(n // 1000) + "thousand" + (number_words(n % 1000) if n % 1000 else "")
    return str(n)


def canon(text, pairs=BUILTIN_RESPELLINGS):
    """What a listener cannot tell apart: case, spaces, hyphens, digits vs number words, the respellings."""
    text = unrespell(text, pairs).lower().replace("%", " percent")
    text = re.sub(r"\ba (?=hundred|thousand|million)", "one ", text)
    return re.sub(r"[^a-z]", "", re.sub(r"\d+", lambda m: number_words(int(m.group())), text))


# Words Qwen3-TTS tends to misread: it spells a lowercase acronym out, reads an identifier as one blob, and trips
# on digits stuck to letters.
RISKY = (
    (lambda t: "_" in t or ("-" in t and re.search(r"\d", t)), "an identifier; write it as plain words"),
    (lambda t: re.search(r"[A-Za-z]\d|\d[A-Za-z]", t), "digits stuck to letters; add a respelling"),
    (lambda t: t.isalpha() and t.islower() and len(t) <= 4 and not re.search(r"[aeiouy]", t),
     "a lowercase acronym; write it in capitals or add a respelling"),
)


def risky_tokens(text, pairs=BUILTIN_RESPELLINGS):
    """[(token, why)] for words in the spoken text that the voice may misread. Respelled words are not listed."""
    out = []
    for tok in respell(text, pairs).split():
        tok = tok.strip(".,;:!?()\"'")
        out += [(tok, why) for test, why in RISKY if tok and test(tok)][:1]
    return out


# --- the three replaceable external calls -------------------------------------------------

def to_wav(src, dst, pad_s=0.0):
    pad = ["-af", f"apad=pad_dur={pad_s}"] if pad_s > 0 else []
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ar", "44100", "-ac", "1", *pad, str(dst)],
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
        subprocess.run(["npx", "hyperframes", "transcribe", str(wav), "--engine", "whisper", "--model", WHISPER_MODEL, "--dir", td],
                       check=True, capture_output=True, text=True, cwd=wav.parents[2])
        arr = json.loads((Path(td) / "transcript.json").read_text())
    return [{"text": w.get("text", w.get("word", "")), "start": w["start"], "end": w["end"]} for w in arr]


def cached_transcribe(p, wav, transcribe):
    """transcribe(wav), remembered by the WAV's SHA-256 in voice-cache/<sha>.json: an unchanged file is never
    transcribed twice. Returns (words, True when it came from the cache)."""
    f = Path(p) / "voice-cache" / f"{hashlib.sha256(Path(wav).read_bytes()).hexdigest()}.json"
    if f.exists():
        return json.loads(f.read_text()), True
    words = transcribe(wav)
    if words:
        f.parent.mkdir(exist_ok=True)
        f.write_text(json.dumps(words))
    return words, False


# --- script words on transcript timings ---------------------------------------------------

def _norm(tok):
    return re.sub(r"[^\w]", "", tok.lower().replace("'", ""))


def _opcodes(script_text, heard):
    a = [_norm(t) for t in script_text.split()]
    b = [_norm(h["text"]) for h in heard]
    return difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes()


def align_words(script_text, heard):
    """The script's own tokens on the transcript's timings: [{text, start, end}], one per script token."""
    toks = script_text.split()
    out, last_end = [], None
    for tag, i1, i2, j1, j2 in _opcodes(script_text, heard):
        n, k = i2 - i1, j2 - j1
        if tag == "insert":  # heard words the script does not have
            continue
        if tag == "delete":  # script words nobody said: zero-length, right after the previous word
            at = last_end if last_end is not None else (heard[j1]["start"] if j1 < len(heard) else 0.0)
            out += [{"text": t, "start": at, "end": at} for t in toks[i1:i2]]
            continue
        if n == k:
            spans = [(h["start"], h["end"]) for h in heard[j1:j2]]
        else:  # unequal replace: spread the heard span evenly over the script tokens
            s, e = heard[j1]["start"], heard[j2 - 1]["end"]
            spans = [(s + d * (e - s) / n, s + (d + 1) * (e - s) / n) for d in range(n)]
        out += [{"text": t, "start": s, "end": e} for t, (s, e) in zip(toks[i1:i2], spans)]
        last_end = out[-1]["end"]
    return out


def speech_diffs(script_text, heard, pairs=BUILTIN_RESPELLINGS):
    """[(want, got)] where what was heard differs from the script. Differences a listener cannot hear are not
    diffs: case, spaces and hyphens inside a word ("PR412" for "PR 412"), digits for number words, respellings."""
    toks = script_text.split()
    diffs = []
    for tag, i1, i2, j1, j2 in _opcodes(script_text, heard):
        if tag == "equal":
            continue
        want, got = " ".join(toks[i1:i2]), " ".join(h["text"].strip() for h in heard[j1:j2])
        if want and got and canon(want, pairs) == canon(got, pairs):
            continue
        diffs.append((want, got))
    return diffs


def diff_lines(frame, text, heard):
    return [f'frame {frame}: heard "{got}" for "{want}"' for want, got in speech_diffs(text, heard)]


# --- modes ---------------------------------------------------------------------------------

def fail(lines):
    print("\n".join(lines), file=sys.stderr)
    return 1


def adopt(p, to_wav, probe_duration, transcribe, pause_s=0.0):
    try:
        sync_script(p)
    except ValueError as e:
        return fail([str(e)])
    script = p / "SCRIPT.md"
    if not script.exists():
        return fail([f"SCRIPT.md not found in {p}"])
    lines = parse_script(script.read_text())
    if not lines:
        return fail(["SCRIPT.md has no '(Frame N)' headings"])
    last_frame = max(f for f, _ in lines)
    problems, voices, heard_by_frame, cached = [], [], {}, 0
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
            to_wav(found[0], dst, pad_s=pause_s if frame != last_frame else 0.0)
            duration = probe_duration(dst)
            words, hit = cached_transcribe(p, dst, transcribe)
            cached += hit
        except Exception as e:  # ffmpeg, ffprobe or transcribe failed on this file
            problems.append(f"frame {frame}: unreadable ({found[0].name}): {e}")
            continue
        if not words:
            problems.append(f"frame {frame}: no words found in {found[0].name}")
            continue
        heard_by_frame[str(frame)] = [{"text": w["text"], "start": round(w["start"], 3), "end": round(w["end"], 3)}
                                      for w in words]
        voices.append({"frame": frame, "path": f"assets/voice/{nn}.wav", "duration_s": round(duration, 3),
                       "words": [{"id": f"w{i}", "text": w["text"], "start": round(w["start"], 3),
                                  "end": round(w["end"], 3)} for i, w in enumerate(align_words(text, words))]})
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
    (p / "voice_heard.json").write_text(json.dumps(heard_by_frame, indent=2))
    print(f"adopted {len(voices)} voice file(s) ({len(voices) - cached} transcribed, {cached} from voice-cache/)"
          " -> audio_meta.json, audio_engine_meta.json")
    diffs = [d for frame, text in lines for d in diff_lines(frame, text, heard_by_frame[str(frame)])]
    if diffs:
        print("\n".join(diffs))
        print(f"run adopt_voice.py {p} --check-speech to list these again")
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
    scripts = {n: (p / n) for n in ("user_script.txt", "STORYBOARD.md")}
    # With no STORYBOARD.md yet (the frame plan comes after voicing starts) only the script's own rules are checked.
    absent = [n for n, f in scripts.items() if not f.exists() and n != "STORYBOARD.md"]
    if absent:
        return fail([f"{n} not found in {p}" for n in absent])
    try:
        approved_md = fill_facts(scripts["user_script.txt"].read_text(), load_facts(p))
        sync_script(p)  # SCRIPT.md is generated, so it can never disagree with user_script.txt
    except ValueError as e:
        return fail([str(e)])
    approved = parse_script(approved_md)
    problems = []
    if not INTRO_HEADING.search(approved_md) or not approved or approved[0][0] != 1:
        problems.append("user_script.txt must open with '## Line 1 — Intro (Frame 1)'")
    elif not 0 < len(unrespell(approved[0][1]).split()) <= MAX_INTRO_WORDS:
        # the written words: "P R" counts as the one word "PR", a hyphenated word as one
        problems.append(f"frame 1: the intro is one short sentence of at most {MAX_INTRO_WORDS} words")
    storyboard = scripts["STORYBOARD.md"].read_text() if scripts["STORYBOARD.md"].exists() else None
    demos = sorted(f.name for f in (p / "public").glob("demo-*"))
    demo_lines = len(DEMO_HEADING.findall(approved_md))
    if demo_lines < len(demos):
        problems.append(f"user_script.txt has {demo_lines} Demo line(s) for {len(demos)} demo file(s)")
    if storyboard is not None:
        if not intro_title(storyboard):
            problems.append("frame 1: STORYBOARD.md has no on_screen_title for the intro")
        problems += [f"{d}: no STORYBOARD.md frame names public/{d} in asset_candidates"
                     for d in demos if d not in named_assets(storyboard)]
        for frame, card in sorted(scene_cards(storyboard).items()):
            if frame == 1 or card.get("demo"):  # the intro and the Demo frames have no scene_job
                continue
            if card.get("scene_job") not in SCENE_JOBS:
                problems.append(f"frame {frame}: STORYBOARD.md has no scene_job")
            elif card["scene_job"] == "change" and not (card.get("before") and card.get("after")):
                problems.append(f"frame {frame}: scene_job change needs before and after")
    for frame, text in approved:  # warnings only: they never fail the check
        for tok, why in risky_tokens(text):
            print(f'warning: frame {frame}: "{tok}" is {why}', file=sys.stderr)
    return fail(problems) if problems else 0


def check_speech(p):
    absent = [n for n in ("SCRIPT.md", "voice_heard.json") if not (p / n).exists()]
    if absent:
        return fail([f"{n} not found in {p}" for n in absent])
    heard = json.loads((p / "voice_heard.json").read_text())
    problems = []
    for frame, text in parse_script((p / "SCRIPT.md").read_text()):
        if str(frame) in heard:
            problems += diff_lines(frame, text, heard[str(frame)])
        else:
            problems.append(f"frame {frame}: not voiced")
    return fail(problems) if problems else 0


USAGE = "usage: adopt_voice.py <project_dir> [--pause SECONDS | --check | --check-script | --check-speech]"


def main(argv, to_wav=to_wav, probe_duration=probe_duration, transcribe=transcribe):
    argv, pause_s, paused = list(argv), 0.0, "--pause" in argv
    if paused:  # `--pause SECONDS`: take both tokens out before the mode/argument split
        i = argv.index("--pause")
        try:
            pause_s = float(argv[i + 1])
        except (IndexError, ValueError):
            return fail([USAGE])
        if not math.isfinite(pause_s) or pause_s < 0:
            return fail([USAGE])
        del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    modes = [a for a in argv if a.startswith("--")]
    if len(args) != 1 or modes not in ([], ["--check"], ["--check-script"], ["--check-speech"]) or (paused and modes):
        return fail([USAGE])
    p = Path(args[0])
    if modes == ["--check-speech"]:
        return check_speech(p)
    if modes == ["--check"]:
        return check(p)
    if modes == ["--check-script"]:
        return check_script(p)
    return adopt(p, to_wav, probe_duration, transcribe, pause_s)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
