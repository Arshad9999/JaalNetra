"""Check local navigation and assets without relying on external websites."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import unittest

ROOT = Path(__file__).resolve().parents[1]


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag in {"a", "link", "script", "img", "source", "video", "iframe"}:
            for attribute in ("href", "src", "poster"):
                if attribute in attrs:
                    self.references.append((tag, attribute, attrs[attribute]))


class StaticSiteTests(unittest.TestCase):
    def test_local_page_links_and_resources_exist(self):
        for page in ROOT.glob("*.html"):
            parser = References()
            parser.feed(page.read_text())
            for tag, attribute, value in parser.references:
                with self.subTest(page=page.name, tag=tag, attribute=attribute, value=value[:120]):
                    url = urlsplit(value)
                    if url.scheme or url.netloc or not url.path:
                        continue
                    target = (ROOT if url.path.startswith("/") else page.parent) / unquote(url.path.lstrip("/"))
                    self.assertTrue(target.is_file(), f"Missing local target: {value}")

    def test_media_and_script_sources_are_not_empty(self):
        for page in ROOT.glob("*.html"):
            parser = References()
            parser.feed(page.read_text())
            for tag, attribute, value in parser.references:
                if tag in {"source", "script", "img", "iframe"} and attribute == "src":
                    with self.subTest(page=page.name, tag=tag):
                        self.assertTrue(value.strip(), "Empty source requests the page instead of an asset")

    def test_root_entry_points_to_home(self):
        page = ROOT / "index.html"
        self.assertTrue(page.is_file())
        parser = References()
        parser.feed(page.read_text())
        self.assertIn(("a", "href", "home.html"), parser.references)


if __name__ == "__main__":
    unittest.main()
