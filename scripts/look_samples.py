#!/usr/bin/env python3
"""Render a one-frame sample of the intro scene in each proposed look.

    python3 -I look_samples.py <project_dir> [--look <folder name>]

Reads looks/<n>-<slug>/ in the run folder (each holds index.template.html and compositions/intro.html), the run's
audio_meta.json (the voice of Frame 1), facts.json (optional) and the hyperframes project files at the run root.
For each look it builds looks/<n>-<slug>/sample/ (Frame 1 only, with build_index.build) and renders it to
looks/<n>-<slug>/intro.mp4. A look that breaks fast capture (a CSS filter, an onUpdate, an unseeded Math.random) or cues a word the intro
lacks fails before any render. Writes nothing outside looks/. `--look` limits the run to one look folder.

Standard library only. The render goes through `render` (`runner`, an exit-code-only stand-in, replaces it in tests).
"""
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_index  # noqa: E402
import finish  # noqa: E402
from finish import fast_capture_problems  # noqa: E402

LOOK_NAME = re.compile(r"^\d+-[\w-]+$")
PROJECT_FILES = ("hyperframes.json", "meta.json", "package.json")
SAMPLE_STORYBOARD = "## Frame 1 — Intro\n- src: compositions/intro.html\n"
# The CLI words it "fast capture falls back to screenshot capture: <reason>"; older text said "falling back".
FALLBACK = re.compile(r"fall(?:s|ing) back to screenshot")
FALLBACK_NOTE = "slower render: fast capture fell back to screenshots"
USAGE = "usage: look_samples.py <project_dir> [--look <folder name>]"


def look_dirs(p):
    return sorted(d for d in (p / "looks").glob("*") if d.is_dir() and LOOK_NAME.match(d.name))


def intro_voice(p):
    """The run's Frame 1 voice entry, or None."""
    meta = p / "audio_meta.json"
    voices = json.loads(meta.read_text()).get("voices", []) if meta.exists() else []
    return next((v for v in voices if v.get("frame") == 1), None)


def look_problems(p, look):
    problems = [f"{look.name}: {name} not found" for name in ("index.template.html", "compositions/intro.html")
                if not (look / name).is_file()]
    return problems or fast_capture_problems([look / "index.template.html", look / "compositions/intro.html"], p)


def build_sample(p, look):
    """Recreate look/sample/ as a project of Frame 1 alone and build its index.html. Returns the folder."""
    sample = look / "sample"
    shutil.rmtree(sample, ignore_errors=True)
    v = intro_voice(p)
    (sample / "compositions").mkdir(parents=True)
    (sample / "build").mkdir()
    (sample / "STORYBOARD.md").write_text(SAMPLE_STORYBOARD)
    (sample / "audio_meta.json").write_text(json.dumps({"voices": [v]}))
    (sample / v["path"]).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(p / v["path"], sample / v["path"])
    shutil.copy(look / "compositions/intro.html", sample / "compositions/intro.html")
    shutil.copy(look / "index.template.html", sample / "build/index.template.html")
    for name in ("facts.json", *PROJECT_FILES):
        if (p / name).exists():
            shutil.copy(p / name, sample / name)
    if (p / "assets/fonts").is_dir():
        shutil.copytree(p / "assets/fonts", sample / "assets/fonts", dirs_exist_ok=True)
    build_index.build(sample)
    return sample


def main(argv, runner=None, render=None):
    render = render or ((lambda cmd, cwd: finish.run_command(cmd, cwd, capture=True)) if runner is None else (lambda cmd, cwd: (runner(cmd, cwd), "")))
    args = list(argv)
    only = None
    if "--look" in args:
        i = args.index("--look")
        only = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]
        if only is None:
            print(USAGE, file=sys.stderr)
            return 1
    if len(args) != 1:
        print(USAGE, file=sys.stderr)
        return 1
    p = Path(args[0]).absolute()  # the render runs in sample/, so its -o path must not depend on the cwd
    looks = [d for d in look_dirs(p) if only in (None, d.name)]
    problems = [] if looks else [f"no look folder {only or '<n>-<slug>'} under {p / 'looks'}"]
    v = intro_voice(p)
    if v is None:
        problems.append("audio_meta.json has no voice for frame 1 (or is missing)")
    elif not (p / v.get("path", "")).is_file():
        problems.append(f"voice file {v.get('path')} does not exist")
    for look in looks:
        problems += look_problems(p, look)
    samples = []
    if not problems:
        for look in looks:
            try:
                samples.append((look, build_sample(p, look)))
            except ValueError as e:
                problems.append(f"{look.name}: {e}")
    if not problems:
        for i, (look, sample) in enumerate(samples, 1):
            out = look / "intro.mp4"
            print(f"rendering {look.name} ({i}/{len(samples)})", flush=True)
            code, log = render(["npx", "hyperframes", "render", ".", "-o", str(out)], sample)
            if code != 0:
                problems.append(f"{look.name}: render failed")
            else:
                print(f"{look.name}: {out}" + (f"  ({FALLBACK_NOTE})" if FALLBACK.search(log) else ""))
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
