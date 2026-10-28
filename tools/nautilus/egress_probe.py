"""Egress probe of the NautilusTrader bridge (spec 2026-10-26 section 4.4; SECURITY-1).

Launched in the venv through tools/nautilus/launch.py, exactly as the sandbox is: one TCP connect to 1.1.1.1:443.
Prints one JSON line {"blocked": bool, "errno": int or null, "error": str}; exit 0 when the connect failed, 1 when
it connected (the socket is closed at once). Imports json and socket only: nothing from the engine or QUANTGEN.
"""
import json
import socket


def probe(host="1.1.1.1", port=443, timeout=3):
    try:
        conn = socket.create_connection((host, port), timeout=timeout)
    except OSError as exc:
        return {"blocked": True, "errno": exc.errno, "error": f"{type(exc).__name__}: {exc}"}
    conn.close()
    return {"blocked": False, "errno": None, "error": ""}


if __name__ == "__main__":
    result = probe()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["blocked"] else 1)
