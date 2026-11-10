#!/usr/bin/env python3
"""Download a Google Fonts family into the run and print the @font-face rules for the look's template.

    python3 -I fetch_font.py <project_dir> "<Family>" <weight> [<weight>...]

Saves the Latin .woff2 of each weight to <project_dir>/assets/fonts/<slug>-<weight>.woff2 and prints one
@font-face rule per weight, with a path relative to the project. Files that already exist are not fetched again.
A bundled family (HyperFrames' list, or Space Grotesk from this skill's assets/fonts/) needs no download. Only the
family name and the weights are sent to Google. Exits 1 when the family or weight does not exist or the network is
down; use a bundled family then.

Standard library only. Every network call goes through `fetch`, which tests replace.
"""
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BUNDLED = {"Inter", "Montserrat", "Outfit", "Nunito", "Oswald", "League Gothic", "Archivo Black", "Space Mono",
           "IBM Plex Mono", "JetBrains Mono", "EB Garamond", "Playfair Display", "Source Code Pro", "Noto Sans JP",
           "Roboto", "Open Sans", "Lato", "Poppins", "Space Grotesk"}
# Google serves .woff2 only to a browser User-Agent; this one names no user.
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0 Safari/537.36")
USAGE = 'usage: fetch_font.py <project_dir> "<Family>" <weight> [<weight>...]'
SUBSET_BLOCK = re.compile(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*\{(.*?)\}", re.S)


def http_get(url, headers):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        return response.read()


def slug(family):
    return re.sub(r"[^a-z0-9]+", "-", family.lower()).strip("-")


def latin_urls(css):
    """{weight: url of the first src} for the blocks Google labels /* latin */."""
    urls = {}
    for subset, body in SUBSET_BLOCK.findall(css):
        weight, src = re.search(r"font-weight:\s*(\d+)", body), re.search(r"url\(([^)]+)\)", body)
        if subset == "latin" and weight and src:
            urls[weight.group(1)] = src.group(1).strip("'\"")
    return urls


def main(argv, fetch=http_get):
    if len(argv) < 3:
        print(USAGE, file=sys.stderr)
        return 1
    if not all(w.isdigit() for w in argv[2:]):
        print(USAGE, file=sys.stderr)
        return 1
    p, family = Path(argv[0]), argv[1]
    weights = sorted(set(argv[2:]), key=int)  # the css2 API wants weights ascending, without repeats
    if family in BUNDLED:
        print(f'"{family}" is bundled; no download needed')
        return 0
    headers = {"User-Agent": USER_AGENT}
    query = f"{urllib.parse.quote_plus(family)}:wght@{';'.join(weights)}"
    try:
        css = fetch(f"https://fonts.googleapis.com/css2?family={query}&display=swap", headers).decode()
        urls = latin_urls(css)
        missing = [w for w in weights if w not in urls]
        if missing:
            print(f"no latin file for weight {missing[0]}", file=sys.stderr)
            return 1
        fonts = p / "assets/fonts"
        for w in weights:
            target = fonts / f"{slug(family)}-{w}.woff2"
            if not target.exists():
                data = fetch(urls[w], headers)
                fonts.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    except OSError as e:
        if isinstance(e, urllib.error.HTTPError) and e.code == 400:
            print(f'Google Fonts has no family "{family}" at weights {" ".join(weights)}', file=sys.stderr)
            return 1
        print(f"could not reach Google Fonts ({getattr(e, 'reason', e)}); use a bundled family instead", file=sys.stderr)
        return 1
    for w in weights:
        print(f'@font-face {{ font-family: "{family}"; src: url("assets/fonts/{slug(family)}-{w}.woff2") '
              f'format("woff2"); font-weight: {w}; }}')
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
