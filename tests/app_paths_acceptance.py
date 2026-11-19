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
        (self.home / ".nextgen").mkdir()
        self.assertEqual(app_paths.user_data_dir(home=self.home, env={"QUANTGEN_DATA_DIR": str(self.home / "p"),
                                                                      "FLET_APP_STORAGE_DATA": str(self.home / "f")}),
                         self.home / "p")
        self.assertEqual(app_paths.user_data_dir(home=self.home, env={"FLET_APP_STORAGE_DATA": str(self.home / "f")}),
                         self.home / "f")
        (self.home / ".nextgen").rmdir()
        app_paths.user_data_dir(home=self.home, env={}, platform="linux")
        self.assertEqual(list(self.home.iterdir()), [])

    def test_a_legacy_file_is_not_mistaken_for_the_folder(self):
        (self.home / ".nextgen").write_text("", encoding="utf-8")
        self.assertEqual(app_paths.user_data_dir(home=self.home, env={}, platform="linux"),
                         self.home / ".local" / "share" / "quantgen")


class DataLocationAndMigrationTests(unittest.TestCase):
    """OS-F2: where the data lives and the consent-only move from ~/.nextgen; only temporary homes are used."""
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.home = Path(folder.name)
        self.env = {"XDG_DATA_HOME": str(self.home / "xdg")}

    def where(self, **env):
        return app_paths.data_location(home=self.home, env={**self.env, **env}, platform="linux")

    def test_sources(self):
        self.assertEqual(self.where().source, "platform")
        self.assertFalse(self.where().can_migrate)
        (self.home / ".nextgen").mkdir()
        where = self.where()
        self.assertEqual((where.source, where.path, where.platform_path, where.can_migrate),
                         ("legacy", self.home / ".nextgen", self.home / "xdg" / "quantgen", True))
        self.assertEqual(self.where(QUANTGEN_DATA_DIR=str(self.home / "o")).source, "override")
        self.assertEqual(self.where(FLET_APP_STORAGE_DATA=str(self.home / "f")).source, "flet")

    def test_describing_lists_and_creates_nothing(self):
        legacy = self.home / ".nextgen"
        legacy.mkdir(); (legacy / "kis_token.json").write_text("t", encoding="utf-8")
        before = sorted(p.relative_to(self.home) for p in self.home.rglob("*"))
        self.where()
        self.assertEqual(sorted(p.relative_to(self.home) for p in self.home.rglob("*")), before)

    def test_migration_needs_consent(self):
        (self.home / ".nextgen").mkdir()
        for confirmed in (False, None, "yes", 1):
            with self.subTest(confirmed=confirmed), self.assertRaises(app_paths.MigrationRefused):
                app_paths.migrate_legacy_data(confirmed=confirmed, home=self.home, env=self.env, platform="linux")
        self.assertTrue((self.home / ".nextgen").is_dir())

    def test_migration_moves_once_and_never_merges(self):
        legacy = self.home / ".nextgen"
        (legacy / "trading").mkdir(parents=True)
        (legacy / "kis_token.json").write_text("token", encoding="utf-8")
        (legacy / "trading" / "rules.json").write_text("{}", encoding="utf-8")
        target = app_paths.migrate_legacy_data(confirmed=True, home=self.home, env=self.env, platform="linux")
        self.assertEqual(target, self.home / "xdg" / "quantgen")
        self.assertFalse(legacy.exists())
        self.assertEqual((target / "kis_token.json").read_text(encoding="utf-8"), "token")
        self.assertEqual((target / "trading" / "rules.json").read_text(encoding="utf-8"), "{}")
        self.assertEqual(app_paths.user_data_dir(home=self.home, env=self.env, platform="linux"), target)
        with self.assertRaises(app_paths.MigrationRefused):   # nothing left to move
            app_paths.migrate_legacy_data(confirmed=True, home=self.home, env=self.env, platform="linux")
        legacy.mkdir()                                      # e.g. TRADEGEN made it again: never merged
        with self.assertRaises(app_paths.MigrationRefused):
            app_paths.migrate_legacy_data(confirmed=True, home=self.home, env=self.env, platform="linux")
        self.assertEqual((target / "kis_token.json").read_text(encoding="utf-8"), "token")

    def test_override_is_never_migrated(self):
        (self.home / ".nextgen").mkdir()
        with self.assertRaises(app_paths.MigrationRefused):
            app_paths.migrate_legacy_data(confirmed=True, home=self.home, platform="linux",
                                          env={**self.env, "QUANTGEN_DATA_DIR": str(self.home / "o")})


class WritersFollowTheDataFolderTests(unittest.TestCase):
    """config.py, kis_client and opendart_client take their paths from core.app_paths (OS-F2), computed at each use."""
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.data = Path(folder.name) / "data"

    def test_paths(self):
        import os
        import dotenv
        with patch.object(dotenv, "load_dotenv", return_value=False):   # never reads .env
            import config
            from data.krx import kis_client, opendart_client
        keep = {k: os.environ.pop(k) for k in ("NEXTGEN_TRADING_DIR", "QUANTGEN_MACRO_DIR", "NEXTGEN_FICC_CACHE")
                if k in os.environ}
        self.addCleanup(os.environ.update, keep)
        with patch.dict(os.environ, {"QUANTGEN_DATA_DIR": str(self.data)}), \
                patch.object(kis_client, "_TOKEN_PATH", None), patch.object(opendart_client, "_CACHE_PATH", None):
            self.assertEqual(config.trading_dir(), self.data / "trading")
            self.assertEqual(config.macro_dir(), self.data / "macro")
            self.assertEqual(config.ficc_cache_dir(), self.data / "ficc_cache")
            self.assertEqual(kis_client._token_path(), self.data / "kis_token.json")
            self.assertEqual(opendart_client._cache_path(), self.data / "dart_corp_codes.json")
        self.assertFalse(self.data.exists())   # computing a path creates nothing
        with patch.dict(os.environ, {"NEXTGEN_TRADING_DIR": str(self.data / "t")}):
            self.assertEqual(config.trading_dir(), self.data / "t")   # the old overrides still win


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
