#!/usr/bin/env python3
"""Everything after a change, in one command. Stops at the first failing step and names it; a video QC failure
is recorded instead, so the cover and RUN.md still follow, and the exit code is non-zero.

    python3 -I finish.py <project_dir> --review    # seconds: adopt, voice check, build, lint, layout check, stills
    python3 -I finish.py <project_dir> --final     # adopt, check, build, lint, render, loudness, QC, cover, RUN.md

--review looks only at the scenes that changed since the last finish run (their voice file or their
compositions/<id>.html, or facts.json for every scene), runs `hyperframes check` at the last half second of
each (overflow, lint, contrast) and writes a still of that moment to review/snapshots/. --final renders renders/video.raw.mp4 once, then makes renders/video.mp4 (loudness
normalized, title cover on frame 0), fills renders/share-copy.txt from renders/share-copy.template.txt when
there is one, and appends the sync, QC and cover lines to RUN.md.
Options: --pause SECONDS (default: RUN.md `pause:`, else 1.0), --target SECONDS|MIN-MAX (default: RUN.md `- target:`).

Standard library only. Every external command goes through `runner`, which tests replace.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from adopt_voice import fill_facts, load_facts  # noqa: E402
from build_index import layout, scene_ids  # noqa: E402

# A CSS blur drops the renderer from fast capture to screenshot capture (about 2x slower). `f.blur(tl, ...)` is
# the scenes' fade helper and is fine: only a blur() with a size is the filter.
BLUR = re.compile(r"(?<![\w.])blur\(\s*(?:\d|var\()")
# A tween callback that changes the page does not run on a seek, so a frame captured by a direct jump differs from
# the sequential one and fast capture's self-check fails (it then re-renders everything the slow way).
CALLBACK = re.compile(r"\bonUpdate\s*:")
STATE_HEAD = "## Finish state"
SYNC_LIMIT_S = 2.0


def run_command(cmd, cwd):
    # Measured on a 3-minute, 17-scene video: the parallel drawElement router renders it in 45 s against 1 m 55 s for
    # one worker, with the same frames (PSNR 72 dB) and the same self-checks.
    env = {"HF_DE_PARALLEL_ROUTER": "true", **os.environ}
    return subprocess.run(cmd, cwd=cwd, env=env).returncode


def probe_length(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                       check=True, capture_output=True, text=True)
    return float(r.stdout.strip())


# --- what changed since the last run ---------------------------------------------------------

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16] if Path(path).exists() else ""


def scene_state(p, scenes):
    """{scene id: {wav, html}, "_facts": hash}: what the scenes were made from."""
    state = {sid: {"wav": sha(p / v["path"]), "html": (p / "compositions" / f"{sid}.html").stat().st_mtime_ns}
             for sid, _, _, v in scenes}
    return {**state, "_facts": sha(p / "facts.json")}


def read_state(p):
    m = re.search(rf"^{STATE_HEAD}\nfinish-state: (\{{[^\n]*\}})$", (p / "RUN.md").read_text(), re.M) \
        if (p / "RUN.md").exists() else None
    return json.loads(m.group(1)) if m else {}


def write_state(p, state):
    run_md = p / "RUN.md"
    text = run_md.read_text() if run_md.exists() else ""
    block = f"{STATE_HEAD}\nfinish-state: {json.dumps(state, sort_keys=True)}\n"
    text = re.sub(rf"^{STATE_HEAD}\n.*?(?=^## |\Z)", "", text, flags=re.S | re.M)
    run_md.write_text(text.rstrip("\n") + "\n\n" + block)


def changed_scenes(old, new):
    everything = old.get("_facts") != new["_facts"]
    return [sid for sid in new if sid != "_facts" and (everything or old.get(sid) != new[sid])]


def load_scenes(p):
    meta = json.loads((p / "audio_meta.json").read_text())
    return layout(meta["voices"], scene_ids((p / "STORYBOARD.md").read_text()))


def sample_times(scenes, changed):
    """Seconds into the video of each changed scene's last 0.5 s, when its reveals are done. Earlier samples
    catch elements that have not appeared yet, and the layout check reports those as invisible text."""
    return [round(start + (d - 0.5 if d > 1 else d / 2), 2) for sid, start, d, _ in scenes if sid in changed]


# --- the steps -----------------------------------------------------------------------------------

class Finish:
    def __init__(self, p, runner, probe, pause_s, target):
        self.p, self.run, self.probe, self.pause_s, self.target = p, runner, probe, pause_s, target
        self.old_state = read_state(p)
        self.scenes, self.state, self.qc = None, None, "pass"

    def cmd(self, *argv):
        """A step that runs one command in the project folder; a non-zero exit fails it."""
        return lambda: None if self.run([str(a) for a in argv], self.p) == 0 else f"{argv[0]} exited non-zero"

    def py(self, script, *args):
        return self.cmd(sys.executable, "-I", HERE / script, self.p, *args)

    def hf(self, *args):
        return self.cmd("npx", "hyperframes", *args)

    def lint_fast_capture(self):
        files = [self.p / "index.html", *sorted((self.p / "compositions").glob("*.html"))]
        lines = [(f"{f.relative_to(self.p)}:{n}", line) for f in files if f.exists()
                 for n, line in enumerate(f.read_text().splitlines(), 1)]
        blur = [where for where, line in lines if BLUR.search(line)]
        callbacks = [where for where, line in lines if CALLBACK.search(line)]
        problems = (["filter blur() turns fast capture off; use opacity and y instead: " + ", ".join(blur)] if blur else []) \
            + (["onUpdate callbacks are not seek-safe and make fast capture fall back; build the effect from tweens of "
                "elements (see fx.type): " + ", ".join(callbacks)] if callbacks else [])
        return "; ".join(problems) or None

    def load(self):
        self.scenes = load_scenes(self.p)
        self.state = scene_state(self.p, self.scenes)

    def review_scenes(self):
        self.load()
        changed = changed_scenes(self.old_state, self.state)
        if not changed:
            print("no scene changed since the last finish run: nothing to look at")
            return None
        print("changed: " + ", ".join(changed))
        at = sample_times(self.scenes, changed)
        print("looking at: " + ", ".join(f"{sid} {t} s" for sid, t in zip(changed, at)))
        times = ",".join(map(str, at))
        error = self.hf("check", ".", "--at", times)()
        if error:
            return f"layout check failed (overflow or lint): {error}"
        error = self.hf("snapshot", ".", "--at", times, "--no-end", "-o", "review/snapshots")()
        if not error:
            print("stills: " + str(self.p / "review/snapshots"))
        return error

    def remember(self):
        self.load()
        write_state(self.p, self.state)

    def normalize(self):
        shutil.copy(self.p / "renders/video.raw.mp4", self.p / "renders/video.mp4")
        return self.py("qc_video.py", "--normalize")()

    def video_qc(self):
        """Records, never stops: a video off its target length is still a video, so the cover and RUN.md follow."""
        if self.py("qc_video.py", "--check", self.target)():
            self.qc = "fail (qc_video.py listed the problems above)"
        return None

    def cover(self):
        """The intro title on frame 0 (handoff.md: a moment about 60% through frame 1's voice)."""
        video, jpg, out = (self.p / "renders" / n for n in ("video.mp4", "cover.jpg", "video.cover.mp4"))
        t = round(self.scenes[0][2] * 0.6, 2)
        before = self.probe(video)
        steps = [("ffmpeg", "-y", "-loglevel", "error", "-ss", t, "-i", video, "-frames:v", 1, "-q:v", 2, jpg),
                 ("ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", jpg, "-filter_complex",
                  "[0:v][1:v]overlay=0:0:enable='eq(n,0)'[v]", "-map", "[v]", "-map", "0:a?", "-c:v", "libx264",
                  "-crf", 18, "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", out)]
        for step in steps:
            if self.run([str(a) for a in step], self.p) != 0:
                return "ffmpeg exited non-zero"
        out.replace(video)
        after = self.probe(video)
        self.cover_s = t
        return None if abs(after - before) < 0.2 else f"the cover changed the length: {before:.3f} s -> {after:.3f} s"

    def caption(self):
        """renders/share-copy.txt from renders/share-copy.template.txt, when the run has one: its {{facts}} follow facts.json."""
        template = self.p / "renders/share-copy.template.txt"
        if template.exists():
            (self.p / "renders/share-copy.txt").write_text(fill_facts(template.read_text(), load_facts(self.p)))

    def record(self):
        voice = sum(s[2] for s in self.scenes)
        mp4 = self.probe(self.p / "renders/video.mp4")
        diff = abs(mp4 - voice)
        note = f"  (above {SYNC_LIMIT_S:g} s: report it before calling the run done)" if diff > SYNC_LIMIT_S else ""
        with (self.p / "RUN.md").open("a") as f:
            f.write(f"\n## Final render {time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"- sync: voice total {voice:.3f} s, MP4 {mp4:.3f} s, difference {diff:.3f} s{note}\n"
                    f"- qc: {self.qc}\n- cover: {self.cover_s} s\n- video: renders/video.mp4\n")
        write_state(self.p, self.state)
        print(f"video: {self.p / 'renders/video.mp4'}  ({mp4:.1f} s, sync difference {diff:.3f} s)")
        return None

    def steps(self, mode):
        common = [("adopt", self.py("adopt_voice.py", "--pause", self.pause_s)),
                  ("voice check", self.py("adopt_voice.py", "--check")),
                  ("build index.html", self.py("build_index.py")),
                  ("fast-capture lint", self.lint_fast_capture)]
        if mode == "--review":
            return common + [("layout check and stills", self.review_scenes), ("remember", self.remember)]
        return common + [
            ("load scenes", self.load),
            ("render", self.hf("render", ".", "-o", "renders/video.raw.mp4")),
            ("loudness", self.normalize),
            ("video qc", self.video_qc),
            ("cover", self.cover),
            ("caption", self.caption),
            ("RUN.md", self.record),
        ]


def run_target(p):
    m = re.search(r"^\s*-\s*target\s*:\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)", (p / "RUN.md").read_text(), re.M) \
        if (p / "RUN.md").exists() else None
    return m.group(1) if m else None


def run_pause(p):
    m = re.search(r"^\s*-?\s*pause\s*:\s*(\d+(?:\.\d+)?)", (p / "RUN.md").read_text(), re.M) \
        if (p / "RUN.md").exists() else None
    return m.group(1) if m else "1.0"


def main(argv, runner=run_command, probe=probe_length):
    args = list(argv)
    opts = {}
    for flag in ("--pause", "--target"):
        if flag in args:
            i = args.index(flag)
            opts[flag] = args[i + 1] if i + 1 < len(args) else ""
            del args[i:i + 2]
    modes = [a for a in args if a in ("--review", "--final")]
    rest = [a for a in args if a not in modes]
    if len(modes) != 1 or len(rest) != 1 or "" in opts.values():
        print("usage: finish.py <project_dir> --review|--final [--pause SECONDS] [--target SECONDS|MIN-MAX]",
              file=sys.stderr)
        return 1
    p = Path(rest[0])
    target = opts.get("--target") or run_target(p)
    if modes[0] == "--final" and not target:
        print("finish: no target length: pass --target SECONDS (or MIN-MAX), or put '- target: ...' under Answers in RUN.md",
              file=sys.stderr)
        return 1
    f = Finish(p, runner, probe, opts.get("--pause") or run_pause(p), target)
    total = time.monotonic()
    for n, (name, step) in enumerate(f.steps(modes[0]), 1):
        print(f"[{n}] {name}", flush=True)
        started = time.monotonic()
        try:
            error = step()
        except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as e:
            error = f"{type(e).__name__}: {e}"
        print(f"    {name}: {time.monotonic() - started:.1f} s", flush=True)
        if error:
            print(f"finish: step '{name}' failed: {error}", file=sys.stderr)
            return 1
    print(f"finish {modes[0][2:]}: done in {time.monotonic() - total:.1f} s")
    if f.qc != "pass":
        print("finish: the video is made, but video qc failed; RUN.md records it", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
