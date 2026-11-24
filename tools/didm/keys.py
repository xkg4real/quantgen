"""DIDM key tool (owner PC). Names, presence and source only; values are typed hidden and never printed.

    python -m tools.didm.keys status
    python -m tools.didm.keys set ECOS_API_KEY        # prompts without echo, saves to Windows Credential Manager

`set` saves to the OS credential store (research names are in it since KEY-3, main 9f76b07). The environment
(setx) still wins over the store when both are set; remove the setx value if you move a key to the store.
"""
from __future__ import annotations

import argparse
import getpass
import sys

import config  # noqa: F401 - development build: loads .env like the app
from data.didm import keys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DIDM key names: status and hidden entry")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p_set = sub.add_parser("set")
    p_set.add_argument("name", choices=keys.RESEARCH_KEYS + keys.APP_KEYS_USED)
    args = ap.parse_args(argv)
    if args.cmd == "status":
        for name in keys.RESEARCH_KEYS + keys.APP_KEYS_USED + keys.ENV_ONLY_KEYS:
            st = keys.key_status(name)
            where = st["source"] or "-"
            store = "store" if st["in_store"] else "env only (store after KEY-3)"
            print(f"{name}: {st['present']} (source {where}; {store})")
        return 0
    value = getpass.getpass(f"{args.name} (input hidden): ")
    try:
        keys.save_key(args.name, value)
    except keys.MissingKey as exc:
        print(f"not saved: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001 - no OS keyring etc.; never echo the value
        print(f"not saved: {type(exc).__name__}")
        return 1
    print(f"{args.name}: saved to the OS credential store")
    return 0


if __name__ == "__main__":
    sys.exit(main())
