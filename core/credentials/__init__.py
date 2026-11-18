"""Credential store: where the app finds a user's API keys (KEY-2; owner decision D7-G, 2026-11-18).

The app never needs a `.env` file. Each secret name (``core.credentials.names.SECRETS``) is looked up in this order:

1. the process environment, as set by the shell or the launcher;
2. the operating system's credential store via the ``keyring`` package (Windows Credential Manager,
   macOS Keychain, Secret Service on Linux), service ``"QUANTGEN"``, user name = the variable name;
3. ``.env``, in a development build only (``core.app_identity.may_read_dotenv()``; a public build never reads it).

``config.py`` calls ``load_dotenv_for_development()`` once and reads every setting through ``read_setting``; the
``.env`` logic lives here so ``config.py`` (a Nautilus bridge code-fingerprint input) changes by three lines only.
``dotenv.load_dotenv`` is still the call that reads ``.env`` (tests patch it to keep a developer's file out); the
names it adds are recorded so a value that came from ``.env`` ranks below the keyring instead of above it.

Values never leave through this module except as the return value of ``get``. ``status``, exceptions, ``repr``
and log lines carry names, kinds and sources only.

Not here on purpose (D7-G): a "company cloud" source. The company data server gives data, not keys; that route
belongs to the gateway (``core/gateway``, KEY-3).
"""
from __future__ import annotations

import os
import threading
from typing import Callable, Optional

from core.credentials import names

SERVICE = "QUANTGEN"

__all__ = [
    "SERVICE", "CredentialError", "UnknownCredential", "CredentialStoreUnavailable",
    "get", "set", "delete", "status", "status_all", "clean_value",
    "get_token", "set_token", "delete_token",
    "keyring_available", "set_backend", "reset_backend", "record_dotenv",
    "load_dotenv_for_development", "read_setting",
    "subscribe", "unsubscribe", "may_read_dotenv",
]


class CredentialError(RuntimeError):
    """A credential operation failed. Messages carry the name only, never a value."""


class UnknownCredential(CredentialError, KeyError):
    """The name is not in ``core.credentials.names``. The argument is never kept: a caller that swaps name and
    value (``set(value, name)``) must not put the value into a message, ``repr`` or traceback."""

    def __init__(self, *_ignored: object) -> None:
        super().__init__("unknown credential name")

    def __str__(self) -> str:
        return "unknown credential name"


class CredentialStoreUnavailable(CredentialError):
    """No usable OS credential store on this machine (or it refused the request)."""


_UNSET = object()
_backend: object = _UNSET
_lock = threading.RLock()
_dotenv_names: frozenset[str] = frozenset()
_listeners: list[Callable[[str], None]] = []


# -- helpers -------------------------------------------------------------------------------------------------
def clean_value(raw: Optional[str]) -> str:
    """Blank, quoted or unedited ``<placeholder>`` values count as absent (same rule config.py always used)."""
    value = (raw or "").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1].strip()
    if value.startswith("<") and value.endswith(">"):
        return ""
    return value


def may_read_dotenv() -> bool:
    """D7-G rule 3. ``core/app_identity.py`` (OS session, OS-P0-c) decides; until it exists the checkout is a
    development build, which is today's behaviour."""
    try:
        from core.app_identity import may_read_dotenv as decide
    except ImportError:
        return True
    try:
        return bool(decide())
    except Exception:
        return False


def record_dotenv(loaded: "set[str] | frozenset[str]") -> None:
    """Called by config.py with the environment names ``load_dotenv()`` added. Only secret names matter."""
    global _dotenv_names
    _dotenv_names = frozenset(n for n in loaded if names.is_secret(n))


def load_dotenv_for_development() -> None:
    """Load ``.env`` into the environment in a development build only, and record which secret names it added.
    A public build never reads ``.env`` (D7-G rule 3). Same search as before: ``.env`` in the repository root or
    a parent folder (``dotenv.find_dotenv`` from config.py's folder)."""
    if not may_read_dotenv():
        return
    try:
        import dotenv
    except Exception:
        return
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = None
    folder = root
    while True:
        candidate = os.path.join(folder, ".env")
        if os.path.isfile(candidate):
            path = candidate
            break
        parent = os.path.dirname(folder)
        if parent == folder:
            break
        folder = parent
    before = frozenset(os.environ)
    try:
        dotenv.load_dotenv(path)
    except Exception:
        return
    record_dotenv(frozenset(os.environ) - before)


def read_setting(name: str) -> str:
    """What ``config._clean`` returns: a secret name through the store (``get``), any other setting from the
    environment, with blank, quoted and ``<placeholder>`` values cleaned the same way."""
    if names.is_secret(name):
        return get(name)
    return clean_value(os.environ.get(name))


def _check_secret(name: str) -> None:
    if not names.is_secret(name):
        raise UnknownCredential(name)


def _check_token(name: str) -> None:
    if name not in names.TOKENS:
        raise UnknownCredential(name)


# -- keyring backend -----------------------------------------------------------------------------------------
# Only the operating system's own stores. Third-party backends such as keyrings.alt's PlaintextKeyring (a
# base64 file, priority 0.5) are refused even if installed.
_OS_BACKEND_MODULES = ("keyring.backends.Windows", "keyring.backends.macOS", "keyring.backends.SecretService",
                       "keyring.backends.kwallet", "keyring.backends.libsecret")


def _os_backend(backend: object) -> bool:
    module = type(backend).__module__ or ""
    if not any(module == m or module.startswith(m + ".") for m in _OS_BACKEND_MODULES):
        return False
    try:
        return float(getattr(backend, "priority", 0)) >= 1
    except Exception:
        return False


def _resolve_backend() -> object:
    try:
        import keyring
    except Exception:
        return None
    try:
        backend = keyring.get_keyring()
    except Exception:
        return None
    candidates = list(getattr(backend, "backends", None) or [backend])    # a ChainerBackend wraps several
    accepted = [b for b in candidates if _os_backend(b)]
    if not accepted:
        return None
    return max(accepted, key=lambda b: float(getattr(b, "priority", 0)))


def _get_backend() -> object:
    global _backend
    with _lock:
        if _backend is _UNSET:
            _backend = _resolve_backend()
        return _backend


def set_backend(backend: object) -> None:
    """Use ``backend`` (anything with keyring's ``get_password``/``set_password``/``delete_password``), or
    ``None`` for "no OS credential store". Tests use an in-memory backend so they never touch a real one."""
    global _backend
    with _lock:
        _backend = backend


def reset_backend() -> None:
    """Forget the chosen backend; the next call looks up the keyring package again."""
    set_backend(_UNSET)


def keyring_available() -> bool:
    return _get_backend() is not None


def _kr_get(item: str) -> str:
    backend = _get_backend()
    if backend is None:
        return ""
    try:
        return backend.get_password(SERVICE, item) or ""
    except Exception:
        return ""                                  # a locked or broken store reads as "not stored"


def _kr_set(item: str, value: str) -> None:
    backend = _get_backend()
    if backend is None:
        raise CredentialStoreUnavailable(f"no OS credential store for {item}")
    try:
        backend.set_password(SERVICE, item, value)
    except Exception as exc:
        raise CredentialStoreUnavailable(f"could not store {item} ({type(exc).__name__})") from None


def _kr_delete(item: str) -> bool:
    backend = _get_backend()
    if backend is None:
        return False
    try:
        if not backend.get_password(SERVICE, item):
            return False
        backend.delete_password(SERVICE, item)
        return True
    except Exception as exc:
        raise CredentialStoreUnavailable(f"could not delete {item} ({type(exc).__name__})") from None


# -- secrets -------------------------------------------------------------------------------------------------
def _lookup(name: str) -> tuple[str, Optional[str]]:
    from_env = clean_value(os.environ.get(name))
    if from_env and name not in _dotenv_names:
        return from_env, "env"
    stored = clean_value(_kr_get(name))
    if stored:
        return stored, "keyring"
    if from_env and may_read_dotenv():
        return from_env, "dotenv"
    return "", None


def get(name: str) -> str:
    """The value for a secret name, or "" when it is set nowhere."""
    _check_secret(name)
    return _lookup(name)[0]


def status(name: str) -> dict:
    """``{"name", "kind", "present", "source"}``; source is "env", "keyring", "dotenv" or None. No value."""
    _check_secret(name)
    value, source = _lookup(name)
    return {"name": name, "kind": names.kind(name), "present": bool(value), "source": source}


def status_all() -> list[dict]:
    return [status(n) for n in names.SECRETS]


def set(name: str, value: str) -> None:  # noqa: A001 - the store's verb
    """Save a secret in the OS credential store. Raises CredentialStoreUnavailable when there is none."""
    _check_secret(name)
    cleaned = clean_value(value)
    if not cleaned:
        raise CredentialError(f"empty value for {name}")
    _kr_set(name, cleaned)
    _notify(name)


def delete(name: str) -> bool:
    """Remove a secret from the OS credential store. True if something was removed. Environment and ``.env``
    values are not touched (the user edits those themselves)."""
    _check_secret(name)
    removed = _kr_delete(name)
    if removed:
        _notify(name)
    return removed


# -- tokens --------------------------------------------------------------------------------------------------
def get_token(name: str) -> str:
    """A cached token from the OS credential store, or "" (absent, or no store)."""
    _check_token(name)
    return _kr_get(name)


def set_token(name: str, text: str) -> bool:
    """Store a token. False when there is no OS credential store, so the caller can keep its file fallback."""
    _check_token(name)
    if _get_backend() is None:
        return False
    try:
        _kr_set(name, text)
    except CredentialStoreUnavailable:
        return False
    return True


def delete_token(name: str) -> None:
    _check_token(name)
    try:
        _kr_delete(name)
    except CredentialStoreUnavailable:
        pass


# -- change notification -------------------------------------------------------------------------------------
def subscribe(callback: Callable[[str], None]) -> None:
    """Call ``callback(name)`` after a secret is set or deleted here, so a client built before the change
    (for example ``KISClient``, whose ``ready`` is fixed at construction) can be rebuilt without a restart."""
    with _lock:
        if callback not in _listeners:
            _listeners.append(callback)


def unsubscribe(callback: Callable[[str], None]) -> None:
    with _lock:
        if callback in _listeners:
            _listeners.remove(callback)


def _notify(name: str) -> None:
    with _lock:
        listeners = list(_listeners)
    for callback in listeners:
        try:
            callback(name)
        except Exception:
            pass                                   # a listener must not break saving a key
