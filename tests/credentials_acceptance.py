"""KEY-2 credential store (owner decision D7-G, 2026-11-18).

Offline. Never reads `.env` or `~/.nextgen`: `dotenv.load_dotenv` is patched before `config` is imported, HOME
and USERPROFILE point at a temporary folder, and every keyring call goes to an in-memory backend (or to none).
All values below are fake strings made up for this test.
"""
from __future__ import annotations

import importlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_HOME = tempfile.mkdtemp(prefix="qg-credentials-home-")
_SAVED_HOME = {n: os.environ.get(n) for n in ("HOME", "USERPROFILE")}
os.environ["HOME"] = _HOME
os.environ["USERPROFILE"] = _HOME

import dotenv  # noqa: E402

with patch.object(dotenv, "load_dotenv", return_value=False):
    import config  # noqa: E402
    from core import credentials  # noqa: E402
    from core.credentials import names  # noqa: E402
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
    return patch.dict(os.environ, {n: "" for n in names.SECRETS})


class Base(unittest.TestCase):
    def setUp(self):
        self.backend = MemoryBackend()
        credentials.set_backend(self.backend)
        credentials.record_dotenv(set())

    def tearDown(self):
        credentials.set_backend(None)
        credentials.record_dotenv(set())


class NamesTest(unittest.TestCase):
    def test_ten_secret_names_from_key1(self):
        self.assertEqual(sorted(names.SECRETS), sorted([
            "KIS_APP_KEY", "KIS_APP_SECRET", "UPBIT_ACCESS_KEY", "UPBIT_SECRET_KEY", "FMP_API_KEY",
            "KRX_API_KEY", "OPENDART_API_KEY", "ANTHROPIC_API_KEY", "GS_CLIENT_ID", "GS_CLIENT_SECRET"]))
        for name in names.SECRETS:
            self.assertIn(names.kind(name), names.KINDS)

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

    def test_unknown_names_refused(self):
        for call in (lambda: credentials.get("NOT_A_KEY"), lambda: credentials.set("NOT_A_KEY", FAKE),
                     lambda: credentials.status("NOT_A_KEY"), lambda: credentials.get_token("NOT_A_KEY")):
            with self.assertRaises(credentials.UnknownCredential) as ctx:
                call()
            self.assertNotIn(FAKE, str(ctx.exception))

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
    def setUp(self):
        super().setUp()
        self.tmp = Path(tempfile.mkdtemp(prefix="qg-kis-token-"))
        self.path = self.tmp / ".nextgen" / "kis_token.json"
        self._patch = patch.object(kis_client, "_TOKEN_PATH", self.path)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        super().tearDown()

    def _client(self):
        return kis_client.KISClient(base_url="https://example.invalid")

    def test_token_goes_to_keyring_and_old_file_is_removed(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{}", encoding="utf-8")
        client = self._client()
        client._store_token("tok-abc", 3600)
        self.assertFalse(self.path.exists())
        stored = json.loads(self.backend.store[(credentials.SERVICE, "kis_token")])
        self.assertEqual(stored["access_token"], "tok-abc")
        self.assertEqual(client._cached_token(), "tok-abc")

    def test_file_fallback_without_keyring(self):
        credentials.set_backend(None)
        client = self._client()
        client._store_token("tok-file", 3600)
        self.assertTrue(self.path.exists())
        self.assertEqual(client._cached_token(), "tok-file")

    def test_expired_token_not_used(self):
        self.backend.set_password(credentials.SERVICE, "kis_token",
                                  json.dumps({"access_token": "old", "expires_at": time.time() - 10}))
        self.assertIsNone(self._client()._cached_token())

    def test_key_change_drops_token(self):
        client = self._client()
        client._store_token("tok-abc", 3600)
        credentials.set("KIS_APP_KEY", FAKE)
        self.assertNotIn((credentials.SERVICE, "kis_token"), self.backend.store)
        self.assertIsNone(client._cached_token())

    def test_reload_credentials_updates_ready(self):
        with _clear_secret_env():
            client = self._client()
            self.assertFalse(client.ready)
            credentials.set("KIS_APP_KEY", FAKE)
            credentials.set("KIS_APP_SECRET", FAKE2)
            self.assertFalse(client.ready)                                  # fixed at construction ...
            self.assertEqual(client.reload_credentials(), kis_client.requests is not None)   # ... until reloaded


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

            def __init__(self):
                super().__init__()
                self.data = {}

            def get_password(self, service, username):
                return self.data.get((service, username))

            def set_password(self, service, username, password):
                self.data[(service, username)] = password

            def delete_password(self, service, username):
                del self.data[(service, username)]

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


def tearDownModule():
    credentials.set_backend(credentials._UNSET)
    for name, value in _SAVED_HOME.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


if __name__ == "__main__":
    unittest.main()
