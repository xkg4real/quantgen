"""Packaging scope: regress against accidental private/research inclusion."""
import unittest
from tools.packaging.stage import allowed


class PackagingScopeTests(unittest.TestCase):
    def test_protected_inputs_are_excluded_before_open(self):
        for name in (".env", ".env.example", "docs/asset_expansion/cache/yf_SPY.csv",
                     "paper_live/E1.jsonl", "grokteam/result.json", "data/techfund/R3_TF_nodes.csv",
                     "core/frozen/anything.py", "core/holdout/test.py", "../config.py"):
            with self.subTest(name=name):
                self.assertFalse(allowed(name))

    def test_runtime_resources_and_status_are_explicit(self):
        for name in ("core/app_paths.py", "quantgen_desktop/app.py", "tools/status/snapshot.py", "assets/fonts/qg-interface.otf",
                     "assets/favicon.png", "assets/manifest.json", "assets/icons/icon-192.png",
                     "assets/branding/f1-symbol.svg", "core/calendars/data/MANIFEST.yaml",
                     "qa/research_status.json", "data/macro/series_registry.yaml"):
            with self.subTest(name=name):
                self.assertTrue(allowed(name))

    def test_unreviewed_artifacts_are_not_swept_up(self):
        for name in ("docs/random.json", "qa/new-private.json", "tools/nautilus/runner.py",
                     "assets/private.json",
                     "assets/private.key", "data/unknown.json", "core/new-ledger.jsonl"):
            self.assertFalse(allowed(name), name)


if __name__ == "__main__":
    unittest.main()
