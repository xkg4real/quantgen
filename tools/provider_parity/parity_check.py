"""Provider parity of the pilot series (roadmap item 5-2): fetch other providers' copies of the two pilot price series
and the cash rate, and compare the md5-pinned files the pilots read against them.

Rules: spec docs/superpowers/specs/2026-10-26-nautilus-bridge-design.md section 10.5, with 10.5.1 (providers and
thresholds) and 10.5.2 (summary fields), on the research branch claude/amazing-gauss-tdiguu from commit 8a8c247. The
design draft docs/nautilus_bridge/PROVIDER_PARITY_DESIGN_DRAFT_2026-11-04.md and its prototype stay on branch
claude/provider-parity-design-20261104 (owner rulings U5 and P-D2 to P-D9 of 2026-11-04); where they differ, the spec
wins.

Run on the owner's machine only, from the root of a clone of the run branch claude/provider-parity-runs-20261111, which
is cut from main (owner ruling P1 of 2026-11-11). Spec 10.5 still names claude/provider-parity-5-2; that branch holds
the unfinished tool of 2026-11-05 (777fc5b) and is not used. The tool commit and sha256 the ruling fixes are written in
README.md here and in results/RULINGS.md, not in this file:

    python -B -m tools.provider_parity.parity_check fetch --series spy --provider fmp --start 2004-12-01 \
        --end 2026-09-25 --out <new folder outside every git work tree> [--env-file <research clone>/.env]
    python -B -m tools.provider_parity.parity_check compare --series spy \
        --table <research clone>/docs/nautilus_bridge/registration/pilot1_E1_spy.json --repo <research clone> \
        --pair fmp <fetch folder>/spy_fmp.csv --pair kis <fetch folder>/spy_kis.csv \
        --unavailable yahoo_now fetch_failed --out <new folder outside every git work tree> --owner-run
    python -B -m tools.provider_parity.parity_check selftest

fetch
- One provider of one series per call. Each provider is a small function over an injected HTTP layer (`http_get`; the
  `kis` fetch goes through the app's KIS client for its token, `yahoo_now` through yfinance). Every request is
  bounded before 2027-01-01: by an explicit last date of at most LAST_REQUEST_DAY or, for the Treasury's yearly
  file, by a calendar year of at most 2026. A response that still holds an observation dated on or after 2027-01-01
  is refused before anything is written.
- Keys are read by NAME only (KEY_NAMES), from --env-file or the process environment, and never printed or written.
- It writes into a new folder outside every git work tree, and never under docs/asset_expansion, ~/.nextgen, a
  ledger folder or a OneDrive folder: the raw response bytes, the normalised `date,value` CSV (window start - 31
  days to window end + 7 days) and `meta.json`. A provider that cannot serve the request ends `UNAVAILABLE <reason>`
  with a reason for compare's --unavailable; nothing is written then.
- The line before `FETCH ... OK` gives one calendar fact of the provider's own dates (weekend dates for spy and rf,
  missing UTC days for btc; calendar membership, the 3.9 exception), so a date label one day off shows before compare.
  For `kis` the same line says when the page-back stopped after the first requested date, and why.

compare
- Reads the pilot table (--table, inside --repo) read-only, then its `prices_file` (spy, btc) or `rf_file` (rf), checks
  the md5 against the table and reads the table's window the way the runner does (lines filtered by their date text
  before any value is parsed). Provider files are `date,value` CSVs. A file that sits beside a fetch record
  (`meta.json`) must be the file that record describes (provider, series, sha256), and the window that record was
  fetched for must cover the table's window; the summary says for each pair whether it had one (`has_fetch_record`).
- Roles and conventions come from PROVIDERS (10.5.1) only; every required provider is compared or declared unavailable
  with a reason. Thresholds are THRESHOLDS (10.5.1). It computes only the kinds COMPUTES names (the 3.9 exception of
  10.5); `selftest` holds the two together.
- Writes `detail.json` (the per-date differences; it stays on the owner's machine) and then `summary.json` (the
  10.5.2 fields; `assert_summary_safe` refuses anything else) into a new folder outside every git work tree and
  outside OneDrive. Nothing is written into the research clone, docs/asset_expansion/ or a ledger.
- Exit codes 0 PASS, 1 FAIL, 3 WITHHELD, 2 refused, 4 error; the result is the last console line
  `PARITY <series> <outcome> exit=<n> summary=<path or ->`. A refused or failed run writes nothing; if the folder of
  a failed write cannot be removed again, a `LEFT BEHIND` line names it, and it never holds a summary without its
  detail.

Every text file is written as UTF-8 with LF, and console lines are written in the console's own encoding (cp949 or
UTF-8) with a backslash escape for a character it lacks, so a run reads the same on Windows and Linux.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import io
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Callable

import numpy as np
import pandas as pd

TOOL_NAME = "parity_check.py"
SCHEMA = "provider-parity-summary/1"
DETAIL_SCHEMA = "provider-parity-detail/1"
FETCH_SCHEMA = "provider-parity-fetch/1"
TABLE_SCHEMA = "nautilus-bridge-table/1"
SERIES = ("spy", "btc", "rf")
ROLES = ("independent", "cross", "vintage", "diagnostic")      # cross: a total-return A against a split-only B
CONVENTIONS = ("total", "split", "none", "rate_pct")
# 10.5.1: provider -> (role, convention, required). The command line names a provider only; it cannot choose a role.
PROVIDERS = {
    "spy": {"fmp": ("independent", "total", True), "kis": ("cross", "split", True),
            "yahoo_now": ("vintage", "total", True)},
    "btc": {"coinbase": ("independent", "none", True), "bitstamp": ("independent", "none", False),
            "binance": ("diagnostic", "none", True)},
    "rf": {"treasury": ("independent", "rate_pct", True), "h15": ("independent", "rate_pct", False),
           "fred_now": ("vintage", "rate_pct", True)},
}
UNAVAILABLE_REASONS = ("no_key", "plan_or_access", "fetch_failed", "short_history")
# The kinds each check computes: the 3.9 exception of spec 10.5 names exactly these, and `selftest` checks that the
# checks compare() emits are these and no others, and that no correlation, mean, volatility or similar is called.
COMPUTES = {
    "coverage": "calendar membership",
    "calendar": "calendar membership",
    "blanks": "calendar membership",
    "integrity_a": "range and gap checks of A alone",
    "units": "range and gap checks of A alone",
    "seed": "range and gap checks of A alone",
    "returns_same_convention": "differences between providers: counts, extreme, range",
    "adjustment_convention": "differences between providers: counts, per-year sums",
    "day_boundary": "differences between providers at lags -1, 0 and +1: counts",
    "levels_and_returns": "differences between providers: counts, percentiles, extreme",
    "values": "differences between providers: counts, extreme",
}
OUTCOMES = ("PASS", "FAIL", "WARN", "WITHHELD")
EXIT = {"PASS": 0, "FAIL": 1, "WITHHELD": 3}
EXIT_REFUSED, EXIT_ERROR = 2, 4
CUTOFF = "2027-01-01"                  # no observation dated on or after this day is requested, stored or compared
# The last day any request names: two days before the cut-off, so an exclusive end bound (yfinance's) is at most
# 2026-12-31.
LAST_REQUEST_DAY = "2026-12-30"
FETCH_LEAD_DAYS, FETCH_TAIL_DAYS = 31, 7    # fetch keeps window start - 31 days (the rf seed) to window end + 7 days
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")    # the runner's line filter (tools/nautilus/runner.py:119)
# series -> (the table's symbol, its file field, its md5 field, the pinned file's name)
PINNED = {"spy": ("SPY", "prices_file", "prices_md5", "yf_SPY.csv"),
          "btc": ("BTC-USD", "prices_file", "prices_md5", "yf_BTC-USD.csv"),
          "rf": ("SPY", "rf_file", "rf_md5", "fred_DGS3MO.csv")}

# 10.5.1 thresholds, fixed before any summary exists. The summary prints them next to every outcome.
THRESHOLDS = {
    "spy": {
        "coverage_min": 0.99,          # share of A's sessions inside B's span that B also has
        "edge_uncovered_max": 5,       # A's sessions outside B's span (B starts late or ends early)
        "ret_diff_tol": 2e-4,          # a day above this counts as a disagreement day
        "ret_diff_max": 2e-3,          # largest allowed abs difference of one day's simple return
        "ret_diff_share_max": 0.005,   # disagreement days allowed: max(floor, share x sessions)
        "ret_diff_floor_days": 5,
        "drift_range_max": 5e-3,       # range of log(P_A / P_B) over the window
        "jump_abs_max": 0.25,          # one-day abs simple return of A above this is a split-shaped error
        "ex_gap_min": 5e-4,            # cross pair: a day whose return gap exceeds this is an ex-dividend candidate
        "ex_gap_max": 2e-2,            # a gap above this is too large for a quarterly SPY dividend
        "ex_days_per_year": 4,         # full calendar years only; 3 or 5 is WARN, anything else FAIL
        "yield_band": [0.005, 0.04],   # per full year, the summed gaps; reported as one boolean only
    },
    "btc": {
        "coverage_min": 0.95,          # inside B's span
        "edge_uncovered_max": 471,     # A's days 2014-09-17..2015-12-31: B may start as late as 2016-01-01
        "late_from": "2017-01-01",     # level bands differ before and after this date
        "level_p50_max": 0.003,        # abs log(P_A / P_B), late segment
        "level_p99_max": 0.015,
        "level_max": 0.05,
        "early_level_p99_max": 0.03,   # early segment: WARN only
        "early_level_max": 0.10,
        "missing_days_warn_max": 5,    # missing UTC days in A: 0 PASS, 1..5 WARN, more FAIL
        "jump_log_abs_max": 0.7,
        "ret_diff_big": 0.02,          # a day whose log-return difference exceeds this is a disagreement day;
                                       # also the day_boundary tolerance at each lag
        "ret_diff_share_max": 0.005,
    },
    "rf": {
        "coverage_min": 0.99,          # share of A's published values inside B's span whose date B also has
        "edge_uncovered_max": 5,
        "value_tol_pct": 0.005,        # DGS3MO is published in percent with 2 decimals
        "range_pct": [-1.0, 20.0],     # data/macro/series_registry.yaml (US_TREASURY range)
        "unit_max_at_least_pct": 1.0,  # the window maximum must be at least this, else the unit is not percent
        "seed_lookback_days": 31,
    },
}
_BUCKET_EDGES = (1e-8, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1)
LIST_CAP = 100

# Keys, read by name only. FMP for fmp; KIS for kis (through the app's KIS client, which keeps its access token in
# ~/.nextgen/kis_token.json: it reads that file and may rewrite it, and writes nothing else under ~/.nextgen).
KEY_NAMES = ("FMP_API_KEY", "KIS_APP_KEY", "KIS_APP_SECRET", "KIS_BASE_URL")
SECRET_NAMES = ("FMP_API_KEY", "KIS_APP_KEY", "KIS_APP_SECRET")


class Refused(Exception):
    """Exit 2: an input the tool will not read, a place it will not write, or a summary outside 10.5.2. Nothing is
    written."""


class FetchFailed(Exception):
    """A provider could not serve a fetch. `reason` is one of UNAVAILABLE_REASONS; the message names no value."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class Series:
    dates: tuple[str, ...]
    values: np.ndarray
    n_dropped_blank: int = 0
    n_dropped_nonpositive: int = 0


@dataclass
class Check:
    id: str
    kind: str                       # "hard" or "warn"
    outcome: str                    # PASS, FAIL, WARN or WITHHELD
    summary: dict = field(default_factory=dict)
    detail: dict = field(default_factory=dict)

    def public(self) -> dict:
        return {"id": self.id, "kind": self.kind, "outcome": self.outcome, **self.summary}


# --------------------------------------------------------------------------- #
# Places
# --------------------------------------------------------------------------- #
def _names_pinned_cache(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    return any(parts[i:i + 2] == ["asset_expansion", "cache"] for i in range(len(parts) - 1))


def guard_path(path: Path, owner_run: bool) -> None:
    """Refuse a pinned cache path before it is opened or hashed, unless the owner says this is his machine. The path
    is judged as it is spelled and as it resolves: a link or a junction to the folder, and on Windows an 8.3 short
    name of it, lead to the same files."""
    if owner_run:
        return
    spelled = Path(path)
    try:
        resolved = spelled.resolve()
    except (OSError, RuntimeError, ValueError):     # a link loop or a malformed name: where it leads cannot be told
        raise Refused(f"{path}: the path cannot be resolved") from None
    if _names_pinned_cache(spelled) or _names_pinned_cache(resolved):
        raise Refused(f"{path}: a pinned cache file is read only on the owner's machine (--owner-run)")


def inside_git_worktree(path: Path) -> bool:
    p = Path(path).resolve()
    return any((q / ".git").exists() for q in (p, *p.parents))


NO_WRITE_PARTS = ("asset_expansion", ".nextgen", "ledgers")     # spec 10.5, Writes
# A OneDrive folder is uploaded: detail.json and the raw responses would leave the machine (spec 10.5, Outputs).
SYNCED_PART_PREFIX = "onedrive"                                 # "OneDrive", "OneDrive - <organisation>"
SYNCED_ROOT_NAMES = ("OneDrive", "OneDriveConsumer", "OneDriveCommercial")     # environment variables, by name


def in_synced_folder(path: Path, environ: dict | None = None) -> bool:
    """True when a part of the resolved path starts with `OneDrive` (any case), or the path lies in a folder one of
    the OneDrive environment variables names (a OneDrive folder that was moved or renamed)."""
    environ = os.environ if environ is None else environ
    p = Path(path).resolve()
    if any(part.lower().startswith(SYNCED_PART_PREFIX) for part in p.parts):
        return True
    here = os.path.normcase(str(p))
    for name in SYNCED_ROOT_NAMES:
        value = (environ.get(name) or "").strip()
        if not value:
            continue
        try:
            root = os.path.normcase(str(Path(value).resolve()))
        except (OSError, RuntimeError, ValueError):
            continue
        if here == root or here.startswith(root.rstrip("\\/") + os.sep):
            return True
    return False


def check_new_out(out: Path) -> None:
    """The output folder must not exist yet and must lie outside every git work tree (the research clone, this
    tool's clone and any other), so nothing the tool writes can be committed by accident; never under
    docs/asset_expansion, ~/.nextgen or a ledger folder (spec 10.5, Writes); and never in a OneDrive folder, which
    would upload detail.json and the raw responses (spec 10.5, Outputs)."""
    if out.exists() or out.is_symlink():
        raise Refused(f"{out}: the output folder must be new")
    if inside_git_worktree(out.parent):
        raise Refused(f"{out}: the output folder must lie outside every git work tree")
    named = sorted({p.lower() for p in Path(out).resolve().parts} & set(NO_WRITE_PARTS))
    if named:
        raise Refused(f"{out}: the output folder must not lie under a folder named {', '.join(named)}")
    if in_synced_folder(out):
        raise Refused(f"{out}: the output folder must not lie in a OneDrive folder (it is uploaded); use a folder "
                      "under %LOCALAPPDATA%")


def _write_new_folder(out: Path, texts: dict[str, str], blobs: dict[str, bytes] | None = None) -> None:
    """Every file is built before this call; the folder and its files are created only here, each with mode x. Text
    is UTF-8 with LF on every platform. `blobs` are written first and `texts` in the order given, so the caller puts
    the file that stands for the result (summary.json, meta.json) last. If a write fails, the folder is removed
    again, so a run that does not end with a result leaves nothing behind; if the removal fails too (a file held
    open by a scanner or a sync client), the exception carries the folder as `left_behind` and `run` names it."""
    out.mkdir(parents=True, exist_ok=False)
    try:
        for rel, data in (blobs or {}).items():
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            with open(out / rel, "xb") as fh:
                fh.write(data)
        for rel, text in texts.items():
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            with open(out / rel, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    except BaseException as exc:
        shutil.rmtree(out, ignore_errors=True)
        if out.exists():
            with contextlib.suppress(Exception):    # an exception type that takes no attribute: the folder goes unnamed
                exc.left_behind = out
        raise


# --------------------------------------------------------------------------- #
# Keys (by name only)
# --------------------------------------------------------------------------- #
def _clean_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1].strip()
    if value.startswith("<") and value.endswith(">"):       # an unedited placeholder, as config.py reads it
        return ""
    return value


def load_keys(env_file: Path | None, environ: dict | None = None) -> dict[str, str]:
    """KEY_NAMES from `env_file` (KEY=value lines; nothing else in it is kept) or else the process environment.
    Values are returned to the caller only; nothing here prints or stores them."""
    environ = os.environ if environ is None else environ
    found: dict[str, str] = {}
    if env_file is not None:
        try:
            text = Path(env_file).read_bytes().decode("utf-8-sig", errors="replace")
        except OSError as exc:
            raise Refused(f"--env-file cannot be read ({type(exc).__name__})") from None
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip()
            if name.startswith("export "):
                name = name[len("export "):].strip()
            if name in KEY_NAMES and _clean_value(value.split(" #", 1)[0]):
                found[name] = _clean_value(value.split(" #", 1)[0])
    for name in KEY_NAMES:
        if name not in found and _clean_value(environ.get(name, "") or ""):
            found[name] = _clean_value(environ.get(name, ""))
    return found


def _secrets(keys: dict[str, str]) -> list[str]:
    return [keys[n] for n in SECRET_NAMES if len(keys.get(n, "")) >= 4]


def _redact(text: str, secrets: list[str]) -> str:
    for s in secrets:
        text = text.replace(s, "<redacted>")
    return text


KIS_NAMES = ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_BASE_URL")


@contextlib.contextmanager
def _environ_names(keys: dict[str, str]):
    """Put the KIS names into the process environment for the app's KIS client, and restore it afterwards."""
    saved = {n: os.environ.get(n) for n in KIS_NAMES}
    try:
        for n in KIS_NAMES:
            if keys.get(n):
                os.environ[n] = keys[n]
        yield
    finally:
        for n, v in saved.items():
            if v is None:
                os.environ.pop(n, None)
            else:
                os.environ[n] = v


# --------------------------------------------------------------------------- #
# HTTP (the one network touchpoint besides the app's KIS client and yfinance)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Response:
    status: int
    body: bytes


HttpGet = Callable[[str, dict, dict], Response]
USER_AGENT = "provider-parity-check/1"
HTTP_TIMEOUT_S = 30.0
_MIN_GAP_S = 0.35
_last_call: dict[str, float] = {}


def urllib_get(url: str, params: dict | None = None, headers: dict | None = None) -> Response:
    """GET `url` with `params`; an HTTP error status is returned, not raised. Any other failure raises FetchFailed with
    the exception type only, because a URL can carry a key (FMP)."""
    import urllib.error
    import urllib.parse
    import urllib.request
    host = urllib.parse.urlsplit(url).netloc
    wait = _MIN_GAP_S - (time.monotonic() - _last_call.get(host, -1e9))
    if wait > 0:
        time.sleep(wait)
    _last_call[host] = time.monotonic()
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    request = urllib.request.Request(full, headers={"User-Agent": USER_AGENT, "Accept": "*/*", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as resp:
            return Response(int(resp.status), resp.read())
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except Exception:
            body = b""
        return Response(int(exc.code), body)
    except Exception as exc:
        raise FetchFailed("fetch_failed", f"request failed ({type(exc).__name__})") from None


# --------------------------------------------------------------------------- #
# Providers (10.5.1 and the design draft's section 3 tables)
# --------------------------------------------------------------------------- #
FMP_URL = "https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted"
KIS_PATH, KIS_TR_ID = "/uapi/overseas-price/v1/quotations/dailyprice", "HHDFS76240000"
KIS_EXCHANGE, KIS_SYMBOL = "AMS", "SPY"           # the draft's code path; AMS for SPY is UNVERIFIED
COINBASE_URL = "https://api.exchange.coinbase.com/products/BTC-USD/candles"
BITSTAMP_URL = "https://www.bitstamp.net/api/v2/ohlc/btcusd/"
BINANCE_URLS = ("https://data-api.binance.vision/api/v3/klines", "https://api.binance.com/api/v3/klines")
TREASURY_URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
H15_URL = "https://www.federalreserve.gov/datadownload/Output.aspx"
H15_SERIES = "bf17364827e38702b42a58cf8eaa3f78"   # Data Download Program id of H15 3-month CMT (UNVERIFIED)
H15_IDENTIFIER = "RIFLGFCM03_N.B"                  # the response must name this series, else the fetch fails
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
SOURCES = {
    "fmp": {"endpoint": FMP_URL, "quote_currency": "USD", "date_label": "the provider's session date"},
    "kis": {"endpoint": f"KIS {KIS_PATH} {KIS_TR_ID} EXCD={KIS_EXCHANGE} SYMB={KIS_SYMBOL} MODP=1",
            "quote_currency": "USD", "date_label": "xymd, the provider's session date"},
    "yahoo_now": {"endpoint": "yfinance.download(SPY, auto_adjust=True)", "quote_currency": "USD",
                  "date_label": "the provider's session date"},
    "coinbase": {"endpoint": COINBASE_URL, "quote_currency": "USD", "date_label": "UTC date of the candle start"},
    "bitstamp": {"endpoint": BITSTAMP_URL, "quote_currency": "USD", "date_label": "UTC date of the candle start"},
    "binance": {"endpoint": " | ".join(BINANCE_URLS), "quote_currency": "USDT",
                "date_label": "UTC date of the kline open time"},
    "treasury": {"endpoint": TREASURY_URL, "quote_currency": "percent", "date_label": "NEW_DATE"},
    "h15": {"endpoint": H15_URL, "quote_currency": "percent", "date_label": "the series' observation date"},
    "fred_now": {"endpoint": FRED_URL, "quote_currency": "percent", "date_label": "observation_date"},
}


@dataclass
class FetchContext:
    series: str
    provider: str
    first: str                        # first requested date
    last: str                         # last requested date, at most LAST_REQUEST_DAY
    http: HttpGet
    keys: dict
    yf_download: Callable | None = None
    kis_get: Callable | None = None

    def key(self, name: str) -> str:
        value = self.keys.get(name, "")
        if not value:
            raise FetchFailed("no_key", f"{name} is not set (--env-file or the environment)")
        return value


@dataclass
class Fetched:
    requests: list[dict]               # each request's parameters, without any key
    pages: list[tuple[str, bytes]]     # (file name, raw response bytes)
    rows: list[tuple[str, float | None]]
    note: str = ""                     # said on the console line above `FETCH ... OK` (kis: a page-back cut short)


# Providers whose requests carry no key: the first bytes of their error answers may be printed. Never fmp, whose URL
# holds the key, and never kis (its client's own message is read by _kis_detail).
KEYLESS = frozenset({"coinbase", "bitstamp", "binance", "treasury", "h15", "fred_now"})
ERROR_EXCERPT_BYTES = 200
_DECIMAL = re.compile(r"\d+\.\d+")


def _excerpt(body: bytes) -> str:
    """The first bytes of an error answer for the console: printable ASCII as it is, every other byte and the
    backslash as \\xNN, and each decimal number masked. Only an error answer (status 400 or above) of a provider
    that takes no key is quoted, so the line can be sent on."""
    text = "".join(chr(b) if 32 <= b < 127 and b != 92 else f"\\x{b:02x}" for b in body[:ERROR_EXCERPT_BYTES])
    return _DECIMAL.sub("#.#", text)


def _ok(resp: Response, what: str) -> bytes:
    if resp.status == 200:
        return resp.body
    said = f"{what}: HTTP {resp.status}"
    if what in KEYLESS and resp.status >= 400 and resp.body:
        said += f", the answer starts: {_excerpt(resp.body)}"
    raise FetchFailed("plan_or_access" if resp.status in (401, 402, 403) else "fetch_failed", said)


def _json(body: bytes, what: str):
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise FetchFailed("fetch_failed", f"{what}: the response is not JSON") from None


def _num(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _iso_from_unix(seconds: float) -> str:
    return datetime.fromtimestamp(float(seconds), tz=timezone.utc).date().isoformat()


def _unix(day: str) -> int:
    return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())


def _chunks(first: str, last: str, days: int) -> list[tuple[str, str]]:
    d0, d1, out = date.fromisoformat(first), date.fromisoformat(last), []
    while d0 <= d1:
        e = min(d0 + timedelta(days=days - 1), d1)
        out.append((d0.isoformat(), e.isoformat()))
        d0 = e + timedelta(days=1)
    return out


def fetch_fmp(ctx: FetchContext) -> Fetched:
    """FMP dividend-adjusted closes (total return), one request with explicit `from` and `to`."""
    key = ctx.key("FMP_API_KEY")
    params = {"symbol": "SPY", "from": ctx.first, "to": ctx.last}
    body = _ok(ctx.http(FMP_URL, {**params, "apikey": key}, {}), "fmp")
    payload = _json(body, "fmp")
    records = payload.get("historical") if isinstance(payload, dict) else payload
    if isinstance(payload, dict) and not records:
        raise FetchFailed("plan_or_access", "fmp answered with a message instead of rows")
    if not isinstance(records, list) or not records:
        raise FetchFailed("fetch_failed", "fmp returned no rows")
    if not any(isinstance(r, dict) and r.get("adjClose") is not None for r in records):
        raise FetchFailed("fetch_failed", "fmp returned no adjClose, so not the dividend-adjusted convention")
    rows = [(str(r.get("date") or "")[:10], _num(r.get("adjClose"))) for r in records if isinstance(r, dict)]
    return Fetched([params], [("fmp_000.json", body)], rows)


def _kis_default_get(keys: dict) -> Callable:
    """The app's KIS client: it reads ~/.nextgen/kis_token.json and may rewrite it with a new token."""
    try:
        from data.krx.kis_client import KISClient    # imported here: only `kis` needs the app's code
        client = KISClient(base_url=keys.get("KIS_BASE_URL") or None)
    except Exception as exc:
        raise FetchFailed("fetch_failed", f"the app's KIS client cannot be loaded ({type(exc).__name__}); run from "
                                          "the clone's root with the app's packages installed") from None
    if not client.ready:
        raise FetchFailed("no_key", "the KIS client is not ready (KIS_APP_KEY, KIS_APP_SECRET)")
    return client._get


_KIS_HTTP = re.compile(r"\bHTTP (\d{3})\b")
_KIS_CODE = re.compile(r"\(([A-Z]{2,6}\d{3,8}): ")                       # the app client's "(<msg_cd>: <msg1>)"
_KIS_INNER = re.compile(r": ([A-Za-z_]{3,40}(?:Error|Exception|Timeout))$")  # the app client's "<tr_id>: <type>"


def _kis_detail(exc: BaseException) -> str:
    """What may be said of a KIS failure: the exception type and, read from the app client's own message by fixed
    patterns only, whether the token request failed, the HTTP status, KIS's message code and the transport error's
    type. The message itself is never printed (it can quote the provider's free text)."""
    text = str(exc)
    said = []
    if text.startswith("token"):
        said.append("token")
    for pattern, label in ((_KIS_HTTP, "HTTP {}"), (_KIS_CODE, "msg_cd {}"), (_KIS_INNER, "{}")):
        m = pattern.search(text)
        if m:
            said.append(label.format(m.group(1)))
    return type(exc).__name__ + ("; " + ", ".join(said) if said else "")


def fetch_kis(ctx: FetchContext) -> Fetched:
    """KIS overseas daily bars with MODP=1 (split-adjusted, dividends not reinvested): 100 rows per call, paged back
    from BYMD = the last requested date. BYMD is never left blank (blank means today). When the page-back ends after
    the first requested date (a page with no new date, or the request budget spent), `note` says where and why: the
    file is short because of the fetch, and the owner reads that before compare."""
    ctx.key("KIS_APP_KEY")
    ctx.key("KIS_APP_SECRET")
    get = ctx.kis_get or _kis_default_get(ctx.keys)
    rows: dict[str, float | None] = {}
    requests, pages = [], []
    bymd = ctx.last.replace("-", "")
    n_pages = (date.fromisoformat(ctx.last) - date.fromisoformat(ctx.first)).days // 100 + 6
    why = f"the budget of {n_pages} requests ran out"
    for k in range(n_pages):
        params = {"AUTH": "", "EXCD": KIS_EXCHANGE, "SYMB": KIS_SYMBOL, "GUBN": "0", "BYMD": bymd, "MODP": "1"}
        try:
            payload = get(KIS_PATH, KIS_TR_ID, params)
        except FetchFailed:
            raise
        except Exception as exc:
            reason = "no_key" if type(exc).__name__ == "KISUnavailable" else "fetch_failed"
            raise FetchFailed(reason, f"kis request failed ({_kis_detail(exc)})") from None
        requests.append(dict(params))
        pages.append((f"kis_{k:03d}.json", json.dumps(payload, sort_keys=True).encode("utf-8")))
        page = payload.get("output2") if isinstance(payload, dict) else None
        fresh = []
        for r in page or []:
            d = str((r or {}).get("xymd") or "")
            if re.fullmatch(r"\d{8}", d):
                iso = f"{d[:4]}-{d[4:6]}-{d[6:]}"
                if iso not in rows:
                    fresh.append(iso)
                    rows[iso] = _num(r.get("clos"))
        if not fresh:
            why = "a page brought no new date"
            break
        earliest = min(fresh)
        if earliest <= ctx.first:
            break
        bymd = (date.fromisoformat(earliest) - timedelta(days=1)).strftime("%Y%m%d")
    if not rows:
        raise FetchFailed("fetch_failed", "kis returned no rows")
    reached = min(rows)
    note = "" if reached <= ctx.first else \
        f"kis paging stopped at {reached}, after the first requested date {ctx.first}: {why}"
    return Fetched(requests, pages, sorted(rows.items()), note)


def _yf_default(symbol: str, start: str, end: str):
    """yfinance as the pinned file was made (auto_adjust=True); its tz cache goes to a temporary folder."""
    import yfinance
    cache = tempfile.mkdtemp(prefix="pp_yf_cache_")
    try:
        if hasattr(yfinance, "set_tz_cache_location"):
            yfinance.set_tz_cache_location(cache)
        return yfinance.download(symbol, start=start, end=end, auto_adjust=True, progress=False, threads=False)
    finally:
        shutil.rmtree(cache, ignore_errors=True)


def fetch_yahoo_now(ctx: FetchContext) -> Fetched:
    """Yahoo re-fetched today (vintage), total return like the pinned file. yfinance's `end` is exclusive."""
    end_exclusive = (date.fromisoformat(ctx.last) + timedelta(days=1)).isoformat()
    params = {"symbol": "SPY", "start": ctx.first, "end": end_exclusive, "auto_adjust": True}
    try:
        df = (ctx.yf_download or _yf_default)("SPY", ctx.first, end_exclusive)
    except FetchFailed:
        raise
    except Exception as exc:
        raise FetchFailed("fetch_failed", f"yfinance failed ({type(exc).__name__})") from None
    if df is None or len(df) == 0:
        raise FetchFailed("fetch_failed", "yfinance returned no rows")
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    rows = [(pd.Timestamp(d).strftime("%Y-%m-%d"), _num(v)) for d, v in close.items()]
    return Fetched([params], [("yahoo_now_000.csv", df.to_csv(lineterminator="\n").encode("utf-8"))], rows)


def fetch_coinbase(ctx: FetchContext) -> Fetched:
    """Coinbase Exchange daily candles [time, low, high, open, close, volume], at most 300 per request."""
    rows, requests, pages = [], [], []
    for k, (lo, hi) in enumerate(_chunks(ctx.first, ctx.last, 300)):
        params = {"granularity": "86400", "start": f"{lo}T00:00:00Z", "end": f"{hi}T00:00:00Z"}
        body = _ok(ctx.http(COINBASE_URL, params, {}), "coinbase")
        payload = _json(body, "coinbase")
        if not isinstance(payload, list):
            raise FetchFailed("fetch_failed", "coinbase answered with a message instead of candles")
        requests.append(params)
        pages.append((f"coinbase_{k:03d}.json", body))
        for c in payload:
            if isinstance(c, list) and len(c) >= 5:
                rows.append((_iso_from_unix(c[0]), _num(c[4])))
    return Fetched(requests, pages, rows)


def fetch_bitstamp(ctx: FetchContext) -> Fetched:
    """Bitstamp daily OHLC (optional provider), at most 1000 per request."""
    rows, requests, pages = [], [], []
    for k, (lo, hi) in enumerate(_chunks(ctx.first, ctx.last, 1000)):
        params = {"step": "86400", "limit": "1000", "start": str(_unix(lo)), "end": str(_unix(hi))}
        body = _ok(ctx.http(BITSTAMP_URL, params, {}), "bitstamp")
        payload = _json(body, "bitstamp")
        ohlc = (payload.get("data") or {}).get("ohlc") if isinstance(payload, dict) else None
        if not isinstance(ohlc, list):
            raise FetchFailed("fetch_failed", "bitstamp answered without an ohlc list")
        requests.append(params)
        pages.append((f"bitstamp_{k:03d}.json", body))
        for c in ohlc:
            if isinstance(c, dict) and c.get("timestamp") is not None:
                rows.append((_iso_from_unix(c["timestamp"]), _num(c.get("close"))))
    return Fetched(requests, pages, rows)


def fetch_binance(ctx: FetchContext) -> Fetched:
    """Binance spot BTCUSDT daily klines (diagnostic: USDT, not USD), at most 1000 per request; the data host first,
    the main host second, as data/crypto/crypto_client.py does."""
    rows, requests, pages = [], [], []
    for k, (lo, hi) in enumerate(_chunks(ctx.first, ctx.last, 1000)):
        params = {"symbol": "BTCUSDT", "interval": "1d", "startTime": str(_unix(lo) * 1000),
                  "endTime": str((_unix(hi) + 86400) * 1000 - 1), "limit": "1000"}
        last_error: FetchFailed | None = None
        body = None
        for url in BINANCE_URLS:
            try:
                body = _ok(ctx.http(url, params, {}), "binance")
                break
            except FetchFailed as exc:
                last_error = exc
        if body is None:
            raise last_error or FetchFailed("fetch_failed", "binance: no host answered")
        payload = _json(body, "binance")
        if not isinstance(payload, list):
            raise FetchFailed("fetch_failed", "binance answered with a message instead of klines")
        requests.append(params)
        pages.append((f"binance_{k:03d}.json", body))
        for c in payload:
            if isinstance(c, list) and len(c) >= 5:
                rows.append((_iso_from_unix(int(c[0]) / 1000), _num(c[4])))
    return Fetched(requests, pages, rows)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def fetch_treasury(ctx: FetchContext) -> Fetched:
    """US Treasury daily par yield curve, one XML file per calendar year; the 3-month column BC_3MONTH."""
    import xml.etree.ElementTree as ET
    rows, requests, pages = [], [], []
    for year in range(int(ctx.first[:4]), int(ctx.last[:4]) + 1):
        params = {"data": "daily_treasury_yield_curve", "field_tdr_date_value": str(year)}
        body = _ok(ctx.http(TREASURY_URL, params, {}), "treasury")
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            raise FetchFailed("fetch_failed", "treasury: the response is not XML") from None
        requests.append(params)
        pages.append((f"treasury_{year}.xml", body))
        for props in root.iter():
            if _local(props.tag) != "properties":
                continue
            fields = {_local(c.tag): (c.text or "").strip() for c in props}
            if fields.get("NEW_DATE"):
                rows.append((fields["NEW_DATE"][:10], _num(fields.get("BC_3MONTH"))))
    return Fetched(requests, pages, rows)


def fetch_h15(ctx: FetchContext) -> Fetched:
    """Federal Reserve H.15 Data Download Program CSV (optional provider). A response can hold several maturities,
    one per column: the values are read from the one column whose `Unique Identifier` cell names H15_IDENTIFIER
    (`H15/H15/<identifier>`). A response where no column or more than one names it is a failed fetch, not data."""
    d0, d1 = date.fromisoformat(ctx.first), date.fromisoformat(ctx.last)
    params = {"rel": "H15", "series": H15_SERIES, "lastobs": "", "from": d0.strftime("%m/%d/%Y"),
              "to": d1.strftime("%m/%d/%Y"), "filetype": "csv", "label": "include", "layout": "seriescolumn"}
    body = _ok(ctx.http(H15_URL, params, {}), "h15")
    try:
        lines = body.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError:
        raise FetchFailed("fetch_failed", "h15: the response is not UTF-8") from None
    table = [[c.strip().strip('"').strip() for c in line.split(",")] for line in lines]
    named = [i for cells in table if cells[0].startswith("Unique Identifier")
             for i, c in enumerate(cells) if i and c.rsplit("/", 1)[-1] == H15_IDENTIFIER]
    if len(named) != 1:
        raise FetchFailed("fetch_failed", "h15: the response names the 3-month series in more than one column" if named
                          else "h15: the response does not name the 3-month series")
    rows = []
    for cells in table:
        if _DATE.fullmatch(cells[0]):
            if len(cells) <= named[0]:
                raise FetchFailed("fetch_failed", "h15: a dated row lacks the 3-month column")
            rows.append((cells[0], _num(cells[named[0]])))    # "ND" (no data) reads as a blank
    return Fetched([params], [("h15_000.csv", body)], rows)


def fetch_fred_now(ctx: FetchContext) -> Fetched:
    """FRED's fredgraph CSV fetched today (vintage); '.' or an empty cell is a published blank."""
    params = {"id": "DGS3MO", "cosd": ctx.first, "coed": ctx.last}
    body = _ok(ctx.http(FRED_URL, params, {}), "fred_now")
    try:
        lines = body.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError:
        raise FetchFailed("fetch_failed", "fred_now: the response is not UTF-8") from None
    if not lines or "DGS3MO" not in lines[0]:
        raise FetchFailed("fetch_failed", "fred_now: the response is not the DGS3MO CSV")
    rows = []
    for line in lines[1:]:
        cells = [c.strip() for c in line.split(",")]
        if len(cells) >= 2 and _DATE.fullmatch(cells[0][:10]):
            rows.append((cells[0][:10], _num(cells[1])))
    return Fetched([params], [("fred_now_000.csv", body)], rows)


FETCHERS = {"fmp": fetch_fmp, "kis": fetch_kis, "yahoo_now": fetch_yahoo_now, "coinbase": fetch_coinbase,
            "bitstamp": fetch_bitstamp, "binance": fetch_binance, "treasury": fetch_treasury, "h15": fetch_h15,
            "fred_now": fetch_fred_now}


def fetch_window(start: str, end: str) -> tuple[str, str]:
    """The requested span: window start - 31 days to window end + 7 days, never past LAST_REQUEST_DAY."""
    first = (date.fromisoformat(start) - timedelta(days=FETCH_LEAD_DAYS)).isoformat()
    last = min((date.fromisoformat(end) + timedelta(days=FETCH_TAIL_DAYS)).isoformat(), LAST_REQUEST_DAY)
    return first, last


def normalise(fetched: Fetched, first: str, last: str) -> list[tuple[str, float | None]]:
    """Unique ISO dates, refused if any row is dated on or after the cut-off, then cut to [first, last]."""
    seen: dict[str, float | None] = {}
    for d, v in fetched.rows:
        if not (_DATE.fullmatch(d or "") and _valid_iso(d)):
            raise FetchFailed("fetch_failed", "a row without an ISO date")
        if d >= CUTOFF:
            raise Refused("a response holds an observation dated on or after 2027-01-01; nothing is written")
        if d in seen and seen[d] != v and not (seen[d] is None and v is None):
            raise FetchFailed("fetch_failed", "a date with two different values")
        seen.setdefault(d, v)
    rows = sorted((d, v) for d, v in seen.items() if first <= d <= last)
    if not any(v is not None for _, v in rows):
        raise FetchFailed("fetch_failed", "no published value in the requested span")
    return rows


def _valid_iso(d: str) -> bool:
    try:
        date.fromisoformat(d)
    except ValueError:
        return False
    return True


def provider_csv(rows: list[tuple[str, float | None]]) -> str:
    return "date,value\n" + "".join(f"{d},{'' if v is None else repr(float(v))}\n" for d, v in rows)


def provider_calendar_fact(series: str, rows: list[tuple[str, float | None]]) -> tuple[str, str, int]:
    """One calendar-membership count of a provider's own dates (the 3.9 exception of spec 10.5), as (meta key,
    console words, count): weekend dates for spy and rf, which have none when the dates are session dates, and the
    UTC days missing inside the file's own first-to-last span for btc. A date label one calendar day off (a Korean
    date, or UTC midnight read in local time) shows here, before compare makes the run of record."""
    dates = [d for d, _ in rows]
    if series == "btc":
        return "n_missing_days", "missing days", len(set(_calendar_days(dates[0], dates[-1])) - set(dates))
    return "n_weekend_dates", "weekend dates", sum(1 for d in dates if date.fromisoformat(d).weekday() >= 5)


def run_fetch(args, *, http: HttpGet, yf_download, kis_get, now: datetime, say) -> int:
    series, provider = args.series, args.provider
    if provider not in PROVIDERS[series]:
        raise Refused(f"{series}: provider {provider!r} is not one of {tuple(PROVIDERS[series])}")
    for d in (args.start, args.end):
        if not (_DATE.fullmatch(d) and _valid_iso(d)):
            raise Refused("--start and --end are ISO dates (YYYY-MM-DD)")
    if args.start > args.end:
        raise Refused("--start is after --end")
    if args.end >= CUTOFF:
        raise Refused("--end is on or after 2027-01-01; no such observation is requested")
    check_new_out(args.out)
    keys = load_keys(args.env_file)
    secrets = _secrets(keys)
    say.secrets[:] = secrets
    first, last = fetch_window(args.start, args.end)
    ctx = FetchContext(series, provider, first, last, http, keys, yf_download, kis_get)
    with _environ_names(keys) if provider == "kis" else contextlib.nullcontext():
        fetched = FETCHERS[provider](ctx)
    for name, blob in fetched.pages:
        if any(s.encode("utf-8") in blob for s in secrets):
            raise Refused(f"{name}: the response holds a key value; nothing is written")
    rows = normalise(fetched, first, last)
    role, convention, required = PROVIDERS[series][provider]
    csv_name = f"{series}_{provider}.csv"
    csv_text = provider_csv(rows)
    fact_key, fact_words, fact = provider_calendar_fact(series, rows)
    meta = {"schema": FETCH_SCHEMA, "series": series, "provider": provider, "role": role, "convention": convention,
            "required": required, **SOURCES[provider], "window": {"start": args.start, "end": args.end},
            "requested": {"first": first, "last": last}, "requests": fetched.requests,
            "fetched_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "raw": [{"file": f"raw/{n}", "sha256": hashlib.sha256(b).hexdigest(), "n_bytes": len(b)}
                    for n, b in fetched.pages],
            "csv": {"file": csv_name, "sha256": hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
                    "n_rows": len(rows), "n_blank": sum(1 for _, v in rows if v is None),
                    "first_date": rows[0][0], "last_date": rows[-1][0], fact_key: fact},
            "keys_read_by_name": [n for n in KEY_NAMES if n in keys],
            "tool": {"name": TOOL_NAME, "sha256": tool_sha256()}}
    meta_text = json.dumps(meta, indent=1, sort_keys=True) + "\n"
    if any(s in meta_text or s in csv_text for s in secrets):
        raise Refused("a key value reached the fetch record; nothing is written")
    _write_new_folder(args.out, {csv_name: csv_text, "meta.json": meta_text},
                      {f"raw/{n}": b for n, b in fetched.pages})
    say(f"rows {len(rows)}, first {rows[0][0]}, last {rows[-1][0]}, {fact_words} {fact}"
        + (f"; {fetched.note}" if fetched.note else ""))
    say(f"FETCH {series} {provider} OK exit=0 csv={args.out / csv_name}")
    return 0


# --------------------------------------------------------------------------- #
# Reading for compare
# --------------------------------------------------------------------------- #
def _window_frame(data: bytes, start: str, end: str) -> pd.Series:
    """Keep the header and the lines whose leading date text lies in [start, end], before any value is parsed
    (spec 2026-10-26 5.3.2 step 5), then read as the study reads (first column as index, first value column)."""
    lines = data.decode("utf-8").splitlines(keepends=True)
    if not lines:
        raise Refused("empty file")
    kept = "".join([lines[0]] + [x for x in lines[1:] if _DATE.fullmatch(x[:10]) and start <= x[:10] <= end])
    s = pd.read_csv(io.StringIO(kept), index_col=0, parse_dates=True).iloc[:, 0]
    s.index = pd.to_datetime(s.index)
    return pd.to_numeric(s, errors="raise").astype(float)


def _to_series(s: pd.Series, keep_blanks: bool) -> Series:
    n_blank = n_nonpos = 0
    if not keep_blanks:
        n_blank = int(s.isna().sum())
        s = s.dropna()
        n_nonpos = int((s <= 0).sum())
        s = s[s > 0]
    if not (s.index.is_monotonic_increasing and s.index.is_unique):
        raise Refused("dates are not strictly increasing and unique")
    return Series(tuple(d.strftime("%Y-%m-%d") for d in s.index), s.to_numpy(dtype=float), n_blank, n_nonpos)


def read_table(table: Path, repo: Path, series: str) -> dict:
    """The pilot table, read-only: the pinned file of `series`, its md5 and the table's window."""
    repo_r = Path(repo).resolve()
    if Path(__file__).resolve().is_relative_to(repo_r):
        raise Refused("--repo holds this tool: run it from a separate clone, never from the research clone (U5)")
    if not (repo_r / ".git").exists():
        raise Refused("--repo must be the root of the research clone (it has no .git)")
    t = Path(table).resolve()
    if not t.is_relative_to(repo_r):
        raise Refused("--table must be a pilot table inside --repo")
    try:
        data = json.loads(t.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise Refused(f"{t.name}: cannot be read as a pilot table ({type(exc).__name__})") from None
    symbol, fkey, mkey, name = PINNED[series]
    if not isinstance(data, dict) or data.get("schema") != TABLE_SCHEMA:
        raise Refused(f"{t.name}: not a pilot table ({TABLE_SCHEMA})")
    if data.get("symbol") != symbol:
        raise Refused(f"--series {series} takes the {symbol} table")
    rel, md5, start, end = data.get(fkey), data.get(mkey), data.get("start"), data.get("end")
    if not isinstance(rel, str) or not rel:
        raise Refused(f"{t.name}: no {fkey}")
    p = PurePosixPath(rel)
    if p.is_absolute() or ".." in p.parts or "\\" in rel or p.name != name:
        raise Refused(f"{t.name}: {fkey} must be a relative path to {name}")
    if not (isinstance(md5, str) and re.fullmatch(r"[0-9a-f]{32}", md5)):
        raise Refused(f"{t.name}: {mkey} is not an md5")
    if not all(isinstance(d, str) and _DATE.fullmatch(d) and _valid_iso(d) for d in (start, end)) or start > end:
        raise Refused(f"{t.name}: start and end must be ISO dates in order")
    if end >= CUTOFF:
        raise Refused(f"{t.name}: the window reaches 2027-01-01; nothing on or after it is compared")
    return {"path": repo_r / Path(*p.parts), "file": name, "md5": md5, "start": start, "end": end}


def read_pinned(path: Path, *, md5: str, start: str, end: str, owner_run: bool, keep_blanks: bool = False) -> Series:
    guard_path(path, owner_run)
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise Refused(f"{Path(path).name}: cannot be read ({type(exc).__name__})") from None
    found = hashlib.md5(data).hexdigest()
    if found != md5:
        raise Refused(f"{Path(path).name}: md5 {found} differs from the table's {md5}")
    try:
        s = _to_series(_window_frame(data, start, end), keep_blanks)
    except (UnicodeDecodeError, ValueError, TypeError, IndexError, KeyError) as exc:
        # the exception's own text can quote a cell of the file, so only its type is printed
        raise Refused(f"{Path(path).name}: cannot be read as the study reads it ({type(exc).__name__})") from None
    if int(np.isfinite(s.values).sum()) < 2:
        raise Refused(f"{Path(path).name}: fewer than two values in the table's window")
    return s


def read_provider(path: Path, *, provider: str, series: str, start: str, end: str, owner_run: bool,
                  window: tuple[str, str], keep_blanks: bool = False) -> tuple[Series, str, bool]:
    """A provider's `date,value` file: (series, file sha256, whether it came with its fetch record). A fetch folder
    says which provider and series its CSV holds and what the CSV's sha256 was when it was fetched: a file beside a
    fetch record that names another provider or series, another file or other bytes is refused. So is one whose
    record was fetched for a window that does not cover `window`, the table's start and end: 10.5.1 measures coverage
    over the provider's first-to-last span and counts A's dates outside it against `edge_uncovered_max` (P-D5), so
    that span has to be the provider's own history, not a fetch cut short by other dates. A wider fetch is taken:
    the file is cut to [start, end] here. A file with no fetch record beside it is compared, and the summary says so
    (`has_fetch_record` false)."""
    guard_path(path, owner_run)
    name = Path(path).name
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise Refused(f"{name}: cannot be read ({type(exc).__name__})") from None
    sha = hashlib.sha256(data).hexdigest()
    has_record = False
    meta = Path(path).parent / "meta.json"
    if meta.is_file():
        try:
            m = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError):
            raise Refused(f"{meta}: unreadable fetch record") from None
        if isinstance(m, dict) and m.get("schema") == FETCH_SCHEMA:
            if (m.get("provider"), m.get("series")) != (provider, series):
                raise Refused(f"{name}: its fetch record names another provider or series")
            recorded = m.get("csv") if isinstance(m.get("csv"), dict) else {}
            if recorded.get("file") != name or recorded.get("sha256") != sha:
                raise Refused(f"{name}: not the file its fetch record describes (name or sha256 differs); fetch "
                              "again into a new folder")
            span = m.get("window") if isinstance(m.get("window"), dict) else {}
            got = (span.get("start"), span.get("end"))
            if not all(isinstance(d, str) and _DATE.fullmatch(d) for d in got):
                raise Refused(f"{name}: its fetch record names no window; fetch again into a new folder")
            if not (got[0] <= window[0] and window[1] <= got[1]):
                raise Refused(f"{name}: its fetch record's window {got[0]}..{got[1]} does not cover the table's window "
                              f"{window[0]}..{window[1]}; fetch again with the table's --start and --end into a new "
                              "folder")
            has_record = True
    lines = data.decode("utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip() != "date,value":
        raise Refused(f"{name}: the header must be `date,value`")
    if any(_DATE.fullmatch(x[:10]) and x[:10] >= CUTOFF for x in lines[1:]):
        raise Refused(f"{name}: holds an observation dated on or after 2027-01-01")
    try:
        frame = _window_frame(data, start, end)
        if np.isinf(frame.to_numpy(dtype=float)).any():     # a fetch writes a finite number or a blank cell, never inf
            raise Refused(f"{name}: holds a value that is not a finite number")
        return _to_series(frame, keep_blanks), sha, has_record
    except (UnicodeDecodeError, ValueError, TypeError, IndexError, KeyError) as exc:
        raise Refused(f"{name}: cannot be read ({type(exc).__name__})") from None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def bucket(x: float | None) -> str:
    """A decade label in place of a magnitude, so no exact difference leaves the owner's machine."""
    if x is None or not math.isfinite(x):
        return "n/a"
    x = abs(float(x))
    for edge in _BUCKET_EDGES:
        if x <= edge:
            return f"<={edge:.0e}"
    return f">{_BUCKET_EDGES[-1]:.0e}"


def _cap(dates: list[str]) -> list[str]:
    return sorted(dates)[:LIST_CAP]


def _common(a: Series, b: Series) -> tuple[list[str], np.ndarray, np.ndarray]:
    ib = {d: i for i, d in enumerate(b.dates)}
    keep = [(d, i) for i, d in enumerate(a.dates) if d in ib]
    days = [d for d, _ in keep]
    return days, a.values[[i for _, i in keep]], b.values[[ib[d] for d, _ in keep]]


def _overlap(a: Series, b: Series) -> tuple[str, str] | None:
    if not a.dates or not b.dates:
        return None
    lo, hi = max(a.dates[0], b.dates[0]), min(a.dates[-1], b.dates[-1])
    return (lo, hi) if lo <= hi else None


def _calendar_days(lo: str, hi: str) -> list[str]:
    d0, d1 = date.fromisoformat(lo), date.fromisoformat(hi)
    return [(d0 + timedelta(days=k)).isoformat() for k in range((d1 - d0).days + 1)]


def _demote(check: Check, role: str) -> Check:
    """A vintage or diagnostic pair never fails a series: its FAIL is reported as WARN (10.5.1)."""
    if role in ("vintage", "diagnostic"):
        check.kind = "warn"
        if check.outcome == "FAIL":
            check.outcome = "WARN"
    return check


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #
def _base_dates(series: str, a: Series) -> list[str]:
    """A's dates that coverage counts: every date, or for the cash rate every date with a published value."""
    return [d for d, v in zip(a.dates, a.values) if not math.isnan(v)] if series == "rf" else list(a.dates)


def check_coverage(series: str, a: Series, b: Series) -> Check:
    """P-D5: the share of A's dates inside B's first-to-last span that B also has, and, as its own count against
    edge_uncovered_max, A's dates outside that span (a provider that starts late or ends early). For the cash rate
    both sides count published values only, so a provider file of blanks covers nothing."""
    t = THRESHOLDS[series]
    days, _, _ = _common(a, b)
    base, b_dates = _base_dates(series, a), _base_dates(series, b)
    inside = [d for d in base if b_dates and b_dates[0] <= d <= b_dates[-1]]
    n_outside = len(base) - len(inside)
    in_b = set(b_dates)
    share = sum(1 for d in inside if d in in_b) / len(inside) if inside else 0.0
    ok = bool(inside) and share >= t["coverage_min"] and n_outside <= t["edge_uncovered_max"]
    return Check("coverage", "hard", "PASS" if ok else "WITHHELD",
                 {"n_a": len(a.dates), "n_b": len(b.dates), "n_common": len(days), "n_a_outside_b_span": n_outside,
                  "coverage_ok": ok,
                  "first_date": b_dates[0] if b_dates else None, "last_date": b_dates[-1] if b_dates else None},
                 {"share": share})


def check_calendar(series: str, a: Series, b: Series) -> Check:
    """Dates of A and B inside their overlap. Calendar dates are public facts and may be reported."""
    ov = _overlap(a, b)
    if ov is None:
        return Check("calendar", "hard", "WITHHELD", {"n_only_a": 0, "n_only_b": 0})
    sa = {d for d in a.dates if ov[0] <= d <= ov[1]}
    sb = {d for d in b.dates if ov[0] <= d <= ov[1]}
    only_a, only_b = sorted(sa - sb), sorted(sb - sa)
    summary = {"n_only_a": len(only_a), "n_only_b": len(only_b), "only_a": _cap(only_a), "only_b": _cap(only_b),
               "truncated": len(only_a) > LIST_CAP or len(only_b) > LIST_CAP}
    if series == "spy":
        weekend = [d for d in a.dates if date.fromisoformat(d).weekday() >= 5]
        summary["n_weekend_a"] = len(weekend)
        outcome = "FAIL" if (only_a or only_b or weekend) else "PASS"
    else:
        outcome = "WARN" if (only_a or only_b) else "PASS"
    return Check("calendar", "hard", outcome, summary)


def check_spy_integrity(a: Series) -> Check:
    t = THRESHOLDS["spy"]
    r = a.values[1:] / a.values[:-1] - 1.0
    big = np.abs(r) > t["jump_abs_max"]
    jumps = [a.dates[i + 1] for i in np.flatnonzero(big)]
    ok = not jumps and a.n_dropped_nonpositive == 0
    return Check("integrity_a", "hard", "PASS" if ok else "FAIL",
                 {"n_rows": len(a.dates), "n_dropped_blank": a.n_dropped_blank,
                  "n_dropped_nonpositive": a.n_dropped_nonpositive, "no_split_shaped_jump": not jumps},
                 {"jump_dates": jumps})


def check_spy_same_convention(a: Series, b: Series) -> Check:
    t = THRESHOLDS["spy"]
    days, pa, pb = _common(a, b)
    if len(days) < 2:
        return Check("returns_same_convention", "hard", "WITHHELD", {})
    d = (pa[1:] / pa[:-1] - 1.0) - (pb[1:] / pb[:-1] - 1.0)
    over = np.abs(d) > t["ret_diff_tol"]
    allowed = max(t["ret_diff_floor_days"], int(t["ret_diff_share_max"] * len(d)))
    log_ratio = np.log(pa / pb)
    drift = float(np.max(log_ratio) - np.min(log_ratio))
    max_abs = float(np.max(np.abs(d)))
    ok = max_abs <= t["ret_diff_max"] and int(over.sum()) <= allowed and drift <= t["drift_range_max"]
    rank = np.argsort(-np.abs(d))[:LIST_CAP]
    return Check("returns_same_convention", "hard", "PASS" if ok else "FAIL",
                 {"n_days": int(len(d)), "n_over_tol": int(over.sum()), "n_allowed": allowed,
                  "max_abs_bucket": bucket(max_abs), "drift_range_bucket": bucket(drift),
                  "max_ok": max_abs <= t["ret_diff_max"], "drift_ok": drift <= t["drift_range_max"]},
                 {"worst": [[days[i + 1], float(d[i])] for i in rank], "drift_range": drift, "max_abs": max_abs})


def check_spy_cross_convention(a: Series, b: Series) -> Check:
    """A total-return A against a split-only B: the return gap should sit on four ex-dividend days a year, each
    positive and small, and be about zero elsewhere. Only counts and one boolean leave: the yearly gap sum is close
    to the dividend yield, which with public dividend amounts would give the price level."""
    t = THRESHOLDS["spy"]
    days, pa, pb = _common(a, b)
    if len(days) < 2:
        return Check("adjustment_convention", "hard", "WITHHELD", {})
    g = (pa[1:] / pa[:-1] - 1.0) - (pb[1:] / pb[:-1] - 1.0)
    gd = days[1:]
    ex = g > t["ex_gap_min"]
    neg = g < -t["ex_gap_min"]
    too_big = g > t["ex_gap_max"]
    # a full year has a compared day on or before 7 January and on or after 24 December
    full = [y for y in range(int(gd[0][:4]), int(gd[-1][:4]) + 1)
            if any(d[:4] == str(y) and d[5:] <= "01-07" for d in gd)
            and any(d[:4] == str(y) and d[5:] >= "12-24" for d in gd)]
    per_year = {y: int(sum(1 for i, d in enumerate(gd) if ex[i] and int(d[:4]) == y)) for y in full}
    sums = {y: float(sum(g[i] for i, d in enumerate(gd) if ex[i] and int(d[:4]) == y)) for y in full}
    want = t["ex_days_per_year"]
    n_ok = sum(1 for y in full if per_year[y] == want)
    n_warn = sum(1 for y in full if abs(per_year[y] - want) == 1)
    n_fail = len(full) - n_ok - n_warn
    lo, hi = t["yield_band"]
    band_ok = all(lo <= sums[y] <= hi for y in full)
    allowed = max(t["ret_diff_floor_days"], int(t["ret_diff_share_max"] * len(g)))
    if not full:
        outcome = "WITHHELD"
    elif n_fail or int(too_big.sum()) or int(neg.sum()) > allowed or not band_ok:
        outcome = "FAIL"
    else:
        outcome = "WARN" if n_warn else "PASS"
    return Check("adjustment_convention", "hard", outcome,
                 {"n_full_years": len(full), "n_years_expected_ex_days": n_ok, "n_years_off_by_one": n_warn,
                  "n_years_off_more": n_fail, "n_negative_gap_days": int(neg.sum()), "n_allowed": allowed,
                  "n_too_large_gap_days": int(too_big.sum()), "yield_band_ok": band_ok},
                 {"ex_days": [gd[i] for i in np.flatnonzero(ex)], "per_year": per_year, "gap_sum_per_year": sums,
                  "negative": [[gd[i], float(g[i])] for i in np.flatnonzero(neg)]})


def check_btc_integrity(a: Series) -> Check:
    t = THRESHOLDS["btc"]
    missing = sorted(set(_calendar_days(a.dates[0], a.dates[-1])) - set(a.dates)) if a.dates else []
    lr = np.diff(np.log(a.values))
    jumps = [a.dates[i + 1] for i in np.flatnonzero(np.abs(lr) > t["jump_log_abs_max"])]
    if jumps or len(missing) > t["missing_days_warn_max"] or a.n_dropped_nonpositive:
        outcome = "FAIL"
    else:
        outcome = "WARN" if missing else "PASS"
    return Check("integrity_a", "hard", outcome,
                 {"n_rows": len(a.dates), "n_dropped_blank": a.n_dropped_blank,
                  "n_dropped_nonpositive": a.n_dropped_nonpositive, "n_missing_days_a": len(missing),
                  "missing_a": _cap(missing), "truncated": len(missing) > LIST_CAP, "no_implausible_jump": not jumps},
                 {"jump_dates": jumps, "missing": missing})


def _daily_log_returns(s: Series, days: list[str]) -> np.ndarray:
    m = dict(zip(s.dates, s.values))
    p = np.array([m.get(d, np.nan) for d in days], dtype=float)
    return np.diff(np.log(p))


def check_btc_day_boundary(a: Series, b: Series) -> Check:
    """Which shift of B's labels lines its daily returns up with A's: 0 means both label a UTC day the same way
    (the bridge reads a BTC date D as the day that closes at 00:00 UTC on D+1, tools/nautilus/runner.py:629-634).
    Built from day-by-day differences only: for each shift k, the days on which |r_A(t) - r_B(t+k)| exceeds
    ret_diff_big. k = 0 must have strictly the fewest. No correlation and no statistic of one series alone."""
    t = THRESHOLDS["btc"]
    ov = _overlap(a, b)
    if ov is None:
        return Check("day_boundary", "hard", "WITHHELD", {})
    days = _calendar_days(*ov)
    ra, rb = _daily_log_returns(a, days), _daily_log_returns(b, days)
    n_over, n_used = {}, {}
    for k in (-1, 0, 1):
        x, y = (ra[:len(ra) - k], rb[k:]) if k >= 0 else (ra[-k:], rb[:len(rb) + k])
        ok = np.isfinite(x) & np.isfinite(y)
        n_used[k] = int(ok.sum())
        n_over[k] = int(np.sum(np.abs(x[ok] - y[ok]) > t["ret_diff_big"]))
    if min(n_used.values()) < 3:
        return Check("day_boundary", "hard", "WITHHELD", {})
    best = min(n_over, key=lambda k: (n_over[k], k != 0))         # the fewest; a tie keeps 0
    strict = n_over[0] < min(n_over[-1], n_over[1])
    return Check("day_boundary", "hard", "PASS" if best == 0 and strict else "FAIL",
                 {"lag": int(best), "lag0_strictly_fewest": bool(strict)},
                 {"n_over_by_lag": n_over, "n_compared_by_lag": n_used})


def check_btc_levels(a: Series, b: Series) -> Check:
    t = THRESHOLDS["btc"]
    days, pa, pb = _common(a, b)
    if len(days) < 2:
        return Check("levels_and_returns", "hard", "WITHHELD", {})
    lv = np.abs(np.log(pa / pb))
    late = np.array([d >= t["late_from"] for d in days])
    out = {}
    fail = warn = False
    for name, mask in (("late", late), ("early", ~late)):
        if not mask.any():
            out[name] = {"n_days": 0}
            continue
        x = lv[mask]
        p50, p99, mx = float(np.percentile(x, 50)), float(np.percentile(x, 99)), float(np.max(x))
        if name == "late":
            ok = p50 <= t["level_p50_max"] and p99 <= t["level_p99_max"] and mx <= t["level_max"]
            fail |= not ok
        else:
            ok = p99 <= t["early_level_p99_max"] and mx <= t["early_level_max"]
            warn |= not ok
        out[name] = {"n_days": int(mask.sum()), "p50_bucket": bucket(p50), "p99_bucket": bucket(p99),
                     "max_bucket": bucket(mx), "within_band": bool(ok)}
    lr = np.diff(np.log(pa)) - np.diff(np.log(pb))
    n_big = int(np.sum(np.abs(lr) > t["ret_diff_big"]))
    allowed = int(t["ret_diff_share_max"] * len(lr))
    fail |= n_big > allowed
    outcome = "FAIL" if fail else ("WARN" if warn else "PASS")
    rank = np.argsort(-lv)[:LIST_CAP]
    return Check("levels_and_returns", "hard", outcome,
                 {**out, "n_big_return_diff_days": n_big, "n_allowed": allowed},
                 {"worst_level": [[days[i], float(lv[i])] for i in rank]})


def check_rf_units(a: Series) -> Check:
    """A alone: every published value inside range_pct and the window maximum at least unit_max_at_least_pct. Only
    NaN is a published blank: plus or minus infinity is a value outside the range, as it is for the runner, whose
    dropna keeps it."""
    t = THRESHOLDS["rf"]
    published = a.values[~np.isnan(a.values)]
    lo, hi = t["range_pct"]
    outside = [d for d, v in zip(a.dates, a.values) if not math.isnan(v) and not lo <= v <= hi]
    ok = bool(published.size) and not outside and float(np.max(published)) >= t["unit_max_at_least_pct"]
    return Check("units", "hard", "PASS" if ok else "FAIL", {"percent_units_ok": ok}, {"outside_range": outside})


def check_rf_seed(a: Series, start: str) -> Check:
    """A alone: a published value on or before the window start, inside the seed lookback (the runner's ffill)."""
    published = [d for d, v in zip(a.dates, a.values) if not math.isnan(v)]
    ok = bool(published) and published[0] <= start
    return Check("seed", "hard", "PASS" if ok else "FAIL", {"seed_before_start": ok})


def check_rf(a: Series, b: Series, role: str) -> list[Check]:
    """A is the pinned DGS3MO with its published blanks kept; B is another channel of the same series. A date on
    which A has a value and B has none, whether B lacks the row or carries a blank there, is listed."""
    t = THRESHOLDS["rf"]
    av = dict(zip(a.dates, a.values))
    bv = dict(zip(b.dates, b.values))
    both = [d for d in a.dates if d in bv and not math.isnan(av[d]) and not math.isnan(bv[d])]
    diff = [abs(av[d] - bv[d]) for d in both]
    off = [d for d, x in zip(both, diff) if not x < t["value_tol_pct"]]      # an infinite A value is off as well
    blank_a_value_b = [d for d in a.dates if math.isnan(av[d]) and d in bv and not math.isnan(bv[d])]
    weekday = [d for d in a.dates if date.fromisoformat(d).weekday() < 5]
    value_a_absent_b = [d for d in weekday if not math.isnan(av[d]) and math.isnan(bv.get(d, math.nan)) and
                        b.dates and b.dates[0] <= d <= b.dates[-1]]
    checks = [
        Check("values", "hard", "FAIL" if off else "PASS",
              {"n_common_values": len(both), "n_off_by_tol": len(off),
               "max_abs_bucket": bucket(max(diff) if diff else None)},
              {"off": [[d, av[d], bv[d]] for d in off]}),
        Check("blanks", "warn", "WARN" if (blank_a_value_b or value_a_absent_b) else "PASS",
              {"n_blank_a_value_b": len(blank_a_value_b), "blank_a_value_b": _cap(blank_a_value_b),
               "n_value_a_absent_b": len(value_a_absent_b), "value_a_absent_b": _cap(value_a_absent_b),
               "truncated": len(blank_a_value_b) > LIST_CAP or len(value_a_absent_b) > LIST_CAP}),
    ]
    return [_demote(c, role) for c in checks]


# --------------------------------------------------------------------------- #
# Compare
# --------------------------------------------------------------------------- #
PAIR_CHECKS = {
    "spy": {"total": (check_calendar, check_spy_same_convention),
            "split": (check_calendar, check_spy_cross_convention)},
    "btc": {"none": (check_calendar, check_btc_day_boundary, check_btc_levels)},
}


def compare(series: str, a: Series, pairs: list[tuple[str, str, str, Series, str]],
            unavailable: list[tuple[str, str]] = (), *, start: str | None = None,
            fetch_records: frozenset[str] = frozenset()) -> tuple[dict, dict, str]:
    """pairs: (role, convention, provider, series, file sha256); unavailable: (provider, reason) for each provider the
    owner could not fetch; start: the window start (the rf seed); fetch_records: the providers whose file came with
    its own fetch record. Returns (summary body, detail, outcome)."""
    if series == "spy":
        integrity = [check_spy_integrity(a)]
    elif series == "btc":
        integrity = [check_btc_integrity(a)]
    else:
        integrity = [check_rf_units(a), check_rf_seed(a, start or (a.dates[0] if a.dates else ""))]
    out_pairs, det_pairs = [], []
    for role, conv, provider, b, sha in pairs:
        cov = _demote(check_coverage(series, a, b), role)
        checks: list[Check] = [cov]
        if cov.outcome == "PASS":
            if series == "rf":
                checks += check_rf(a, b, role)
            elif conv not in PAIR_CHECKS[series]:
                raise Refused(f"{series}: convention {conv!r} is not compared")
            else:
                checks += [_demote(fn(series, a, b) if fn is check_calendar else fn(a, b), role)
                           for fn in PAIR_CHECKS[series][conv]]
        hard = [c for c in checks if c.kind == "hard"]
        if any(c.outcome == "FAIL" for c in hard):
            p_out = "FAIL"
        elif cov.outcome != "PASS" or any(c.outcome == "WITHHELD" for c in hard):
            p_out = "WITHHELD"
        else:
            p_out = "WARN" if any(c.outcome == "WARN" for c in checks) else "PASS"
        out_pairs.append({"provider": provider, "role": role, "convention": conv, "file_sha256": sha,
                          "has_fetch_record": provider in fetch_records, "outcome": p_out,
                          "checks": [c.public() for c in checks]})
        det_pairs.append({"provider": provider, "role": role, "checks": {c.id: c.detail for c in checks}})
    evidence = [p for p in out_pairs if p["role"] in ("independent", "cross")]
    withheld = [f"{provider} not compared: {reason}" for provider, reason in unavailable]
    if any(c.outcome == "FAIL" for c in integrity) or any(p["outcome"] == "FAIL" for p in evidence):
        outcome = "FAIL"
    elif not any(p["outcome"] in ("PASS", "WARN") for p in evidence):
        outcome = "WITHHELD"
        withheld.append(NO_EVIDENCE)
    else:
        outcome = "PASS"
    # A's dates that no fully evaluated independent or cross pair spans: checked by A's own integrity check only
    spans = [(bd[0], bd[-1]) for (role, _, _, b, _), p in zip(pairs, out_pairs)
             if role in ("independent", "cross") and p["outcome"] in ("PASS", "WARN")
             for bd in [_base_dates(series, b)] if bd]
    n_uncovered = sum(1 for d in _base_dates(series, a) if not any(lo <= d <= hi for lo, hi in spans))
    body = {"integrity": [c.public() for c in integrity], "pairs": out_pairs, "outcome": outcome,
            "n_a_outside_evidence_spans": n_uncovered, "withheld_reasons": withheld}
    detail = {"integrity": {c.id: c.detail for c in integrity}, "pairs": det_pairs}
    return body, detail, outcome


NO_EVIDENCE = "no independent or cross pair was evaluated in full"


def provider_map(series: str) -> dict:
    return {p: {"role": r, "convention": cv, "required": req} for p, (r, cv, req) in PROVIDERS[series].items()}


def tool_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def build_summary(series: str, body: dict, *, file: str, md5: str, start: str, end: str, now: datetime) -> dict:
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    return {"schema": SCHEMA, "tool": {"name": TOOL_NAME, "sha256": tool_sha256()},
            "run_id": f"PP-{stamp}-{series}", "created_utc": stamp, "series": series,
            "window": {"start": start, "end": end}, "pinned": {"file": file, "md5": md5, "md5_ok": True},
            "providers": provider_map(series), "thresholds": THRESHOLDS[series], **body}


# --------------------------------------------------------------------------- #
# Summary allow-list (10.5.2)
# --------------------------------------------------------------------------- #
class SummaryUnsafe(Refused):
    """The summary breaks 10.5.2; the message names the key only."""


TOP_KEYS = ("schema", "tool", "run_id", "created_utc", "series", "window", "pinned", "providers", "thresholds",
            "integrity", "pairs", "outcome", "n_a_outside_evidence_spans", "withheld_reasons")
_NESTED = {"tool", "window", "pinned", "integrity", "pairs", "checks", "late", "early"}
_DATE_LISTS = {"only_a", "only_b", "missing_a", "blank_a_value_b", "value_a_absent_b"}
_DATE_SCALARS = {"first_date", "last_date", "start", "end"}
_BOOLS = {"md5_ok", "has_fetch_record", "coverage_ok", "truncated", "no_split_shaped_jump", "max_ok", "drift_ok",
          "yield_band_ok", "lag0_strictly_fewest", "within_band", "percent_units_ok", "seed_before_start",
          "no_implausible_jump"}
_HEX = {"sha256": re.compile(r"[0-9a-f]{64}"), "file_sha256": re.compile(r"[0-9a-f]{64}"),
        "md5": re.compile(r"[0-9a-f]{32}")}
_BUCKET = re.compile(r"<=1e-0\d|>1e-01|n/a")
_STAMP = re.compile(r"\d{8}T\d{6}Z")


def assert_summary_safe(summary: dict) -> None:
    """10.5.2 as an allow-list: identifiers and hashes, the window, the thresholds and the provider map, integers under
    n_*, `lag` in {-1, 0, 1}, at most 100 calendar dates under the named date keys, decade buckets, booleans,
    outcomes and withheld_reasons. Any other key, type or value raises SummaryUnsafe before a file is written."""
    if not isinstance(summary, dict) or set(summary) != set(TOP_KEYS):
        raise SummaryUnsafe("the summary's top-level keys are not the 10.5.2 set")
    series = summary["series"]
    if series not in SERIES:
        raise SummaryUnsafe("series")
    if summary["thresholds"] != THRESHOLDS[series]:
        raise SummaryUnsafe("thresholds differ from 10.5.1")
    if summary["providers"] != provider_map(series):
        raise SummaryUnsafe("providers differ from 10.5.1")
    enums = {"schema": (SCHEMA,), "name": (TOOL_NAME,), "series": SERIES, "outcome": OUTCOMES, "kind": ("hard", "warn"),
             "id": tuple(COMPUTES), "role": ROLES, "convention": CONVENTIONS, "provider": tuple(PROVIDERS[series]),
             "file": (PINNED[series][3],)}
    reasons = {f"{p} not compared: {r}" for p in PROVIDERS[series] for r in UNAVAILABLE_REASONS} | {NO_EVIDENCE}

    def date_ok(v) -> bool:
        return isinstance(v, str) and bool(_DATE.fullmatch(v)) and _valid_iso(v) and v < CUTOFF

    def walk(key: str, v) -> None:
        if key in ("thresholds", "providers") and v is summary.get(key):
            return
        if key in _NESTED:
            items = v if isinstance(v, list) else [v]
            for item in items:
                if not isinstance(item, dict):
                    raise SummaryUnsafe(key)
                for k, x in item.items():
                    walk(k, x)
            return
        if key in _DATE_LISTS:
            if not (isinstance(v, list) and len(v) <= LIST_CAP and all(date_ok(x) for x in v)):
                raise SummaryUnsafe(key)
        elif key in _DATE_SCALARS:
            if not (v is None or date_ok(v)):
                raise SummaryUnsafe(key)
        elif key.startswith("n_"):
            if not (isinstance(v, int) and not isinstance(v, bool) and v >= 0):
                raise SummaryUnsafe(key)
        elif key == "lag":
            if not (isinstance(v, int) and not isinstance(v, bool) and v in (-1, 0, 1)):
                raise SummaryUnsafe(key)
        elif key.endswith("_bucket"):
            if not (isinstance(v, str) and _BUCKET.fullmatch(v)):
                raise SummaryUnsafe(key)
        elif key in _BOOLS:
            if not isinstance(v, bool):
                raise SummaryUnsafe(key)
        elif key in enums:
            if not (isinstance(v, str) and v in enums[key]):
                raise SummaryUnsafe(key)
        elif key in _HEX:
            if not (isinstance(v, str) and _HEX[key].fullmatch(v)):
                raise SummaryUnsafe(key)
        elif key == "created_utc":
            if not (isinstance(v, str) and _STAMP.fullmatch(v)):
                raise SummaryUnsafe(key)
        elif key == "run_id":
            if v != f"PP-{summary.get('created_utc')}-{series}":
                raise SummaryUnsafe(key)
        elif key == "withheld_reasons":
            if not (isinstance(v, list) and all(isinstance(x, str) and x in reasons for x in v)):
                raise SummaryUnsafe(key)
        else:
            raise SummaryUnsafe(f"key {key!r} is not in the 10.5.2 allow-list")

    for k in TOP_KEYS:
        walk(k, summary[k])


# --------------------------------------------------------------------------- #
# compare (command)
# --------------------------------------------------------------------------- #
def _accounted_pairs(series: str, pair_args: list[list[str]], unavailable_args: list[list[str]]):
    """The command line names providers only; their role and convention come from PROVIDERS. Every required provider
    is compared or declared unavailable with a reason from UNAVAILABLE_REASONS (10.5, Providers)."""
    table = PROVIDERS[series]
    named = [p for p, _ in pair_args] + [p for p, _ in unavailable_args]
    for p in named:
        if p not in table:
            raise Refused(f"{series}: provider {p!r} is not one of {tuple(table)}")
    if len(named) != len(set(named)):
        raise Refused(f"{series}: a provider is named twice")
    for _, reason in unavailable_args:
        if reason not in UNAVAILABLE_REASONS:
            raise Refused(f"{series}: reason {reason!r} is not one of {UNAVAILABLE_REASONS}")
    missing = [p for p, (_, _, required) in table.items() if required and p not in named]
    if missing:
        raise Refused(f"{series}: required provider(s) {', '.join(missing)} neither compared (--pair <provider> "
                      f"<file>) nor declared unavailable (--unavailable <provider> <reason>)")
    return [(table[p][0], table[p][1], p, Path(path)) for p, path in pair_args], \
        [(p, reason) for p, reason in unavailable_args]


def _json_default(x):
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    raise TypeError(type(x).__name__)


def run_compare(args, *, now: datetime, say) -> int:
    check_new_out(args.out)
    pair_specs, unavailable = _accounted_pairs(args.series, args.pair, args.unavailable)
    tab = read_table(args.table, args.repo, args.series)
    rf = args.series == "rf"
    first = tab["start"]
    if rf:
        first = (date.fromisoformat(tab["start"]) - timedelta(days=THRESHOLDS["rf"]["seed_lookback_days"])).isoformat()
    a = read_pinned(tab["path"], md5=tab["md5"], start=first, end=tab["end"], owner_run=args.owner_run,
                    keep_blanks=rf)
    pairs, with_record = [], set()
    for role, conv, provider, path in pair_specs:
        b, sha, has_record = read_provider(path, provider=provider, series=args.series, start=first, end=tab["end"],
                                           owner_run=args.owner_run, window=(tab["start"], tab["end"]),
                                           keep_blanks=rf)
        pairs.append((role, conv, provider, b, sha))
        if has_record:
            with_record.add(provider)
    body, detail, outcome = compare(args.series, a, pairs, unavailable, start=tab["start"],
                                    fetch_records=frozenset(with_record))
    summary = build_summary(args.series, body, file=tab["file"], md5=tab["md5"], start=tab["start"], end=tab["end"],
                            now=now)
    assert_summary_safe(summary)
    # both files are serialised before the folder exists, so a failure up to here leaves nothing behind
    s_text = json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=True, default=_json_default) + "\n"
    d_text = json.dumps({"schema": DETAIL_SCHEMA, "run_id": summary["run_id"], **detail}, indent=1,
                        sort_keys=True, default=_json_default) + "\n"
    # detail.json first and summary.json last: whatever a failed write leaves, it is never a summary without its detail
    _write_new_folder(args.out, {"detail.json": d_text, "summary.json": s_text})
    code = EXIT[outcome]
    say(f"PARITY {args.series} {outcome} exit={code} summary={args.out / 'summary.json'}")
    return code


# --------------------------------------------------------------------------- #
# selftest: COMPUTES against the checks compare() emits, and no other statistic
# --------------------------------------------------------------------------- #
FORBIDDEN_STATISTICS = frozenset({"corrcoef", "corr", "cov", "std", "nanstd", "var", "nanvar", "mean", "nanmean",
                                  "average", "sharpe", "sharpe_ratio", "drawdown", "max_drawdown", "volatility"})


def forbidden_statistics(source: str) -> list[str]:
    """Calls in `source` whose name is a correlation, mean, volatility, Sharpe or drawdown statistic."""
    hits = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
            if name.lower() in FORBIDDEN_STATISTICS:
                hits.append(f"{name}@{node.lineno}")
    return hits


def _synthetic(series: str) -> tuple[Series, list[tuple[str, str, str, Series, str]], str]:
    """Small synthetic stand-ins (no file, no real price): A and one pair per convention of `series`."""
    rng = np.random.default_rng({"spy": 7, "btc": 11, "rf": 5}[series])
    if series == "spy":
        d0 = date(2010, 1, 1)
        days = [(d0 + timedelta(k)).isoformat() for k in range(3 * 366) if (d0 + timedelta(k)).weekday() < 5]
        days = [d for d in days if d <= "2012-12-31"]
        raw, div, p = np.empty(len(days)), np.zeros(len(days)), 100.0
        ex = {next(d for d in days if d >= f"{y}-{m:02d}-15") for y in (2010, 2011, 2012) for m in (3, 6, 9, 12)}
        for i, d in enumerate(days):
            if i:
                p *= 1.0 + rng.normal(0.0003, 0.011)
                if d in ex:
                    div[i] = round(0.0045 * raw[i - 1], 2)
                    p -= div[i]
            raw[i] = round(p, 2)
        factor, f = np.ones(len(days)), 1.0
        for i in range(len(days) - 1, -1, -1):
            factor[i] = f
            if div[i] > 0:
                f *= 1.0 - div[i] / raw[i - 1]
        adj = raw * factor
        a = Series(tuple(days), adj)
        return a, [("independent", "total", "fmp", Series(tuple(days), adj * 0.987), "0" * 64),
                   ("cross", "split", "kis", Series(tuple(days), raw), "1" * 64)], days[0]
    if series == "btc":
        d0 = date(2016, 1, 1)
        days = [(d0 + timedelta(k)).isoformat() for k in range(3 * 365)]
        p = 400.0 * np.exp(np.cumsum(rng.normal(0.001, 0.04, len(days))))
        venue = p * np.exp(rng.normal(0.0, 0.001, len(days)))
        return Series(tuple(days), p), [("independent", "none", "coinbase", Series(tuple(days), venue), "2" * 64)], \
            days[0]
    d0 = date(2010, 1, 1)
    days = [(d0 + timedelta(k)).isoformat() for k in range(730) if (d0 + timedelta(k)).weekday() < 5]
    vals = np.round(np.clip(np.cumsum(rng.normal(0.0, 0.03, len(days))) + 1.2, 0.0, 6.0), 2)
    a_vals = vals.copy()
    a_vals[10] = np.nan                                       # one published blank
    pairs = [("independent", "rate_pct", "treasury", Series(tuple(days), vals), "3" * 64)]
    return Series(tuple(days), a_vals), pairs, days[40]


def selftest() -> list[str]:
    """Returns the failures (empty when every check holds). Reads only this file; writes nothing."""
    failures: list[str] = []
    seen: set[str] = set()
    now = datetime(2026, 11, 5, tzinfo=timezone.utc)
    for series in SERIES:
        a, pairs, start = _synthetic(series)
        body, _, outcome = compare(series, a, pairs, [(p, "fetch_failed") for p, (_, _, req) in
                                                      PROVIDERS[series].items() if req and p not in
                                                      {x[2] for x in pairs}], start=start)
        if outcome != "PASS":
            failures.append(f"synthetic {series} is {outcome}, not PASS")
        summary = build_summary(series, body, file=PINNED[series][3], md5="0" * 32, start=start, end=a.dates[-1],
                                now=now)
        try:
            assert_summary_safe(summary)
        except SummaryUnsafe as exc:
            failures.append(f"synthetic {series} summary refused: {exc}")
        seen |= {c["id"] for c in body["integrity"]} | {c["id"] for p in body["pairs"] for c in p["checks"]}
    if seen != set(COMPUTES):
        failures.append(f"checks emitted {sorted(seen)} differ from COMPUTES {sorted(COMPUTES)}")
    hits = forbidden_statistics(Path(__file__).read_text(encoding="utf-8"))
    if hits:
        failures.append(f"statistics outside the 3.9 exception: {hits}")
    if not forbidden_statistics("import numpy as np\nnp.corrcoef(x, y)\ns.std()\n"):
        failures.append("the statistic scan misses a planted call")
    for series, table in PROVIDERS.items():
        if not any(r in ("independent", "cross") and req for r, _, req in table.values()):
            failures.append(f"{series}: no required independent or cross provider")
        if set(table) - set(FETCHERS):
            failures.append(f"{series}: a provider without a fetcher")
    bad = build_summary("spy", {"integrity": [], "pairs": [], "outcome": "PASS", "n_a_outside_evidence_spans": 0,
                                "withheld_reasons": []}, file="yf_SPY.csv", md5="0" * 32, start="2010-01-04",
                        end="2010-12-31", now=now)
    for name, mutate in (("float", lambda s: s["integrity"].append({"id": "coverage", "max_abs": 0.0012})),
                         ("price key", lambda s: s.update(price=4321)),
                         ("date key", lambda s: s["integrity"].append({"id": "coverage", "worst_day": "2015-07-01"})),
                         ("lag", lambda s: s["integrity"].append({"id": "day_boundary", "lag": 2}))):
        s = json.loads(json.dumps(bad))
        mutate(s)
        try:
            assert_summary_safe(s)
            failures.append(f"the allow-list accepts a {name}")
        except SummaryUnsafe:
            pass
    return failures


# --------------------------------------------------------------------------- #
# Command line
# --------------------------------------------------------------------------- #
def _where(exc: BaseException) -> str:
    """The tool's own line numbers on the way to an unexpected exception, outermost first. Numbers only: the
    exception's text can quote a value or a URL with a key, so it is never printed."""
    here = os.path.normcase(os.path.abspath(__file__))
    lines, tb = [], exc.__traceback__
    while tb is not None:
        if os.path.normcase(os.path.abspath(tb.tb_frame.f_code.co_filename)) == here:
            lines.append(str(tb.tb_lineno))
        tb = tb.tb_next
    return f" at {TOOL_NAME} lines {' > '.join(lines)}" if lines else ""


def _say_error(say, exc: BaseException) -> None:
    left = getattr(exc, "left_behind", None)
    if left is not None:
        say(f"LEFT BEHIND: {left} could not be removed; it is not a result, delete it by hand")
    say(f"ERROR: {type(exc).__name__}{_where(exc)}")


class _Say:
    """print() with every loaded key value replaced, as a last guard; the tool never formats a key into a line. A
    character the console encoding lacks (cp949, or any other) is written as a backslash escape, so a line never
    fails to print and the last line is the same text on every console."""

    def __init__(self):
        self.secrets: list[str] = []

    def __call__(self, line: str) -> None:
        text = _redact(line, self.secrets)
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        try:
            text = text.encode(encoding, errors="backslashreplace").decode(encoding)
        except LookupError:
            text = text.encode("ascii", errors="backslashreplace").decode("ascii")
        print(text)


def _parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -B -m tools.provider_parity.parity_check",
                                 description="Provider parity of the pilot series (spec 10.5).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="fetch one provider's copy of one series")
    f.add_argument("--series", choices=SERIES, required=True)
    f.add_argument("--provider", required=True)
    f.add_argument("--start", required=True, help="the table's start (the fetch begins 31 days earlier)")
    f.add_argument("--end", required=True, help="the table's end (the fetch ends 7 days later)")
    f.add_argument("--out", type=Path, required=True, help="a new folder outside every git work tree")
    f.add_argument("--env-file", type=Path, help="read FMP_API_KEY, KIS_APP_KEY, KIS_APP_SECRET, KIS_BASE_URL by name")
    c = sub.add_parser("compare", help="compare the pinned file of a pilot table with provider files")
    c.add_argument("--series", choices=SERIES, required=True)
    c.add_argument("--table", type=Path, required=True, help="the pilot table, inside --repo")
    c.add_argument("--repo", type=Path, required=True, help="the research clone's root (read only)")
    c.add_argument("--pair", nargs=2, action="append", default=[], metavar=("PROVIDER", "FILE"))
    c.add_argument("--unavailable", nargs=2, action="append", default=[], metavar=("PROVIDER", "REASON"))
    c.add_argument("--out", type=Path, required=True, help="a new folder outside every git work tree")
    c.add_argument("--owner-run", action="store_true", help="only on the owner's machine: read the pinned cache file")
    sub.add_parser("selftest", help="COMPUTES against the checks, and the summary allow-list")
    return ap


def run(argv: list[str] | None = None, *, now: datetime | None = None, http: HttpGet | None = None,
        yf_download: Callable | None = None, kis_get: Callable | None = None) -> int:
    """The command line. `http`, `yf_download` and `kis_get` replace the network layers (tests)."""
    args = _parser().parse_args(argv)
    now = now or datetime.now(timezone.utc)
    say = _Say()
    if args.cmd == "selftest":
        failures = selftest()
        for line in failures:
            say(f"FAIL {line}")
        say(f"SELFTEST {'FAIL' if failures else 'PASS'} checks={len(COMPUTES)} failures={len(failures)}")
        return 1 if failures else 0
    if args.cmd == "fetch":
        tag = f"FETCH {args.series} {args.provider}"
        try:
            return run_fetch(args, http=http or urllib_get, yf_download=yf_download, kis_get=kis_get, now=now,
                             say=say)
        except Refused as exc:
            say(f"REFUSED: {exc}")
            say(f"{tag} REFUSED exit={EXIT_REFUSED} csv=-")
            return EXIT_REFUSED
        except FetchFailed as exc:
            say(f"UNAVAILABLE: {exc}")
            say(f"{tag} UNAVAILABLE {exc.reason} exit={EXIT_ERROR} csv=-")
            return EXIT_ERROR
        except Exception as exc:              # the text can quote a value or a URL with a key, so only the type
            _say_error(say, exc)
            say(f"{tag} ERROR exit={EXIT_ERROR} csv=-")
            return EXIT_ERROR
    try:
        return run_compare(args, now=now, say=say)
    except Refused as exc:
        say(f"REFUSED: {exc}")
        say(f"PARITY {args.series} REFUSED exit={EXIT_REFUSED} summary=-")
        return EXIT_REFUSED
    except Exception as exc:                  # never FAIL by accident; the text can quote a value, so only the type
        _say_error(say, exc)
        say(f"PARITY {args.series} ERROR exit={EXIT_ERROR} summary=-")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(run())
