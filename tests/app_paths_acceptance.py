"""core.app_paths (OS-P0-c): packaged-app root and per-user data folder, computed without touching the real home."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from core import app_paths


class UserDataDirTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.home = Path(folder.name)

    def test_existing_legacy_folder_wins_on_every_platform(self):
        (self.home / ".nextgen").mkdir()
        for platform in ("win32", "darwin", "linux"):
            with self.subTest(platform=platform):
                self.assertEqual(app_paths.user_data_dir(home=self.home, env={"LOCALAPPDATA": "C:/x"}, platform=platform),
                                 self.home / ".nextgen")

    def test_new_install_uses_the_platform_folder(self):
        self.assertEqual(app_paths.user_data_dir(home=self.home, env={"LOCALAPPDATA": str(self.home / "L")}, platform="win32"),
                         self.home / "L" / "QUANTGEN")
        self.assertEqual(app_paths.user_data_dir(home=self.home, env={}, platform="win32"),
                         self.home / "AppData" / "Local" / "QUANTGEN")
        self.assertEqual(app_paths.user_data_dir(home=self.home, env={}, platform="darwin"),
                         self.home / "Library" / "Application Support" / "QUANTGEN")
        self.assertEqual(app_paths.user_data_dir(home=self.home, env={"XDG_DATA_HOME": str(self.home / "x")}, platform="linux"),
                         self.home / "x" / "quantgen")
        self.assertEqual(app_paths.user_data_dir(home=self.home, env={}, platform="linux"),
                         self.home / ".local" / "share" / "quantgen")

    def test_override_and_nothing_is_created(self):
        self.assertEqual(app_paths.user_data_dir(home=self.home, env={"QG_USER_DATA_DIR": str(self.home / "p")}),
                         self.home / "p")
        app_paths.user_data_dir(home=self.home, env={}, platform="linux")
        self.assertEqual(list(self.home.iterdir()), [])

    def test_a_legacy_file_is_not_mistaken_for_the_folder(self):
        (self.home / ".nextgen").write_text("", encoding="utf-8")
        self.assertEqual(app_paths.user_data_dir(home=self.home, env={}, platform="linux"),
                         self.home / ".local" / "share" / "quantgen")


class ApplicationRootTests(unittest.TestCase):
    def test_source_checkout_and_packaged_app(self):
        self.assertFalse(app_paths.is_frozen())
        self.assertEqual(app_paths.application_root(), Path(app_paths.__file__).resolve().parents[1])
        with tempfile.TemporaryDirectory() as bundle, patch.object(sys, "frozen", True, create=True), \
                patch.object(sys, "_MEIPASS", bundle, create=True):
            self.assertTrue(app_paths.is_frozen())
            self.assertEqual(app_paths.application_root(), Path(bundle))
            self.assertEqual(app_paths.assets_directory(), str(Path(bundle) / "assets"))


if __name__ == "__main__":
    unittest.main()
