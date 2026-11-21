"""core.app_paths (OS-P0-c): packaged-app root and per-user data folder, computed without touching the real home."""
import errno
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

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

    def test_destination_appearing_after_the_precheck_is_not_merged_or_nested(self):
        legacy = self.home / ".nextgen"
        legacy.mkdir()
        (legacy / "kis_token.json").write_text("synthetic-token", encoding="utf-8")
        target = self.home / "xdg" / "quantgen"
        mkdir = Path.mkdir

        def destination_appears(folder, *args, **kwargs):
            result = mkdir(folder, *args, **kwargs)
            if folder == target.parent and not target.exists():
                mkdir(target)
                (target / "other-app.txt").write_text("keep", encoding="utf-8")
            return result

        with patch.object(Path, "mkdir", new=destination_appears):
            with self.assertRaises(app_paths.MigrationRefused):
                app_paths.migrate_legacy_data(confirmed=True, home=self.home, env=self.env, platform="linux")
        self.assertEqual((legacy / "kis_token.json").read_text(encoding="utf-8"), "synthetic-token")
        self.assertEqual((target / "other-app.txt").read_text(encoding="utf-8"), "keep")
        self.assertFalse((target / ".nextgen").exists())

    def test_marker_failure_does_not_move_the_legacy_token(self):
        legacy = self.home / ".nextgen"
        legacy.mkdir()
        (legacy / "kis_token.json").write_text("synthetic-token", encoding="utf-8")
        target = self.home / "xdg" / "quantgen"
        with patch.object(app_paths, "_stamp", side_effect=PermissionError("synthetic marker failure")):
            with self.assertRaises((app_paths.MigrationRefused, OSError)):
                app_paths.migrate_legacy_data(confirmed=True, home=self.home, env=self.env, platform="linux")
        self.assertEqual((legacy / "kis_token.json").read_text(encoding="utf-8"), "synthetic-token")
        self.assertFalse(target.exists())

    def test_an_empty_destination_appearing_after_the_precheck_is_not_replaced(self):
        legacy = self.home / ".nextgen"
        legacy.mkdir()
        (legacy / "kis_token.json").write_text("synthetic-token", encoding="utf-8")
        target = self.home / "xdg" / "quantgen"
        stamp = app_paths._stamp

        def destination_appears(folder):
            stamp(folder)
            target.mkdir()

        with patch.object(app_paths, "_stamp", side_effect=destination_appears):
            with self.assertRaises(app_paths.MigrationRefused):
                app_paths.migrate_legacy_data(confirmed=True, home=self.home, env=self.env, platform="linux")
        self.assertEqual((legacy / "kis_token.json").read_text(encoding="utf-8"), "synthetic-token")
        self.assertEqual(list(target.iterdir()), [])

    def test_exdev_unsupported_and_permission_errors_never_copy_or_delete(self):
        legacy = self.home / ".nextgen"
        legacy.mkdir()
        (legacy / "kis_token.json").write_text("synthetic-token", encoding="utf-8")
        target = self.home / "xdg" / "quantgen"
        for error in (errno.EXDEV, errno.ENOSYS, errno.EACCES):
            with self.subTest(error=error), \
                    patch.object(app_paths, "_rename_no_replace", side_effect=OSError(error, "synthetic refusal")):
                with self.assertRaises(app_paths.MigrationRefused) as caught:
                    app_paths.migrate_legacy_data(confirmed=True, home=self.home, env=self.env, platform="linux")
                self.assertEqual(caught.exception.__cause__.errno, error)
                self.assertEqual((legacy / "kis_token.json").read_text(encoding="utf-8"), "synthetic-token")
                self.assertFalse(target.exists())
                self.assertTrue((legacy / app_paths.DATA_MARKER).is_file())  # documented harmless residue

    def test_a_directory_marker_is_refused_before_the_legacy_folder_moves(self):
        legacy = self.home / ".nextgen"
        legacy.mkdir()
        (legacy / app_paths.DATA_MARKER).mkdir()
        (legacy / "kis_token.json").write_text("synthetic-token", encoding="utf-8")
        with self.assertRaises(app_paths.MigrationRefused):
            app_paths.migrate_legacy_data(confirmed=True, home=self.home, env=self.env, platform="linux")
        self.assertEqual((legacy / "kis_token.json").read_text(encoding="utf-8"), "synthetic-token")
        self.assertFalse((self.home / "xdg" / "quantgen").exists())

    def test_a_legacy_symlink_is_not_advertised_or_moved_as_a_migration(self):
        elsewhere = self.home / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "kis_token.json").write_text("synthetic-token", encoding="utf-8")
        legacy = self.home / ".nextgen"
        try:
            legacy.symlink_to(elsewhere, target_is_directory=True)
        except OSError:
            self.skipTest("this host does not permit directory symlinks")
        self.assertFalse(self.where().can_migrate)
        with self.assertRaises(app_paths.MigrationRefused):
            app_paths.migrate_legacy_data(confirmed=True, home=self.home, env=self.env, platform="linux")
        self.assertTrue(legacy.is_symlink())
        self.assertEqual((elsewhere / "kis_token.json").read_text(encoding="utf-8"), "synthetic-token")
        self.assertFalse((elsewhere / app_paths.DATA_MARKER).exists())


class ExclusiveRenameTests(unittest.TestCase):
    """Check the native operation contracts without claiming the mocked host APIs ran on that OS."""
    def setUp(self):
        self.source, self.target = Path("synthetic-source"), Path("synthetic-target")

    def test_posix_native_calls_require_no_replace_and_report_native_errors(self):
        for platform, symbol, expected in (
                ("linux", "renameat2", (-100, os.fsencode(self.source), -100, os.fsencode(self.target), 1)),
                ("darwin", "renamex_np", (os.fsencode(self.source), os.fsencode(self.target), 4))):
            for result in (0, -1):
                rename = Mock(return_value=result)
                with self.subTest(platform=platform, result=result), patch.object(os, "name", "posix"), \
                        patch.object(sys, "platform", platform), \
                        patch.object(app_paths.ctypes, "CDLL", return_value=SimpleNamespace(**{symbol: rename})), \
                        patch.object(app_paths.ctypes, "get_errno", return_value=errno.EEXIST):
                    if result:
                        with self.assertRaises(OSError) as caught:
                            app_paths._rename_no_replace(self.source, self.target)
                        self.assertEqual(caught.exception.errno, errno.EEXIST)
                    else:
                        app_paths._rename_no_replace(self.source, self.target)
                    rename.assert_called_once_with(*expected)

    def test_missing_native_symbol_and_unsupported_platform_are_refused(self):
        for platform in ("linux", "darwin", "unsupported-os"):
            with self.subTest(platform=platform), patch.object(os, "name", "posix"), \
                    patch.object(sys, "platform", platform), \
                    patch.object(app_paths.ctypes, "CDLL", return_value=SimpleNamespace()):
                with self.assertRaises(OSError) as caught:
                    app_paths._rename_no_replace(self.source, self.target)
                self.assertEqual(caught.exception.errno, errno.ENOSYS)

    def test_windows_uses_its_no_replace_rename_without_a_posix_fallback(self):
        with patch.object(os, "name", "nt"), patch.object(os, "rename") as rename, \
                patch.object(app_paths.ctypes, "CDLL", side_effect=AssertionError("unexpected POSIX API")):
            app_paths._rename_no_replace(self.source, self.target)
            rename.assert_called_once_with(self.source, self.target)


class MarkerKeepsTheChosenFolderTests(unittest.TestCase):
    """Main decision 2026-11-20: QUANTGEN's marker in the platform folder decides before ~/.nextgen."""
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.home = Path(folder.name)
        self.env = {"XDG_DATA_HOME": str(self.home / "xdg")}
        self.platform_dir = self.home / "xdg" / "quantgen"
        self.legacy = self.home / ".nextgen"

    def resolve(self):
        return app_paths.user_data_dir(home=self.home, env=self.env, platform="linux")

    def ensure(self):
        with patch.dict("os.environ", self.env, clear=True), patch.object(Path, "home", return_value=self.home), \
                patch.object(sys, "platform", "linux"):
            return app_paths.ensure_user_data_dir()

    def test_a_new_user_gets_the_platform_folder_with_the_marker(self):
        self.assertEqual(self.ensure(), self.platform_dir)
        marker = json.loads((self.platform_dir / app_paths.DATA_MARKER).read_text(encoding="utf-8"))
        self.assertEqual(sorted(marker), ["app", "created", "format"])
        self.assertEqual((marker["app"], marker["format"]), ("QUANTGEN", 1))
        if os.name == "posix":  # Windows stat does not expose POSIX directory permission bits.
            self.assertEqual(self.platform_dir.stat().st_mode & 0o777, 0o700)

    def test_b_a_later_nextgen_does_not_move_a_new_user(self):
        self.ensure()
        self.legacy.mkdir()                                     # e.g. TRADEGEN installed afterwards
        self.assertEqual(self.resolve(), self.platform_dir)
        self.assertEqual(app_paths.data_location(home=self.home, env=self.env, platform="linux").source, "platform")

    def test_path_getters_do_not_stamp_a_folder_made_without_preparation(self):
        (self.platform_dir / "trading").mkdir(parents=True)
        self.assertEqual(self.resolve(), self.platform_dir)
        with patch.dict(os.environ, self.env, clear=True), patch.object(Path, "home", return_value=self.home), \
                patch.object(sys, "platform", "linux"):
            self.assertEqual(app_paths.user_data_path("trading"), self.platform_dir / "trading")
        self.assertFalse((self.platform_dir / app_paths.DATA_MARKER).exists())
        self.ensure()  # application startup or a standalone writer explicitly prepares before its first write
        self.legacy.mkdir()
        self.assertEqual(self.resolve(), self.platform_dir)

    def test_preparation_pins_the_platform_choice_during_a_legacy_creation_race(self):
        mkdir = Path.mkdir

        def legacy_appears(folder, *args, **kwargs):
            result = mkdir(folder, *args, **kwargs)
            if folder == self.platform_dir and not self.legacy.exists():
                mkdir(self.legacy)
            return result

        with patch.object(Path, "mkdir", new=legacy_appears):
            self.assertEqual(self.ensure(), self.platform_dir)
        self.assertTrue(self.legacy.is_dir())
        self.assertTrue((self.platform_dir / app_paths.DATA_MARKER).is_file())
        self.assertEqual(self.resolve(), self.platform_dir)

    def test_bad_existing_markers_refuse_preparation_without_overwriting_them(self):
        self.platform_dir.mkdir(parents=True)
        marker = self.platform_dir / app_paths.DATA_MARKER
        for text in ("", "not-json", '{"app":"OTHER","format":1,"created":"2026-01-01"}',
                     '{"app":"QUANTGEN","format":2,"created":"2026-01-01"}',
                     '{"app":"QUANTGEN","format":true,"created":"2026-01-01"}',
                     '{"app":"QUANTGEN","format":1,"created":"not-a-date"}'):
            marker.write_text(text, encoding="utf-8")
            with self.subTest(text=text), self.assertRaises(OSError):
                self.ensure()
            self.assertEqual(marker.read_text(encoding="utf-8"), text)

    def test_c_an_existing_nextgen_user_stays(self):
        self.legacy.mkdir()
        self.assertEqual(self.resolve(), self.legacy)
        self.assertEqual(self.ensure(), self.legacy)
        self.assertFalse(self.platform_dir.exists())

    def test_d_an_unmarked_platform_folder_does_not_win_over_nextgen(self):
        self.platform_dir.mkdir(parents=True)                  # made by some other tool
        self.legacy.mkdir()
        self.assertEqual(self.resolve(), self.legacy)
        self.assertEqual(list(self.platform_dir.iterdir()), [])  # not stamped while ~/.nextgen is in use

    def test_describing_never_writes_the_marker(self):
        self.platform_dir.mkdir(parents=True)
        app_paths.data_location(home=self.home, env=self.env, platform="linux")
        self.assertEqual(list(self.platform_dir.iterdir()), [])

    def test_migration_marks_the_moved_folder(self):
        self.legacy.mkdir()
        target = app_paths.migrate_legacy_data(confirmed=True, home=self.home, env=self.env, platform="linux")
        self.assertTrue((target / app_paths.DATA_MARKER).is_file())
        self.legacy.mkdir()
        self.assertEqual(self.resolve(), target)


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


class StandaloneWriterPreparationTests(unittest.TestCase):
    """Real KIS/DART file writers with synthetic payloads, no requests, keys, real home or dotenv reads."""
    def setUp(self):
        from core import credentials
        with patch.object(credentials, "load_dotenv_for_development"), \
                patch.object(credentials, "read_setting", return_value=""):
            from data.krx import kis_client, opendart_client
        self.kis, self.dart = kis_client, opendart_client
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.home = Path(folder.name)
        self.platform_dir = self.home / "xdg" / "quantgen"
        self.legacy = self.home / ".nextgen"
        for context in (patch.dict(os.environ, {"XDG_DATA_HOME": str(self.home / "xdg")}, clear=True),
                        patch.object(Path, "home", return_value=self.home), patch.object(sys, "platform", "linux"),
                        patch.object(self.kis, "_TOKEN_PATH", None), patch.object(self.dart, "_CACHE_PATH", None)):
            context.start()
            self.addCleanup(context.stop)

    def test_kis_writer_prepares_the_marker_before_saving_and_reading_its_token(self):
        token = '{"access_token":"synthetic-token","expires_at":12345}'
        self.assertFalse(self.platform_dir.exists())
        self.kis._write_token_file(token)
        self.assertTrue((self.platform_dir / app_paths.DATA_MARKER).is_file())
        self.legacy.mkdir()
        self.assertEqual(self.kis._token_path(), self.platform_dir / "kis_token.json")
        self.assertEqual(self.kis._read_token_file(), token)
        self.assertFalse((self.legacy / "kis_token.json").exists())

    def test_dart_writer_prepares_the_marker_before_saving_its_cache(self):
        client = object.__new__(self.dart.OpenDARTClient)
        entries = {"005930": {"corp_code": "SYNTHETIC", "corp_name": "Fixture"}}
        client._store_cache(entries)
        self.assertTrue((self.platform_dir / app_paths.DATA_MARKER).is_file())
        self.legacy.mkdir()
        self.assertEqual(client._load_cache(), entries)
        self.assertFalse((self.legacy / "dart_corp_codes.json").exists())

    def test_refused_marker_stops_both_writers_before_they_write_payloads(self):
        self.platform_dir.mkdir(parents=True)
        (self.platform_dir / app_paths.DATA_MARKER).mkdir()
        with self.assertRaises(OSError):
            self.kis._write_token_file("synthetic-token")
        client = object.__new__(self.dart.OpenDARTClient)
        client._store_cache({"fixture": {}})  # the existing cache-writer contract swallows storage errors
        self.assertFalse((self.platform_dir / "kis_token.json").exists())
        self.assertFalse((self.platform_dir / "dart_corp_codes.json").exists())
        self.assertTrue((self.platform_dir / app_paths.DATA_MARKER).is_dir())

    def test_explicit_test_paths_remain_pinned_without_preparing_a_default_folder(self):
        token, cache = self.home / "pinned-token.json", self.home / "pinned-cache.json"
        with patch.object(self.kis, "_TOKEN_PATH", token), patch.object(self.dart, "_CACHE_PATH", cache):
            self.kis._write_token_file("synthetic-token")
            object.__new__(self.dart.OpenDARTClient)._store_cache({"fixture": {}})
        self.assertEqual(token.read_text(encoding="utf-8"), "synthetic-token")
        self.assertEqual(json.loads(cache.read_text(encoding="utf-8"))["entries"], {"fixture": {}})
        self.assertFalse(self.platform_dir.exists())


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
