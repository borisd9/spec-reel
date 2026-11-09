"""Tests for fetch_font.py: Latin-only downloads into the run, bundled families skipped, clean failures."""
import contextlib
import io
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_font as ff  # noqa: E402

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def block(subset, weight, name):
    return (f"/* {subset} */\n@font-face {{\n  font-family: 'Press Start 2P';\n  font-style: normal;\n"
            f"  font-weight: {weight};\n  font-display: swap;\n"
            f"  src: url(https://fonts.gstatic.com/s/x/{name}.woff2) format('woff2');\n"
            f"  unicode-range: U+0000-00FF;\n}}\n")


CSS = "".join(block(s, w, f"{s}{w}") for w in (400, 700) for s in ("cyrillic", "latin"))


class FetchFontTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.p = Path(self._td.name)
        self.calls = []
        self.error = None
        self.css = CSS

    def fetch(self, url, headers):
        self.calls.append((url, headers))
        if self.error:
            raise self.error
        return self.css.encode() if "googleapis" in url else b"font:" + url.rsplit("/", 1)[1].encode()

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ff.main([str(self.p), *args], fetch=self.fetch)
        return code, out.getvalue(), err.getvalue()

    def test_only_latin_blocks_are_downloaded(self):
        code, out, _ = self.run_main("Press Start 2P", "400", "700")
        self.assertEqual(code, 0)
        self.assertEqual(len(self.calls), 3)
        fonts = self.p / "assets/fonts"
        self.assertEqual((fonts / "press-start-2p-400.woff2").read_bytes(), b"font:latin400.woff2")
        self.assertEqual((fonts / "press-start-2p-700.woff2").read_bytes(), b"font:latin700.woff2")
        self.assertEqual(out.splitlines(), [
            '@font-face { font-family: "Press Start 2P"; src: url("assets/fonts/press-start-2p-%s.woff2") '
            'format("woff2"); font-weight: %s; }' % (w, w) for w in ("400", "700")])

    def test_css_request_uses_the_browser_user_agent(self):
        self.run_main("Press Start 2P", "400")
        url, headers = self.calls[0]
        self.assertIn("family=Press+Start+2P:wght@400", url)
        self.assertEqual(headers["User-Agent"], UA)

    def test_bundled_family_needs_no_download(self):
        code, out, _ = self.run_main("Lato", "400")
        self.assertEqual(code, 0)
        self.assertEqual(self.calls, [])
        self.assertIn('"Lato" is bundled; no download needed', out)
        self.assertNotIn("@font-face", out)

    def test_unknown_family_fails_cleanly(self):
        self.error = urllib.error.HTTPError("u", 400, "Bad Request", {}, None)
        code, _, err = self.run_main("Nope Sans", "400")
        self.assertEqual(code, 1)
        self.assertIn('Google Fonts has no family "Nope Sans" at weights 400', err)
        self.assertFalse(list((self.p / "assets/fonts").glob("*")) if (self.p / "assets/fonts").exists() else [])

    def test_network_error_suggests_a_bundled_family(self):
        self.error = urllib.error.URLError("offline")
        code, _, err = self.run_main("Press Start 2P", "400")
        self.assertEqual(code, 1)
        self.assertIn("offline", err)
        self.assertIn("bundled family", err)

    def test_existing_files_are_not_fetched_again(self):
        _, first, _ = self.run_main("Press Start 2P", "400", "700")
        self.calls.clear()
        _, second, _ = self.run_main("Press Start 2P", "400", "700")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(first, second)

    def test_weight_without_a_latin_block_fails(self):
        self.css = block("cyrillic", 400, "c400")
        code, _, err = self.run_main("Press Start 2P", "400")
        self.assertEqual(code, 1)
        self.assertIn("no latin file for weight 400", err)

    def test_usage(self):
        code, _, err = self.run_main("Press Start 2P")
        self.assertEqual(code, 1)
        self.assertIn("usage: fetch_font.py", err)

    def test_slug(self):
        self.assertEqual(ff.slug("Press Start 2P"), "press-start-2p")
        self.assertEqual(ff.slug("Noto Serif JP"), "noto-serif-jp")


if __name__ == "__main__":
    unittest.main()
