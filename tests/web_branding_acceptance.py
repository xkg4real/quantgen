"""Serve branded browser resources without importing the research application."""
from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import urlsplit

import flet_web.fastapi
from fastapi.testclient import TestClient

ASSETS = Path(__file__).resolve().parents[1] / "assets"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = {}

    def handle_starttag(self, tag, attrs):
        if tag == "link":
            values = dict(attrs)
            self.links[values.get("rel")] = values.get("href")


class WebBrandingTests(unittest.TestCase):
    def test_served_icons_and_manifest_use_project_assets(self):
        app = flet_web.fastapi.FastAPI()
        app.mount("/", flet_web.fastapi.app(lambda page: None, assets_dir=str(ASSETS)))
        with TestClient(app) as client:
            page = client.get("/")
            self.assertEqual(page.status_code, 200)
            links = Links()
            links.feed(page.text)
            self.assertEqual(links.links["icon"], "favicon.png")
            self.assertEqual(links.links["apple-touch-icon"], "icons/apple-touch-icon-192.png")
            manifest = client.get(links.links["manifest"])
            self.assertEqual(manifest.status_code, 200)
            data = manifest.json()
            self.assertEqual(data["name"], "QUANTGEN")
            self.assertEqual(data["theme_color"], "#194C40")
            resources = [links.links["icon"], links.links["apple-touch-icon"]]
            resources += [icon["src"] for icon in data["icons"]]
            for path in resources:
                with self.subTest(path=path):
                    self.assertFalse(urlsplit(path).netloc)
                    response = client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn("image/png", response.headers["content-type"])
                    self.assertEqual(response.content, (ASSETS / path).read_bytes())
            self.assertEqual(client.get("/missing-brand.png").status_code, 404)


if __name__ == "__main__":
    unittest.main()
