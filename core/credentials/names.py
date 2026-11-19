"""The names the credential store accepts (KEY-1 list, docs/commercial/ENV_NAMES.md section 1).

Only names live here, never values. A name that is not listed is refused by `core.credentials.set`, so a typo
cannot create a stray keyring entry. Kinds follow the commercial character in the KEY-1 list:

- ``user_broker_key``: the user's own brokerage or exchange key. It stays on the user's PC in every profile
  (D7-G rule 1: the company server never handles brokerage keys, accounts or orders).
- ``user_data_key``: the user's own data-provider key.
- ``user_ai_key``: the user's own AI key.
- ``dev_only``: kept for development; a candidate for removal from the commercial build.
- ``token``: a short-lived token the app itself obtains (not typed in by the user).
"""
from __future__ import annotations

SECRETS: dict[str, str] = {
    "KIS_APP_KEY": "user_broker_key",
    "KIS_APP_SECRET": "user_broker_key",
    "UPBIT_ACCESS_KEY": "user_broker_key",
    "UPBIT_SECRET_KEY": "user_broker_key",
    "FMP_API_KEY": "user_data_key",
    "KRX_API_KEY": "user_data_key",
    "OPENDART_API_KEY": "user_data_key",
    "ANTHROPIC_API_KEY": "user_ai_key",
    "GS_CLIENT_ID": "dev_only",
    "GS_CLIENT_SECRET": "dev_only",
}

# Tokens the app caches. Never read from the environment or .env, only from the keyring.
TOKENS: dict[str, str] = {
    "kis_token": "token",
}

KINDS = ("user_broker_key", "user_data_key", "user_ai_key", "dev_only", "token")


def kind(name: str) -> str:
    """The kind of a known name; KeyError for anything else."""
    if name in SECRETS:
        return SECRETS[name]
    return TOKENS[name]


def is_secret(name: str) -> bool:
    return name in SECRETS


def is_known(name: str) -> bool:
    return name in SECRETS or name in TOKENS
