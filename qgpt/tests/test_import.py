"""The skeleton imports, and it imports nothing outside the standard library."""
import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import quantgpt  # noqa: E402


class ImportTests(unittest.TestCase):
    def test_every_subpackage_imports(self):
        for name in quantgpt.SUBPACKAGES:
            with self.subTest(name=name):
                importlib.import_module(f"quantgpt.{name}")

    def test_no_host_application_or_validation_library_is_imported(self):
        for name in quantgpt.SUBPACKAGES:
            importlib.import_module(f"quantgpt.{name}")
        for banned in ("core", "quantgen_desktop", "ui", "config", "jsonschema", "pydantic"):
            with self.subTest(banned=banned):
                self.assertNotIn(banned, sys.modules)

    def test_no_weight_files_are_tracked_here(self):
        suffixes = {".safetensors", ".bin", ".gguf", ".onnx", ".xml", ".pt", ".pth", ".ckpt"}
        found = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix in suffixes]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
