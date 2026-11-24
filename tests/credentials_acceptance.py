"""KEY-2 credential store (owner decision D7-G, 2026-11-18).

Offline. Never reads `.env` or the real user's data folders: imports disable dotenv, the module fixture patches
Path.home() and all platform data roots, and every keyring call goes to an in-memory backend (or to none).
HOME/USERPROFILE are not reassigned; explicit QUANTGEN/Flet storage overrides are cleared inside the fixture.
All values below are fake strings made up for this test.
"""
from __future__ import annotations

import importlib
import json
import os
import shutil
import tempfile
import time
import unittest
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

_HOME = ""  # assigned by setUpModule; importing this helper module changes no process paths


@contextmanager
def _temporary_storage_home(home):
    """Isolate every input used by app_paths, including a Windows host's already-marked LOCALAPPDATA."""
    home = Path(home)
    storage_env = {"LOCALAPPDATA": str(home / "AppData" / "Local"),
                   "APPDATA": str(home / "AppData" / "Roaming"),
                   "XDG_DATA_HOME": str(home / ".local" / "share"),
                   "QUANTGEN_DATA_DIR": "", "FLET_APP_STORAGE_DATA": ""}
    with patch.object(Path, "home", return_value=home), patch.dict(os.environ, storage_env):
        yield


def setUpModule():
    global _HOME
    folder = tempfile.TemporaryDirectory(prefix="qg-credentials-home-")
    _HOME = folder.name
    unittest.addModuleCleanup(folder.cleanup)
    contexts = ExitStack()
    unittest.addModuleCleanup(contexts.close)  # restore paths/env before removing the temporary folder
    contexts.enter_context(_temporary_storage_home(_HOME))

import dotenv  # noqa: E402
from core import credentials  # noqa: E402
from core.credentials import names  # noqa: E402

with patch.object(credentials, "load_dotenv_for_development"), \
        patch.object(dotenv, "load_dotenv", return_value=False):
    import config  # noqa: E402
    from data.krx import kis_client  # noqa: E402

FAKE = "fake-value-for-test-7f3a"
FAKE2 = "fake-other-value-9c1d"


class MemoryBackend:
    """Stands in for a keyring backend (same three methods)."""

    priority = 1

    def __init__(self):
        self.store: dict[tuple[str, str], str] = {}

    def get_password(self, service, user):
        return self.store.get((service, user))

    def set_password(self, service, user, password):
        self.store[(service, user)] = password

    def delete_password(self, service, user):
        del self.store[(service, user)]


class LeakyBackend(MemoryBackend):
    """A backend whose errors quote the password, to prove the store does not pass them on."""

    def set_password(self, service, user, password):
        raise RuntimeError(f"cannot save {password}")

    def get_password(self, service, user):
        raise RuntimeError("locked store")


def _clear_secret_env():
    return patch.dict(os.environ, {n: "" for n in list(names.SECRETS) + list(names.RESEARCH)})


class Base(unittest.TestCase):
    """Every test pins the KIS token path to a temporary file, so a key-change listener can never touch the real
    ~/.nextgen/kis_token.json even when kis_client was imported earlier with the real HOME (review item 2)."""

    def setUp(self):
        self.backend = MemoryBackend()
        credentials.set_backend(self.backend)
        credentials.record_dotenv(set())
        self.token_dir = Path(tempfile.mkdtemp(prefix="qg-kis-token-"))
        self.addCleanup(shutil.rmtree, self.token_dir, True)
        self.path = self.token_dir / ".nextgen" / "kis_token.json"
        self._token_patch = patch.object(kis_client, "_TOKEN_PATH", self.path)
        self._token_patch.start()
        kis_client._FILE_TOKEN_IGNORED = False

    def tearDown(self):
        self._token_patch.stop()
        kis_client._FILE_TOKEN_IGNORED = False
        credentials.set_backend(None)
        credentials.record_dotenv(set())


class NamesTest(unittest.TestCase):
    def test_ten_secret_names_from_key1(self):
        self.assertEqual(sorted(names.SECRETS), sorted([
            "KIS_APP_KEY", "KIS_APP_SECRET", "UPBIT_ACCESS_KEY", "UPBIT_SECRET_KEY", "FMP_API_KEY",
            "KRX_API_KEY", "OPENDART_API_KEY", "ANTHROPIC_API_KEY", "GS_CLIENT_ID", "GS_CLIENT_SECRET"]))
        for name in names.SECRETS:
            self.assertIn(names.kind(name), names.KINDS)

    def test_research_names_for_didm(self):
        """Owner answer 2026-11-19: research (DIDM) names are accepted too, kept apart from the app's ten."""
        self.assertEqual(sorted(names.RESEARCH), sorted([
            "FRED_API_KEY", "ECOS_API_KEY", "SEC_EDGAR_USER_AGENT", "ALPHAVANTAGE_API_KEY", "TIINGO_API_KEY",
            "CRYPTOPANIC_API_KEY", "CME_FEDWATCH_API_ID", "CME_FEDWATCH_API_SECRET", "TRADINGECONOMICS_API_KEY",
            # owner N0 approval 2026-11-24: Alpaca, Massive (EODHD not yet: N1 unanswered)
            "ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY", "MASSIVE_API_KEY"]))
        self.assertFalse(set(names.RESEARCH) & set(names.SECRETS))
        for name in names.RESEARCH:
            self.assertEqual(names.kind(name), "research")
            self.assertTrue(names.is_secret(name))

    def test_broker_keys_are_user_broker_keys(self):
        for name in ("KIS_APP_KEY", "KIS_APP_SECRET", "UPBIT_ACCESS_KEY", "UPBIT_SECRET_KEY"):
            self.assertEqual(names.kind(name), "user_broker_key")

    def test_no_company_cloud_slot(self):
        """D7-G: no quantgen_cloud source in the credential store."""
        source = Path(credentials.__file__).read_text(encoding="utf-8") + Path(names.__file__).read_text(encoding="utf-8")
        self.assertNotIn("quantgen_cloud", source)


class LookupOrderTest(Base):
    def test_environment_beats_keyring(self):
        self.backend.set_password(credentials.SERVICE, "FMP_API_KEY", FAKE2)
        with _clear_secret_env(), patch.dict(os.environ, {"FMP_API_KEY": FAKE}):
            self.assertEqual(credentials.get("FMP_API_KEY"), FAKE)
            self.assertEqual(credentials.status("FMP_API_KEY")["source"], "env")

    def test_keyring_beats_dotenv(self):
        self.backend.set_password(credentials.SERVICE, "FMP_API_KEY", FAKE2)
        credentials.record_dotenv({"FMP_API_KEY"})
        with _clear_secret_env(), patch.dict(os.environ, {"FMP_API_KEY": FAKE}):
            self.assertEqual(credentials.get("FMP_API_KEY"), FAKE2)
            self.assertEqual(credentials.status("FMP_API_KEY")["source"], "keyring")

    def test_dotenv_used_last_in_development_build(self):
        credentials.record_dotenv({"FMP_API_KEY"})
        with _clear_secret_env(), patch.dict(os.environ, {"FMP_API_KEY": FAKE}), \
                patch.object(credentials, "may_read_dotenv", return_value=True):
            self.assertEqual(credentials.status("FMP_API_KEY")["source"], "dotenv")
            self.assertEqual(credentials.get("FMP_API_KEY"), FAKE)

    def test_public_build_ignores_dotenv_values(self):
        credentials.record_dotenv({"FMP_API_KEY"})
        with _clear_secret_env(), patch.dict(os.environ, {"FMP_API_KEY": FAKE}), \
                patch.object(credentials, "may_read_dotenv", return_value=False):
            self.assertEqual(credentials.get("FMP_API_KEY"), "")
            self.assertIsNone(credentials.status("FMP_API_KEY")["source"])

    def test_placeholders_and_quotes(self):
        with _clear_secret_env(), patch.dict(os.environ, {"KRX_API_KEY": "<your key>"}):
            self.assertEqual(credentials.get("KRX_API_KEY"), "")
        with _clear_secret_env(), patch.dict(os.environ, {"KRX_API_KEY": f'"{FAKE}"'}):
            self.assertEqual(credentials.get("KRX_API_KEY"), FAKE)

    def test_nothing_set_anywhere(self):
        with _clear_secret_env():
            self.assertEqual(credentials.get("OPENDART_API_KEY"), "")
            self.assertEqual(credentials.status("OPENDART_API_KEY"),
                             {"name": "OPENDART_API_KEY", "kind": "user_data_key", "present": False, "source": None})

    def test_record_dotenv_keeps_only_secret_names(self):
        credentials.record_dotenv({"FMP_API_KEY", "NEXTGEN_HTTP_TIMEOUT", "PATH"})
        self.assertEqual(credentials._dotenv_names, frozenset({"FMP_API_KEY"}))


class WriteTest(Base):
    def test_set_get_delete_round_trip(self):
        with _clear_secret_env():
            credentials.set("ANTHROPIC_API_KEY", f"  {FAKE}  ")
            self.assertEqual(self.backend.store[(credentials.SERVICE, "ANTHROPIC_API_KEY")], FAKE)
            self.assertEqual(credentials.status("ANTHROPIC_API_KEY")["source"], "keyring")
            self.assertTrue(credentials.delete("ANTHROPIC_API_KEY"))
            self.assertFalse(credentials.delete("ANTHROPIC_API_KEY"))
            self.assertEqual(credentials.get("ANTHROPIC_API_KEY"), "")

    def test_research_key_round_trip(self):
        with _clear_secret_env():
            credentials.set("ECOS_API_KEY", FAKE)
            self.assertEqual(credentials.get("ECOS_API_KEY"), FAKE)
            self.assertEqual(credentials.status("ECOS_API_KEY")["kind"], "research")
            self.assertTrue(credentials.delete("ECOS_API_KEY"))

    def test_unknown_names_refused(self):
        for call in (lambda: credentials.get("NOT_A_KEY"), lambda: credentials.set("NOT_A_KEY", FAKE),
                     lambda: credentials.status("NOT_A_KEY"), lambda: credentials.get_token("NOT_A_KEY")):
            with self.assertRaises(credentials.UnknownCredential) as ctx:
                call()
            self.assertNotIn(FAKE, str(ctx.exception))

    def test_swapped_arguments_do_not_leak_value(self):
        """Review item 7: set(value, name) must not put the value in the message, repr or args."""
        with self.assertRaises(credentials.UnknownCredential) as ctx:
            credentials.set(FAKE, "KIS_APP_KEY")
        for text in (str(ctx.exception), repr(ctx.exception), repr(ctx.exception.args)):
            self.assertNotIn(FAKE, text)

    def test_empty_value_refused(self):
        with self.assertRaises(credentials.CredentialError):
            credentials.set("FMP_API_KEY", "   ")

    def test_no_store_raises_without_value(self):
        credentials.set_backend(None)
        with self.assertRaises(credentials.CredentialStoreUnavailable) as ctx:
            credentials.set("FMP_API_KEY", FAKE)
        self.assertNotIn(FAKE, str(ctx.exception))
        self.assertFalse(credentials.keyring_available())

    def test_backend_error_does_not_leak_value(self):
        credentials.set_backend(LeakyBackend())
        with self.assertRaises(credentials.CredentialStoreUnavailable) as ctx:
            credentials.set("FMP_API_KEY", FAKE)
        self.assertNotIn(FAKE, str(ctx.exception))
        self.assertNotIn(FAKE, repr(ctx.exception))
        self.assertTrue(ctx.exception.__suppress_context__)
        with _clear_secret_env():
            self.assertEqual(credentials.get("FMP_API_KEY"), "")      # a locked store reads as "not stored"

    def test_status_never_carries_value(self):
        with _clear_secret_env():
            credentials.set("KIS_APP_KEY", FAKE)
            text = repr(credentials.status_all())
        self.assertNotIn(FAKE, text)
        self.assertEqual(len(credentials.status_all()), 10)
        self.assertEqual(len(credentials.status_all(include_research=True)), 22)   # 10 app + 12 research

    def test_listeners_notified_and_isolated(self):
        seen = []

        def boom(name):
            raise RuntimeError("listener failure")

        credentials.subscribe(boom)
        credentials.subscribe(seen.append)
        try:
            credentials.set("UPBIT_ACCESS_KEY", FAKE)
            credentials.delete("UPBIT_ACCESS_KEY")
        finally:
            credentials.unsubscribe(boom)
            credentials.unsubscribe(seen.append)
        self.assertEqual(seen, ["UPBIT_ACCESS_KEY", "UPBIT_ACCESS_KEY"])


class ConfigTest(Base):
    def test_config_reads_secrets_through_store(self):
        with _clear_secret_env():
            self.assertFalse(config.kis_ready())
            credentials.set("KIS_APP_KEY", FAKE)
            credentials.set("KIS_APP_SECRET", FAKE2)
            self.assertTrue(config.kis_ready())
            self.assertEqual(config.kis_credentials(), (FAKE, FAKE2))

    def test_settings_still_come_from_environment(self):
        with patch.dict(os.environ, {"NEXTGEN_HTTP_TIMEOUT": "'7'"}):
            self.assertEqual(config._clean("NEXTGEN_HTTP_TIMEOUT"), "7")
        self.backend.set_password(credentials.SERVICE, "NEXTGEN_HTTP_TIMEOUT", "99")
        with patch.dict(os.environ, {"NEXTGEN_HTTP_TIMEOUT": ""}):
            self.assertEqual(config._clean("NEXTGEN_HTTP_TIMEOUT"), "")      # settings never come from keyring

    def test_public_build_does_not_call_load_dotenv(self):
        loader = MagicMock(return_value=False)
        try:
            with patch.object(dotenv, "load_dotenv", loader), \
                    patch.object(credentials, "may_read_dotenv", return_value=False):
                importlib.reload(config)
            loader.assert_not_called()
            dev_loader = MagicMock(return_value=False)
            with patch.object(dotenv, "load_dotenv", dev_loader), \
                    patch.object(credentials, "may_read_dotenv", return_value=True):
                importlib.reload(config)
            dev_loader.assert_called_once()
        finally:
            with patch.object(dotenv, "load_dotenv", return_value=False):
                importlib.reload(config)

    def test_dotenv_names_recorded_by_config(self):
        def fake_load(*args, **kwargs):
            os.environ["OPENDART_API_KEY"] = FAKE
            os.environ["NEXTGEN_HTTP_TIMEOUT"] = "9"
            return True

        try:
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OPENDART_API_KEY", None)
                os.environ.pop("NEXTGEN_HTTP_TIMEOUT", None)
                with patch.object(dotenv, "load_dotenv", fake_load), \
                        patch.object(credentials, "may_read_dotenv", return_value=True):
                    importlib.reload(config)
                self.assertEqual(credentials._dotenv_names, frozenset({"OPENDART_API_KEY"}))
                self.backend.set_password(credentials.SERVICE, "OPENDART_API_KEY", FAKE2)
                self.assertEqual(config.opendart_key(), FAKE2)          # keyring ranks above .env
        finally:
            with patch.object(dotenv, "load_dotenv", return_value=False):
                importlib.reload(config)


class KisTokenTest(Base):
    def _client(self):
        return kis_client.KISClient(base_url="https://example.invalid")

    def _file_token(self, token, expires_in=3600):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"access_token": token, "expires_at": time.time() + expires_in}),
                             encoding="utf-8")

    def test_token_goes_to_keyring_and_shared_file_is_kept(self):
        """Review item 4: the file is shared with TRADEGEN and is never deleted."""
        self._file_token("tok-tradegen")
        client = self._client()
        client._store_token("tok-abc", 3600)
        self.assertTrue(self.path.exists())
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["access_token"], "tok-tradegen")
        stored = json.loads(self.backend.store[(credentials.SERVICE, "kis_token")])
        self.assertEqual(stored["access_token"], "tok-abc")
        self.assertEqual(client._cached_token(), "tok-abc")

    def test_existing_file_token_reused_on_first_run(self):
        self._file_token("tok-file")
        self.assertEqual(self._client()._cached_token(), "tok-file")

    def test_file_fallback_without_keyring(self):
        credentials.set_backend(None)
        client = self._client()
        client._store_token("tok-file", 3600)
        self.assertEqual(client._cached_token(), "tok-file")

    @unittest.skipUnless(os.name == "posix", "POSIX file modes")
    def test_fallback_file_is_owner_only(self):
        """Review item 5: 0600 file, 0700 directory when created; an old 0644 file is tightened on read."""
        credentials.set_backend(None)
        self._client()._store_token("tok-file", 3600)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.path.parent.stat().st_mode & 0o777, 0o700)
        os.chmod(self.path, 0o644)
        self._client()._cached_token()
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_expired_keyring_copy_does_not_hide_valid_file(self):
        """Review item 3."""
        self.backend.set_password(credentials.SERVICE, "kis_token",
                                  json.dumps({"access_token": "old", "expires_at": time.time() - 10}))
        self._file_token("tok-file")
        self.assertEqual(self._client()._cached_token(), "tok-file")
        self.backend.set_password(credentials.SERVICE, "kis_token", "{not json")
        self.assertEqual(self._client()._cached_token(), "tok-file")

    def test_keyring_refusing_writes_falls_back_to_file(self):
        """Review item 3: a keyring that reads but refuses writes keeps no stale copy; the file takes the token."""
        class ReadOnly(MemoryBackend):
            def set_password(self, service, user, password):
                raise RuntimeError("CredWrite refused")

        backend = ReadOnly()
        backend.store[(credentials.SERVICE, "kis_token")] = json.dumps({"access_token": "old",
                                                                       "expires_at": time.time() - 10})
        credentials.set_backend(backend)
        client = self._client()
        client._store_token("tok-new", 3600)
        self.assertNotIn((credentials.SERVICE, "kis_token"), backend.store)
        self.assertEqual(client._cached_token(), "tok-new")

    def test_expired_token_not_used(self):
        self.backend.set_password(credentials.SERVICE, "kis_token",
                                  json.dumps({"access_token": "old", "expires_at": time.time() - 10}))
        self.assertIsNone(self._client()._cached_token())

    def test_key_change_drops_keyring_token_and_ignores_shared_file(self):
        client = self._client()
        client._store_token("tok-abc", 3600)
        self._file_token("tok-old-key")
        credentials.set("KIS_APP_KEY", FAKE)
        self.assertNotIn((credentials.SERVICE, "kis_token"), self.backend.store)
        self.assertTrue(self.path.exists())                                 # shared file kept
        self.assertIsNone(client._cached_token())                           # but not trusted for the new key

    def test_real_home_token_file_survives_key_change(self):
        """Review item 2: with no pinned path the listener still never deletes the temporary home's token."""
        home = Path(tempfile.mkdtemp(prefix="qg-fake-home-"))
        self.addCleanup(shutil.rmtree, home, True)
        sentinel = home / ".nextgen" / "kis_token.json"
        sentinel.parent.mkdir(parents=True)
        sentinel.write_text("sentinel", encoding="utf-8")
        with patch.object(kis_client, "_TOKEN_PATH", None), \
                _temporary_storage_home(home):
            self.assertEqual(kis_client._token_path(), sentinel)
            credentials.set("KIS_APP_KEY", FAKE)
            credentials.delete("KIS_APP_KEY")
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "sentinel")

    def test_chmod_failure_still_reads_token(self):
        """KEY-2/b item 1: a file whose mode cannot be changed is still read."""
        self._file_token("tok-file")
        with patch.object(kis_client.os, "chmod", side_effect=PermissionError("not owner")):
            self.assertEqual(self._client()._cached_token(), "tok-file")

    @unittest.skipUnless(os.name == "posix", "POSIX symlinks and modes")
    def test_symlinked_file_mode_left_alone(self):
        """KEY-2/b item 3: the mode fix never follows a link to someone else's file."""
        target = self.token_dir / "shared.json"
        target.write_text(json.dumps({"access_token": "tok-link", "expires_at": time.time() + 3600}),
                          encoding="utf-8")
        os.chmod(target, 0o644)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(target, self.path)
        self.assertEqual(self._client()._cached_token(), "tok-link")
        self.assertEqual(target.stat().st_mode & 0o777, 0o644)

    def test_write_leaves_no_temporary_file(self):
        """KEY-2/b item 3: random temporary name, replaced atomically, nothing left behind."""
        credentials.set_backend(None)
        seen = []
        real_mkstemp = kis_client.tempfile.mkstemp

        def spy(*args, **kwargs):
            fd, name = real_mkstemp(*args, **kwargs)
            seen.append(Path(name).name)
            return fd, name

        with patch.object(kis_client.tempfile, "mkstemp", spy):
            self._client()._store_token("tok-file", 3600)
        self.assertEqual(sorted(p.name for p in self.path.parent.iterdir()), ["kis_token.json"])
        self.assertEqual(len(seen), 1)
        self.assertNotEqual(seen[0], "kis_token.json.tmp")

    @unittest.skipUnless(os.name == "posix", "POSIX symlinks")
    def test_planted_tmp_link_is_not_followed(self):
        """KEY-3 prep item 4: a fixed temporary name would write through a planted link; mkstemp never does."""
        victim = self.token_dir / "victim.txt"
        victim.write_text("do not touch", encoding="utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(victim, self.path.parent / "kis_token.json.tmp")
        credentials.set_backend(None)
        self._client()._store_token("tok-file", 3600)
        self.assertEqual(victim.read_text(encoding="utf-8"), "do not touch")
        self.assertEqual(self._client()._cached_token(), "tok-file")

    @unittest.skipUnless(os.name == "posix", "POSIX symlinks")
    def test_symlinked_token_file_stays_a_link(self):
        """KEY-3 prep item 1: writing through a shared link replaces the target and keeps the link."""
        target = self.token_dir / "shared" / "kis_token.json"
        target.parent.mkdir()
        target.write_text("{}", encoding="utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(target, self.path)
        credentials.set_backend(None)
        self._client()._store_token("tok-shared", 3600)
        self.assertTrue(self.path.is_symlink())
        self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["access_token"], "tok-shared")

    def test_key_id_comes_from_minting_key(self):
        """KEY-3 prep item 3: the key that minted the token, not whatever config holds when it is saved."""
        credentials.set_backend(None)
        client = self._client()
        with _clear_secret_env(), patch.dict(os.environ, {"KIS_APP_KEY": "fake-new-key-0000", "KIS_APP_SECRET": FAKE2}):
            client._store_token("tok-a", 3600, app_key=FAKE)
        stored = json.loads(self.path.read_text(encoding="utf-8"))["key_id"]
        self.assertEqual(stored, kis_client._key_id(FAKE, client.base_url))

    def test_token_records_key_id_not_key(self):
        credentials.set_backend(None)
        with _clear_secret_env(), patch.dict(os.environ, {"KIS_APP_KEY": FAKE, "KIS_APP_SECRET": FAKE2}):
            self._client()._store_token("tok-a", 3600)
        text = self.path.read_text(encoding="utf-8")
        self.assertNotIn(FAKE, text)
        self.assertNotIn(FAKE2, text)
        self.assertEqual(len(json.loads(text)["key_id"]), 16)

    def test_old_key_token_ignored_after_restart(self):
        """KEY-2/b item 2: the key-change flag lives only in one process; key_id covers a restart."""
        credentials.set_backend(None)
        with _clear_secret_env(), patch.dict(os.environ, {"KIS_APP_KEY": FAKE, "KIS_APP_SECRET": FAKE2}):
            self._client()._store_token("tok-old-key", 3600)
        kis_client._FILE_TOKEN_IGNORED = False                             # as after a restart
        with _clear_secret_env(), patch.dict(os.environ, {"KIS_APP_KEY": "fake-new-key-0000", "KIS_APP_SECRET": FAKE2}):
            self.assertIsNone(self._client()._cached_token())
        with _clear_secret_env(), patch.dict(os.environ, {"KIS_APP_KEY": FAKE, "KIS_APP_SECRET": FAKE2}):
            self.assertEqual(self._client()._cached_token(), "tok-old-key")

    def test_token_without_key_id_still_accepted(self):
        """Files written by TRADEGEN or older QUANTGEN have no key_id."""
        self._file_token("tok-tradegen")
        with _clear_secret_env(), patch.dict(os.environ, {"KIS_APP_KEY": FAKE, "KIS_APP_SECRET": FAKE2}):
            self.assertEqual(self._client()._cached_token(), "tok-tradegen")

    def test_reload_credentials_updates_ready(self):
        with _clear_secret_env():
            client = self._client()
            self.assertFalse(client.ready)
            credentials.set("KIS_APP_KEY", FAKE)
            credentials.set("KIS_APP_SECRET", FAKE2)
            self.assertFalse(client.ready)                                  # fixed at construction ...
            self.assertEqual(client.reload_credentials(), kis_client.requests is not None)   # ... until reloaded


class BackendChoiceTest(unittest.TestCase):
    """Review item 6: only the operating system's own stores are accepted."""

    @staticmethod
    def _fake(module, priority):
        cls = type("Fake", (), {"priority": priority})
        cls.__module__ = module
        return cls()

    def test_os_backends_accepted(self):
        for module in ("keyring.backends.Windows", "keyring.backends.macOS", "keyring.backends.SecretService",
                       "keyring.backends.kwallet", "keyring.backends.libsecret"):
            self.assertTrue(credentials._os_backend(self._fake(module, 5)), module)

    def test_chainer_picks_os_store(self):
        """KEY-2/b item 6: a ChainerBackend holding a plaintext store and an OS store yields the OS store."""
        plain = self._fake("keyrings.alt.file", 0.5)
        os_store = self._fake("keyring.backends.SecretService", 5)
        chainer = type("Chainer", (), {"backends": [plain, os_store], "priority": 10})()
        self.assertIs(credentials._choose(chainer), os_store)
        self.assertIsNone(credentials._choose(type("Chainer", (), {"backends": [plain]})()))

    def test_plaintext_and_low_priority_refused(self):
        self.assertFalse(credentials._os_backend(self._fake("keyrings.alt.file", 0.5)))
        self.assertFalse(credentials._os_backend(self._fake("keyrings.alt.file", 5)))
        self.assertFalse(credentials._os_backend(self._fake("keyring.backends.SecretService", 0.5)))
        self.assertFalse(credentials._os_backend(self._fake("keyring.backends.fail", 0)))
        self.assertFalse(credentials._os_backend(self._fake("tests.whatever", 9)))


class KeyringPackageTest(unittest.TestCase):
    """The real `keyring` package path, with an in-memory backend registered through keyring itself."""

    def setUp(self):
        try:
            import keyring  # noqa: F401
            from keyring.backend import KeyringBackend
        except ImportError:
            self.skipTest("keyring not installed")

        class Memory(KeyringBackend):
            priority = 1
            # poses as an OS store so this test exercises keyring.get_keyring(); BackendChoiceTest covers refusal

            def __init__(self):
                super().__init__()
                self.data = {}

            def get_password(self, service, username):
                return self.data.get((service, username))

            def set_password(self, service, username, password):
                self.data[(service, username)] = password

            def delete_password(self, service, username):
                del self.data[(service, username)]

        Memory.__module__ = "keyring.backends.Windows"
        import keyring
        self._previous = keyring.get_keyring()
        self.memory = Memory()
        keyring.set_keyring(self.memory)
        credentials.reset_backend()

    def tearDown(self):
        import keyring
        keyring.set_keyring(self._previous)
        credentials.set_backend(None)

    def test_store_uses_registered_keyring(self):
        self.assertTrue(credentials.keyring_available())
        with _clear_secret_env():
            credentials.set("FMP_API_KEY", FAKE)
            self.assertEqual(self.memory.data[("QUANTGEN", "FMP_API_KEY")], FAKE)
            self.assertEqual(credentials.get("FMP_API_KEY"), FAKE)
            credentials.delete("FMP_API_KEY")

    def test_non_os_backend_refused(self):
        import keyring
        from keyring.backend import KeyringBackend

        class Plain(KeyringBackend):
            priority = 5

            def get_password(self, service, username):
                return None

            def set_password(self, service, username, password):
                pass

            def delete_password(self, service, username):
                pass

        keyring.set_keyring(Plain())
        credentials.reset_backend()
        self.assertFalse(credentials.keyring_available())

    def test_fail_backend_means_no_store(self):
        import keyring
        from keyring.backends import fail
        keyring.set_keyring(fail.Keyring())
        credentials.reset_backend()
        self.assertFalse(credentials.keyring_available())


class AppIdentityTest(unittest.TestCase):
    """D7-G rule 3 goes through core/app_identity.py (OS session, merged with PR #127)."""

    def test_store_asks_app_identity(self):
        from core import app_identity
        with patch.object(app_identity, "may_read_dotenv", return_value=False):
            self.assertFalse(credentials.may_read_dotenv())
        with patch.object(app_identity, "may_read_dotenv", return_value=True):
            self.assertTrue(credentials.may_read_dotenv())

    def test_source_checkout_is_a_development_build(self):
        from core import app_identity
        self.assertEqual(credentials.may_read_dotenv(), app_identity.may_read_dotenv())


class IsolationTest(unittest.TestCase):
    def test_home_is_temporary(self):
        self.assertEqual(Path.home().resolve(), Path(_HOME).resolve())

    def test_all_storage_roots_are_temporary_and_overrides_are_empty(self):
        home = Path(_HOME)
        self.assertEqual(Path(os.environ["LOCALAPPDATA"]), home / "AppData" / "Local")
        self.assertEqual(Path(os.environ["APPDATA"]), home / "AppData" / "Roaming")
        self.assertEqual(Path(os.environ["XDG_DATA_HOME"]), home / ".local" / "share")
        self.assertEqual(os.environ["QUANTGEN_DATA_DIR"], "")
        self.assertEqual(os.environ["FLET_APP_STORAGE_DATA"], "")

    def test_nested_fixture_ignores_a_synthetic_marked_host_folder_and_restores_inputs(self):
        from core.app_paths import DATA_MARKER, user_data_dir
        with tempfile.TemporaryDirectory(prefix="qg-synthetic-host-") as host_folder, \
                tempfile.TemporaryDirectory(prefix="qg-isolated-home-") as home_folder:
            host, home = Path(host_folder), Path(home_folder)
            marked = host / "Local" / "QUANTGEN"
            marked.mkdir(parents=True)
            marker = marked / DATA_MARKER
            marker.write_text('{"app":"QUANTGEN","format":1,"created":"2026-01-01"}', encoding="utf-8")
            legacy = home / ".nextgen"
            legacy.mkdir()
            host_env = {"LOCALAPPDATA": str(host / "Local"), "APPDATA": str(host / "Roaming"),
                        "XDG_DATA_HOME": str(host / "xdg"), "QUANTGEN_DATA_DIR": str(host / "override"),
                        "FLET_APP_STORAGE_DATA": str(host / "flet")}
            with patch.dict(os.environ, host_env):
                before_home = Path.home()
                # A plain temporary HOME would still see this marked Windows platform folder.
                with patch.object(Path, "home", return_value=home), \
                        patch.dict(os.environ, {"QUANTGEN_DATA_DIR": "", "FLET_APP_STORAGE_DATA": ""}):
                    self.assertEqual(user_data_dir(platform="win32"), marked)
                for platform in ("win32", "darwin", "linux"):
                    with self.subTest(platform=platform), _temporary_storage_home(home):
                        self.assertEqual(user_data_dir(platform=platform), legacy)
                        self.assertEqual(os.environ["QUANTGEN_DATA_DIR"], "")
                        self.assertEqual(os.environ["FLET_APP_STORAGE_DATA"], "")
                with self.assertRaisesRegex(RuntimeError, "synthetic fixture error"):
                    with _temporary_storage_home(home):
                        raise RuntimeError("synthetic fixture error")
                self.assertEqual(Path.home(), before_home)
                self.assertEqual({key: os.environ[key] for key in host_env}, host_env)
            self.assertTrue(marker.is_file())
            self.assertEqual(list(marked.iterdir()), [marker])  # no token or mutation in the synthetic host folder


def tearDownModule():
    credentials.set_backend(credentials._UNSET)


if __name__ == "__main__":
    unittest.main()
