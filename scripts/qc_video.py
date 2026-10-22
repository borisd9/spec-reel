#!/usr/bin/env python3
"""Final checks on the rendered MP4.

    python3 -I qc_video.py <project_dir> --normalize         # renders/video.mp4 loudness to -16 LUFS, video copied
    python3 -I qc_video.py <project_dir> --check <seconds>   # format, audio, black spans and length against the target

Standard library only. ffprobe and ffmpeg are reached through three small functions that tests replace.
"""
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"
BLACKDETECT = "blackdetect=d=0.5:pix_th=0.10"
SIZE = (1920, 1080)
LENGTH_TOLERANCE = 0.12
BLACK_RE = re.compile(r"black_start:([\d.]+)\s+black_end:([\d.]+)")


# --- the three replaceable external calls -------------------------------------------------

def probe(video):
    """ffprobe -> {"streams": [{codec_type, codec_name, pix_fmt, width, height}], "duration": seconds}."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,codec_name,pix_fmt,width,height:format=duration",
                        "-of", "json", str(video)], check=True, capture_output=True, text=True)
    data = json.loads(r.stdout)
    return {"streams": data.get("streams", []), "duration": float(data["format"]["duration"])}


def black_spans(video):
    """blackdetect -> [(start, end)] of every black span of at least 0.5 s."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf", BLACKDETECT,
                        "-an", "-f", "null", "-"], check=True, capture_output=True, text=True)
    return [(float(a), float(b)) for a, b in BLACK_RE.findall(r.stderr)]


def loudnorm(src, dst):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-c:v", "copy", "-af", LOUDNORM,
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(dst)],
                   check=True, capture_output=True, text=True)


# --- modes ---------------------------------------------------------------------------------

def fail(lines):
    print("\n".join(lines), file=sys.stderr)
    return 1


def problems_of(video, target_s, probe, black_spans):
    info = probe(video)
    video_stream = next((s for s in info["streams"] if s.get("codec_type") == "video"), {})
    problems = []
    if video_stream.get("codec_name") != "h264":
        problems.append(f"video codec is {video_stream.get('codec_name')}, not h264")
    if video_stream.get("pix_fmt") != "yuv420p":
        problems.append(f"pixel format is {video_stream.get('pix_fmt')}, not yuv420p")
    if (video_stream.get("width"), video_stream.get("height")) != SIZE:
        problems.append(f"size is {video_stream.get('width')}x{video_stream.get('height')}, not {SIZE[0]}x{SIZE[1]}")
    if not any(s.get("codec_type") == "audio" for s in info["streams"]):
        problems.append("no audio stream")
    problems += [f"black from {a:.1f}s to {b:.1f}s" for a, b in black_spans(video)]
    if abs(info["duration"] - target_s) > LENGTH_TOLERANCE * target_s:
        problems.append(f"length {info['duration']:.1f}s is outside {target_s:g}s plus or minus "
                        f"{LENGTH_TOLERANCE:.0%}")
    return problems


def normalize(p, loudnorm):
    video = p / "renders/video.mp4"
    if not video.is_file():
        return fail([f"{video} not found"])
    tmp = video.with_name("video.norm.mp4")
    try:
        loudnorm(video, tmp)
    except Exception as e:  # ffmpeg failed: keep the original
        tmp.unlink(missing_ok=True)
        return fail([f"loudness normalization failed: {e}"])
    os.replace(tmp, video)
    print(f"normalized {video} to -16 LUFS")
    return 0


def check(p, target_s, probe, black_spans):
    video = p / "renders/video.mp4"
    if not video.is_file():
        return fail([f"{video} not found"])
    problems = problems_of(video, target_s, probe, black_spans)
    if problems:
        return fail(problems)
    print("qc: pass")
    return 0


USAGE = "usage: qc_video.py <project_dir> (--normalize | --check TARGET_SECONDS)"


def main(argv, probe=probe, black_spans=black_spans, loudnorm=loudnorm):
    argv = list(argv)
    if len(argv) == 2 and argv[1] == "--normalize":
        return normalize(Path(argv[0]), loudnorm)
    if len(argv) == 3 and argv[1] == "--check":
        try:
            target_s = float(argv[2])
        except ValueError:
            return fail([USAGE])
        if not math.isfinite(target_s) or target_s <= 0:
            return fail([USAGE])
        return check(Path(argv[0]), target_s, probe, black_spans)
    return fail([USAGE])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
