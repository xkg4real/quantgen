"""Key lookup for the DIDM research connectors (owner approval 2026-11-19: research key names in the
credential store, KEY-3 PR of the payments/keys session).

``get_key(name)`` asks ``core.credentials.get`` (environment -> OS keyring -> .env in a development build).
Since KEY-3 (main 9f76b07, 2026-11-19) the store knows all nine research names. A name it does not know falls
back to the process environment with the same cleaning rule (kept for names added here before the store).

Values are only ever returned by ``get_key``. ``key_status`` gives names, presence and source only.
"""
from __future__ import annotations

import os

from core import credentials

RESEARCH_KEYS = (
    "FRED_API_KEY", "ECOS_API_KEY", "SEC_EDGAR_USER_AGENT",
    "ALPHAVANTAGE_API_KEY", "TIINGO_API_KEY", "CRYPTOPANIC_API_KEY",
    "CME_FEDWATCH_API_ID", "CME_FEDWATCH_API_SECRET", "TRADINGECONOMICS_API_KEY",
)
APP_KEYS_USED = ("OPENDART_API_KEY",)


class MissingKey(RuntimeError):
    pass


class SourceError(RuntimeError):
    """A provider refused or answered oddly. The message is safe to print: HTTP status and the provider's
    own short error text with every key value masked (``safe_detail``)."""


def safe_detail(text: object, *secrets: str, limit: int = 160) -> str:
    out = str(text or "")
    for secret in secrets:          # mask first: a key cut in half by the limit would otherwise leak its start
        if secret:
            out = out.replace(secret, "****")
    return " ".join(out.split())[:limit]


def in_store(name: str) -> bool:
    """True once the credential store knows this name (research names: after the KEY-3 PR)."""
    return credentials.names.is_secret(name)


def get_key(name: str) -> str:
    if in_store(name):
        return credentials.get(name)
    return credentials.clean_value(os.environ.get(name))


def require(name: str, hint: str = "") -> str:
    value = get_key(name)
    if not value:
        raise MissingKey(f"{name} is not set" + (f" ({hint})" if hint else ""))
    return value


def key_status(name: str) -> dict:
    """{"name", "present", "source", "in_store"}; never the value."""
    if in_store(name):
        st = credentials.status(name)
        return {"name": name, "present": st["present"], "source": st["source"], "in_store": True}
    present = bool(credentials.clean_value(os.environ.get(name)))
    return {"name": name, "present": present, "source": "env" if present else None, "in_store": False}


def save_key(name: str, value: str) -> None:
    """Save into the OS credential store (Windows Credential Manager). Needs the name to be in the store."""
    if name not in RESEARCH_KEYS + APP_KEYS_USED:
        raise MissingKey(f"{name} is not a DIDM key name")
    if not in_store(name):
        raise MissingKey(f"{name} is not in the credential store yet (KEY-3 PR); use setx {name} for now")
    credentials.set(name, value)
